from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def dummy_settings():
    s = MagicMock()
    s.AMQP_URL = "amqp://guest:guest@localhost:5672/"
    s.SENDGRID_API_KEY = "dummy"
    s.NOTIFY_EMAIL_FROM = "no-reply@example.com"
    s.NOTIFY_EMAIL_TO = "test@example.com"
    return s


@pytest.mark.asyncio
async def test_handle_event_started(dummy_settings):
    with (
        patch("notifier.get_settings", return_value=dummy_settings),
        patch("notifier.send_email") as mock_send,
    ):
        from notifier import handle_event

        evt = {"orderId": "order123", "type": "order.started"}
        await handle_event(evt)
        mock_send.assert_called_once_with(
            "Order started", "Order order123 has started."
        )


@pytest.mark.asyncio
async def test_handle_event_complete(dummy_settings):
    with (
        patch("notifier.get_settings", return_value=dummy_settings),
        patch("notifier.send_email") as mock_send,
    ):
        from notifier import handle_event

        evt = {"orderId": "order456", "type": "order.complete"}
        await handle_event(evt)
        mock_send.assert_called_once_with(
            "Order complete", "Order order456 finished successfully."
        )


@pytest.mark.asyncio
async def test_handle_event_failed(dummy_settings):
    with (
        patch("notifier.get_settings", return_value=dummy_settings),
        patch("notifier.send_email") as mock_send,
    ):
        from notifier import handle_event

        evt = {"orderId": "order789", "type": "order.failed", "error": "some error"}
        await handle_event(evt)
        mock_send.assert_called_once_with(
            "Order failed", "Order order789 failed: some error"
        )
