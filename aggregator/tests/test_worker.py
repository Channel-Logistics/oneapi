import json
from unittest.mock import patch

import pytest


# --- Dummy UmbraProvider to avoid real token logic ---
class DummyUmbraProvider:
    def __init__(self, *args, **kwargs):
        self.name = "Umbra"


# --- Dummy classes for channel and provider ---
class DummyChannel:
    def __init__(self):
        self.published = []

    async def get_exchange(self, _):
        return self

    async def publish(self, message, routing_key):
        self.published.append((json.loads(message.body), routing_key))


class DummyMessage:
    def __init__(self, body):
        self.body = body
        self.acked = False

    async def ack(self):
        self.acked = True


class DummyProvider:
    name = "Dummy"

    async def search_archive(self, start, end, bbox):
        return [{"id": f"fake-archive-{start}-{end}-{bbox}"}]

    async def search_feasibility(self, start, end, geometry):
        return [{"id": f"fake-feasibility-{start}-{end}-{geometry}"}]


# --- Patch UmbraProvider before importing worker ---
with patch("providers.umbra_canopy.UmbraProvider", DummyUmbraProvider):
    from worker import JobRequest, call_provider, process_order


# --- Tests ---
@pytest.mark.asyncio(loop_scope="function")
async def test_call_provider_search():
    ch = DummyChannel()
    provider = DummyProvider()
    req = JobRequest(
        start_date="2024-01-01T00:00:00Z",
        end_date="2099-01-01T00:00:00Z",
        bbox=[0, 0, 1, 1],
    )
    with patch("worker.PROVIDERS", [provider]):
        await call_provider(ch, "order123", provider, "search", req)
        
    # Check at least one provider.update event got published
    assert any("provider.update" in evt["type"] for evt, _ in ch.published)


@pytest.mark.asyncio(loop_scope="function")
async def test_process_order_with_unknown_type():
    ch = DummyChannel()
    payload = {"orderId": "order999", "type": "unknown"}
    msg = DummyMessage(json.dumps(payload).encode())

    with patch("worker.PROVIDERS", [DummyProvider()]):
        await process_order(ch, msg)
        
    assert msg.acked
    assert any(evt["type"] == "order.failed" for evt, _ in ch.published)
