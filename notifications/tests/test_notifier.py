from unittest.mock import patch

import pytest

# Patch send_email before importing notifier
with patch("notifier.send_email") as mock_send:
    from notifier import handle_event


# --- Tests ---
@pytest.mark.asyncio
async def test_handle_event_started():
    evt = {"orderId": "order123", "type": "order.started"}
    with patch("notifier.send_email") as mock_send:
        await handle_event(evt)
        mock_send.assert_called_once_with(
            "Order started", "Order order123 has started."
        )


@pytest.mark.asyncio
async def test_handle_event_complete():
    evt = {"orderId": "order456", "type": "order.complete"}
    with patch("notifier.send_email") as mock_send:
        await handle_event(evt)
        mock_send.assert_called_once_with(
            "Order complete", "Order order456 finished successfully."
        )


@pytest.mark.asyncio
async def test_handle_event_failed():
    evt = {"orderId": "order789", "type": "order.failed", "error": "some error"}
    with patch("notifier.send_email") as mock_send:
        await handle_event(evt)
        mock_send.assert_called_once_with(
            "Order failed", "Order order789 failed: some error"
        )
