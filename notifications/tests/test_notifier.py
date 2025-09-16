from unittest.mock import patch

import pytest

# Patch send_email before importing notifier
with patch("notifier.send_email") as mock_send:
    from notifier import handle_event


# --- Tests ---
@pytest.mark.asyncio
async def test_handle_event_started():
    evt = {"taskId": "task123", "type": "task.started"}
    with patch("notifier.send_email") as mock_send:
        await handle_event(evt)
        mock_send.assert_called_once_with("Task started", "Task task123 has started.")


@pytest.mark.asyncio
async def test_handle_event_complete():
    evt = {"taskId": "task456", "type": "task.complete"}
    with patch("notifier.send_email") as mock_send:
        await handle_event(evt)
        mock_send.assert_called_once_with(
            "Task complete", "Task task456 finished successfully."
        )


@pytest.mark.asyncio
async def test_handle_event_failed():
    evt = {"taskId": "task789", "type": "task.failed", "error": "some error"}
    with patch("notifier.send_email") as mock_send:
        await handle_event(evt)
        mock_send.assert_called_once_with(
            "Task failed", "Task task789 failed: some error"
        )
