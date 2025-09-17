import asyncio
import json
import logging
from functools import lru_cache

import aio_pika
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


# --- Environment Settings ---
class Settings(BaseSettings):
    AMQP_URL: str = Field(..., description="AMQP connection string")
    SENDGRID_API_KEY: str = Field(..., description="SendGrid API key")
    NOTIFY_EMAIL_FROM: str = Field(..., description="Email address to send from")
    NOTIFY_EMAIL_TO: str = Field(..., description="Email address to send to")


@lru_cache
def get_settings() -> Settings:
    """Load settings once (cached)."""
    return Settings()


# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Notifications")


def send_email(subject: str, body: str):
    """Send a simple email using SendGrid"""
    settings = get_settings()
    message = Mail(
        from_email=settings.NOTIFY_EMAIL_FROM,
        to_emails=settings.NOTIFY_EMAIL_TO,
        subject=subject,
        plain_text_content=body,
    )
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"✅ Email sent: {response.status_code}")
    except Exception as e:
        logger.error(f"💥 Failed to send email: {e}")


async def handle_event(evt: dict):
    order_id = evt.get("orderId")
    evt_type = evt.get("type")

    if evt_type == "order.started":
        send_email("Order started", f"Order {order_id} has started.")
    elif evt_type == "order.complete":
        send_email("Order complete", f"Order {order_id} finished successfully.")
    elif evt_type == "order.failed":
        send_email("Order failed", f"Order {order_id} failed: {evt.get('error')}")


async def main():
    settings = get_settings()
    conn = await aio_pika.connect_robust(settings.AMQP_URL)
    ch = await conn.channel()
    await ch.set_qos(prefetch_count=10)

    # Declare the events exchange
    ex = await ch.declare_exchange("events", aio_pika.ExchangeType.TOPIC, durable=True)

    # Create a queue just for notifications
    q = await ch.declare_queue("notifications", durable=True)

    # Bind to order.*.started, order.*.complete, order.*.failed
    await q.bind(ex, routing_key="order.*.started")
    await q.bind(ex, routing_key="order.*.complete")
    await q.bind(ex, routing_key="order.*.failed")

    logger.info("📧 Notifications worker started, waiting for orders...")

    async with q.iterator() as queue_iter:
        async for msg in queue_iter:
            async with msg.process():
                try:
                    evt = json.loads(msg.body)
                    logger.info(f"📥 Received event: {evt}")
                    await handle_event(evt)
                except Exception as e:
                    logger.error(f"Error handling event: {e}")


if __name__ == "__main__":
    asyncio.run(main())
