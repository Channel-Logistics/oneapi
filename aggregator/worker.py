import os, json, asyncio
import aio_pika
import logging
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import List
from logging_config import setup_logging
from dotenv import load_dotenv

from providers.copernicus import CopernicusProvider
from providers.planetary_computer import PlanetaryComputerProvider
from providers.umbra_canopy import UmbraProvider

# --- Unified Pydantic model ---
class JobRequest(BaseModel):
    start_date: str
    end_date: str
    bbox: List[float]

# --- Setup ---
load_dotenv()
setup_logging()
logger = logging.getLogger("Aggregator")

AMQP_URL = os.getenv("AMQP_URL", "amqp://user:pass@rabbitmq:5672")

CONFIG = {"UMBRA_TOKEN": os.getenv("UMBRA_TOKEN")}

PROVIDERS = [
    CopernicusProvider(),
    PlanetaryComputerProvider(),
    UmbraProvider(token=CONFIG["UMBRA_TOKEN"]),
]

# --- Helper to publish back into "events" exchange ---
async def publish_event(ch: aio_pika.Channel, task_id: str, evt: dict, rk: str):
    ex = await ch.get_exchange("events")
    body = json.dumps(evt).encode()
    await ex.publish(aio_pika.Message(body=body), routing_key=rk)

# --- Per-provider task runner ---
async def call_provider(ch: aio_pika.Channel, task_id: str, provider, job_type, request):
    # Small artificial delay for testing SSE updates
    await asyncio.sleep(3)

    try:
        if job_type == "search":
            # Decide mode
            start_dt = datetime.fromisoformat(request.start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(request.end_date.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            modes = []
            if end_dt < now: modes.append("archive")
            if start_dt > now: modes.append("feasibility")
            if start_dt <= now <= end_dt: modes.append("mixed")

            # Run provider per mode
            for mode in modes:
                if mode in ["archive", "mixed"]:
                    res = await provider.search_archive(request.start_date, request.end_date, request.bbox)
                    key = "features"
                if mode in ["feasibility", "mixed"]:
                    lon = (request.bbox[0] + request.bbox[2]) / 2
                    lat = (request.bbox[1] + request.bbox[3]) / 2
                    geometry = {"type": "Point", "coordinates": [lon, lat]}
                    res = await provider.search_feasibility(request.start_date, request.end_date, geometry)
                    key = "opportunities"

                evt = {
                    "type": "provider.update",
                    "taskId": task_id,
                    "provider": provider.name,
                    "mode": mode,
                    "status": "ok" if res else "empty",
                }
                if res: evt[key] = res
                await publish_event(ch, task_id, evt, f"task.{task_id}.provider.{provider.name}.{evt['status']}")

        elif job_type == "task":
            if provider.name == "Umbra" and hasattr(provider, "create_task"):
                lon = (request.bbox[0] + request.bbox[2]) / 2
                lat = (request.bbox[1] + request.bbox[3]) / 2
                geometry = {"type": "Point", "coordinates": [lon, lat]}
                res = await provider.create_task(request.start_date, request.end_date, geometry)
                evt = {
                    "type": "provider.update",
                    "taskId": task_id,
                    "provider": provider.name,
                    "mode": "tasking",
                    "status": "ok",
                    "task": res,
                }
                await publish_event(ch, task_id, evt, f"task.{task_id}.provider.{provider.name}.{evt['status']}")

    except Exception as e:
        evt = {
            "type": "provider.update",
            "taskId": task_id,
            "provider": provider.name,
            "status": "error",
            "error": str(e)
        }
        await publish_event(ch, task_id, evt, f"task.{task_id}.provider.{provider.name}.error")

# --- Main task processor ---
async def process_task(ch: aio_pika.Channel, msg: aio_pika.IncomingMessage):
    payload = json.loads(msg.body)
    task_id = payload["taskId"]
    job_type = payload.get("type", "search")

    logger.info(f"📥 Processing {job_type} task {task_id}")
    if job_type not in ("search", "task"):
        logger.warning(f"⚠️ Unknown job type {job_type} for task {task_id}")
        # Delay to show the user a failed job
        await asyncio.sleep(3)
        
        await publish_event(
            ch,
            task_id,
            {"type": "task.failed", "taskId": task_id, "error": f"Unknown job type: {job_type}"},
            f"task.{task_id}.failed",
        )
        await msg.ack()
        return
    # Delay so the client can see the task started event
    await asyncio.sleep(3)

    await publish_event(ch, task_id, {"type": "task.started", "taskId": task_id}, f"task.{task_id}.started")

    try:
        request = JobRequest(**payload)

        # Run all providers concurrently, each publishing its own updates
        await asyncio.gather(*[call_provider(ch, task_id, p, job_type, request) for p in PROVIDERS])

        await publish_event(ch, task_id, {"type": "task.complete", "taskId": task_id}, f"task.{task_id}.complete")

    except Exception as e:
        logger.error(f"💥 Task {task_id} failed: {e}")
        await publish_event(ch, task_id, {"type": "task.failed", "taskId": task_id, "error": str(e)}, f"task.{task_id}.failed")

    await msg.ack()

# --- Main loop ---
async def main():
    conn = await aio_pika.connect_robust(AMQP_URL)
    ch = await conn.channel()
    await ch.set_qos(prefetch_count=5)

    await ch.declare_exchange("tasks", aio_pika.ExchangeType.DIRECT, durable=True)
    await ch.declare_exchange("events", aio_pika.ExchangeType.TOPIC, durable=True)

    q = await ch.declare_queue("tasks.search", durable=True)
    await q.bind("tasks", routing_key="search")

    logger.info("🚀 Worker started, waiting for jobs...")

    async with q.iterator() as queue_iter:
        async for msg in queue_iter:
            try:
                await process_task(ch, msg)
            except Exception as e:
                logger.error(f"Error processing: {e}")
                await msg.nack(requeue=False)

if __name__ == "__main__":
    asyncio.run(main())