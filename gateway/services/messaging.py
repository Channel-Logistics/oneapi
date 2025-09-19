import asyncio
import json
import uuid
from typing import AsyncIterator, Optional

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractRobustConnection


class Messaging:
    def __init__(self, amqp_url: str):
        self.amqp_url = amqp_url
        self._conn: Optional[AbstractRobustConnection] = None
        self._channel: Optional[AbstractChannel] = None

    async def start(self):
        conn = await aio_pika.connect_robust(self.amqp_url)
        self._conn = conn
        channel = await conn.channel()
        self._channel = channel
        if channel is None:
            raise RuntimeError("Messaging.start: channel not initialized")
        await channel.declare_exchange(
            "tasks", aio_pika.ExchangeType.DIRECT, durable=True
        )
        await channel.declare_exchange(
            "events", aio_pika.ExchangeType.TOPIC, durable=True
        )

    async def stop(self):
        if self._conn:
            await self._conn.close()

    async def publish_order(self, order_id: str, payload: dict):
        channel = self._channel
        if channel is None:
            raise RuntimeError("Messaging not started: channel is None")
        ex = await channel.get_exchange("tasks")
        body = json.dumps({"orderId": order_id, **payload}).encode()
        await ex.publish(
            aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
            routing_key="search",
        )

    async def sse_events(self, order_id: str) -> AsyncIterator[dict]:
        channel = self._channel
        if channel is None:
            raise RuntimeError("Messaging not started: channel is None")
        events = await channel.get_exchange("events")
        queue = await channel.declare_queue(
            name=f"sse-{order_id}-{uuid.uuid4().hex}",
            exclusive=True,
            auto_delete=True,
            durable=False,
        )
        await queue.bind(events, routing_key=f"order.{order_id}.#")

        inbox: asyncio.Queue[dict] = asyncio.Queue()

        async def pump():
            async with queue.iterator() as it:
                async for rmq in it:
                    async with rmq.process():
                        try:
                            evt = json.loads(rmq.body)
                        except Exception:
                            evt = {
                                "type": "update",
                                "raw": rmq.body.decode("utf-8", "ignore"),
                            }
                        await inbox.put(evt)
                        if evt.get("type") in ("order.complete", "order.failed"):
                            await inbox.put({"type": "__end__"})
                            break

        pump_task = asyncio.create_task(pump())
        try:
            while True:
                evt = await inbox.get()
                if evt.get("type") == "__end__":
                    break
                yield evt
        finally:
            try:
                await queue.unbind(events, routing_key=f"order.{order_id}.#")
            except Exception:
                pass
            try:
                await queue.delete(if_unused=False, if_empty=False)
            except Exception:
                pass
            pump_task.cancel()
