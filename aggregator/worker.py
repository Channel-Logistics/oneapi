import asyncio
import json
import logging
from datetime import datetime, timezone
from functools import lru_cache
from typing import List

import aio_pika
from dotenv import load_dotenv
from logging_config import setup_logging
from providers.copernicus import CopernicusProvider
from providers.planetary_computer import PlanetaryComputerProvider
from providers.umbra_canopy import UmbraProvider
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


# --- Unified Pydantic model ---
class JobRequest(BaseModel):
    start_date: str
    end_date: str
    bbox: List[float]


# --- Environment Settings ---
class Settings(BaseSettings):
    AMQP_URL: str = Field(..., description="AMQP connection string")


@lru_cache
def get_settings() -> Settings:
    return Settings()


# --- Setup ---
load_dotenv()
setup_logging()
logger = logging.getLogger("Aggregator")

PROVIDERS = [
    CopernicusProvider(),
    PlanetaryComputerProvider(),
    UmbraProvider(),
]


# --- Helper to publish back into "events" exchange ---
async def publish_event(ch: aio_pika.Channel, order_id: str, evt: dict, rk: str):
    """Publish event to the events exchange and always inject orderId."""
    evt.setdefault("orderId", order_id)

    ex = await ch.get_exchange("events")
    body = json.dumps(evt).encode()
    await ex.publish(aio_pika.Message(body=body), routing_key=rk)


# --- Per-provider order runner ---
async def call_provider(
    ch: aio_pika.Channel, order_id: str, provider, job_type: str, request: JobRequest
):
    # Small artificial delay for testing SSE updates
    await asyncio.sleep(3)

    try:
        if job_type == "search":
            # Decide mode
            start_dt = datetime.fromisoformat(request.start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(request.end_date.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)

            modes = []
            if end_dt < now:
                modes.append("archive")
            if start_dt > now:
                modes.append("feasibility")
            if start_dt <= now <= end_dt:
                modes.append("mixed")

            # Run provider per mode
            for mode in modes:
                if mode in ["archive", "mixed"]:
                    res = await provider.search_archive(
                        request.start_date, request.end_date, request.bbox
                    )
                    key = "features"

                if mode in ["feasibility", "mixed"]:
                    lon = (request.bbox[0] + request.bbox[2]) / 2
                    lat = (request.bbox[1] + request.bbox[3]) / 2
                    geometry = {"type": "Point", "coordinates": [lon, lat]}
                    res = await provider.search_feasibility(
                        request.start_date, request.end_date, geometry
                    )
                    key = "opportunities"

                evt = {
                    "type": "provider.update",
                    "provider": provider.name,
                    "mode": mode,
                    "status": "ok" if res else "empty",
                }
                if res:
                    evt[key] = res

                await publish_event(
                    ch,
                    order_id,
                    evt,
                    f"order.{order_id}.provider.{provider.name}.{evt['status']}",
                )

        # TODO: Check process when a tasking order is going to be created
        elif job_type == "task":
            if provider.name == "Umbra" and hasattr(provider, "create_order"):
                lon = (request.bbox[0] + request.bbox[2]) / 2
                lat = (request.bbox[1] + request.bbox[3]) / 2
                geometry = {"type": "Point", "coordinates": [lon, lat]}
                res = await provider.create_task(
                    request.start_date, request.end_date, geometry
                )
                evt = {
                    "type": "provider.update",
                    "provider": provider.name,
                    "mode": "task",
                    "status": "ok",
                    "order": res,
                }
                await publish_event(
                    ch,
                    order_id,
                    evt,
                    f"order.{order_id}.provider.{provider.name}.{evt['status']}",
                )

    except Exception as e:
        evt = {
            "type": "provider.update",
            "provider": provider.name,
            "status": "error",
            "error": str(e),
        }
        await publish_event(
            ch, order_id, evt, f"order.{order_id}.provider.{provider.name}.error"
        )


# --- Main order processor ---
async def process_order(ch: aio_pika.Channel, msg: aio_pika.IncomingMessage):
    payload = json.loads(msg.body)
    order_id = payload["orderId"]
    job_type = payload.get("type", "search")

    logger.info(f"📥 Processing {job_type} order {order_id}")

    if job_type not in ("search", "task"):
        logger.warning(f"⚠️ Unknown job type {job_type} for order {order_id}")

        # Delay to show the user a failed job
        await asyncio.sleep(3)

        await publish_event(
            ch,
            order_id,
            {"type": "order.failed", "error": f"Unknown job type: {job_type}"},
            f"order.{order_id}.failed",
        )
        await msg.ack()
        return

    # Delay so the client can see the order started event
    await asyncio.sleep(3)

    await publish_event(
        ch,
        order_id,
        {"type": "order.started"},
        f"order.{order_id}.started",
    )

    try:
        request = JobRequest(**payload)

        # Run all providers concurrently
        await asyncio.gather(
            *[call_provider(ch, order_id, p, job_type, request) for p in PROVIDERS]
        )

        await publish_event(
            ch,
            order_id,
            {"type": "order.complete"},
            f"order.{order_id}.complete",
        )

    except Exception as e:
        logger.error(f"💥 Order {order_id} failed: {e}")
        await publish_event(
            ch,
            order_id,
            {"type": "order.failed", "error": str(e)},
            f"order.{order_id}.failed",
        )

    await msg.ack()


# --- Main loop ---
async def main():
    settings = get_settings()
    conn = await aio_pika.connect_robust(settings.AMQP_URL)
    ch = await conn.channel()
    await ch.set_qos(prefetch_count=5)

    await ch.declare_exchange("orders", aio_pika.ExchangeType.DIRECT, durable=True)
    await ch.declare_exchange("events", aio_pika.ExchangeType.TOPIC, durable=True)

    q = await ch.declare_queue("orders.search", durable=True)
    await q.bind("orders", routing_key="search")

    logger.info("🚀 Worker started, waiting for jobs...")

    async with q.iterator() as queue_iter:
        async for msg in queue_iter:
            try:
                await process_order(ch, msg)
            except Exception as e:
                logger.error(f"Error processing: {e}")
                await msg.nack(requeue=False)


if __name__ == "__main__":
    asyncio.run(main())
