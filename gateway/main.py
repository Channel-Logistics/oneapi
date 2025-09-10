import asyncio, json, uuid, os
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import aio_pika
from sse_starlette.sse import EventSourceResponse

AMQP_URL = os.getenv("AMQP_URL", "amqp://user:pass@rabbitmq:5672")

app = FastAPI(title="Gateway SSE + RabbitMQ")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Keep one shared connection/channel
amqp_conn: aio_pika.RobustConnection
amqp_channel: aio_pika.Channel

@app.on_event("startup")
async def startup():
    global amqp_conn, amqp_channel
    amqp_conn = await aio_pika.connect_robust(AMQP_URL)
    amqp_channel = await amqp_conn.channel()
    # declare exchanges (idempotent)
    await amqp_channel.declare_exchange("tasks", aio_pika.ExchangeType.DIRECT, durable=True)
    await amqp_channel.declare_exchange("events", aio_pika.ExchangeType.TOPIC, durable=True)

@app.on_event("shutdown")
async def shutdown():
    if amqp_conn:
        await amqp_conn.close()

async def publish_task(task_id: str, payload: dict):
    ex = await amqp_channel.get_exchange("tasks")
    body = json.dumps({"taskId": task_id, **payload}).encode()
    await ex.publish(aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                     routing_key="search")

@app.post("/tasks")
async def create_task(body: dict, bg: BackgroundTasks):
    task_id = str(uuid.uuid4())
    bg.add_task(publish_task, task_id, body)
    return {"taskId": task_id, "sseUrl": f"/tasks/{task_id}/events"}

@app.get("/tasks/{task_id}/events")
async def sse(task_id: str):
    ex = await amqp_channel.get_exchange("events")
    
    # exclusive, auto-delete queue for this SSE connection
    queue = await amqp_channel.declare_queue(
        name=f"sse-{task_id}-{uuid.uuid4().hex}",
        exclusive=True, auto_delete=True, durable=False
    )

    await queue.bind(ex, routing_key=f"task.{task_id}.#")

    # in-process mailbox from RMQ -> SSE
    inbox: asyncio.Queue[dict] = asyncio.Queue()
    stop = asyncio.Event()

    async def pump_from_rmq():
        try:
            async with queue.iterator() as qit:
                async for rmq in qit:
                    async with rmq.process():
                        try:
                            evt = json.loads(rmq.body)
                        except Exception:
                            evt = {"type": "update", "raw": rmq.body.decode("utf-8", "ignore")}
                        await inbox.put(evt)
                        # after completion, enqueue sentinel then stop the pump
                        if evt.get("type") == "task.complete":
                            await inbox.put({"type": "__end__"})
                            break
        finally:
            stop.set()

    pump_task = asyncio.create_task(pump_from_rmq())

    async def event_gen():
        try:
            while True:
                evt = await inbox.get()
                if evt.get("type") == "__end__":
                    # we stop yielding; client should close the EventSource
                    break
                # Map evt to SSE {event, data}
                yield {
                    "event": evt.get("type", "provider.update"),
                    "data": evt,
                }
        finally:
            try:
                await queue.unbind(ex, routing_key=f"task.{task_id}.#")
            except Exception:
                pass
            try:
                await queue.delete(if_unused=False, if_empty=False)
            except Exception:
                pass
            pump_task.cancel()

    # EventSourceResponse sends heartbeats automatically (default ping=15s)
    resp = EventSourceResponse(event_gen(), ping=15)
    # Helpful headers for proxies
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["Connection"] = "keep-alive"
    resp.headers["X-Accel-Buffering"] = "no"
    return resp
@app.get("/health")
def health():
    return {"ok": True}

