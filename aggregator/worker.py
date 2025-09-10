import os, json, asyncio, random
import aio_pika

AMQP_URL = os.getenv("AMQP_URL", "amqp://user:pass@rabbitmq:5672")

PROVIDERS = ["Planet", "Copernicus", "UP42", "Esteban"]

async def publish_event(ch: aio_pika.Channel, task_id: str, evt: dict, rk: str):
    ex = await ch.get_exchange("events")
    body = json.dumps(evt).encode()
    await ex.publish(aio_pika.Message(body=body), routing_key=rk)

async def process_task(ch: aio_pika.Channel, msg: aio_pika.IncomingMessage):
    payload = json.loads(msg.body)
    task_id = payload["taskId"]
    await publish_event(ch, task_id, {"type": "task.startedhola", "taskId": task_id}, f"task.{task_id}.started")

    async def call_provider(name: str):
        # simulate latency + outcome
        await asyncio.sleep(random.uniform(0.5, 2.0))
        status = "succeeded" if random.random() < 0.85 else "failed"
        evt = {"type": "provider.update", "taskId": task_id, "provider": name, "status": status}
        if status == "succeeded":
            evt["items"] = random.randint(1, 10)
        else:
            evt["error"] = "timeout"
        await publish_event(ch, task_id, evt, f"task.{task_id}.provider.{name}.{status}")

    await asyncio.gather(*[call_provider(p) for p in PROVIDERS])
    await publish_event(ch, task_id, {"type": "task.complete", "taskId": task_id}, f"task.{task_id}.complete")

    await msg.ack()

async def main():
    conn = await aio_pika.connect_robust(AMQP_URL)
    ch = await conn.channel()
    await ch.set_qos(prefetch_count=5)

    ex_tasks = await ch.declare_exchange("tasks", aio_pika.ExchangeType.DIRECT, durable=True)
    ex_events = await ch.declare_exchange("events", aio_pika.ExchangeType.TOPIC, durable=True)

    q = await ch.declare_queue("tasks.search", durable=True)
    await q.bind(ex_tasks, routing_key="search")

    async with q.iterator() as queue_iter:
        async for msg in queue_iter:
            try:
                await process_task(ch, msg)
            except Exception as e:
                print("error processing", e)
                await msg.nack(requeue=False)

if __name__ == "__main__":
    asyncio.run(main())
