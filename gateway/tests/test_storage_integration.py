"""
Test storage service integration in the gateway (orders-centric).
"""

from unittest.mock import AsyncMock, patch

import pytest
from contracts import OrderCreate
from fastapi.testclient import TestClient
from main import app

from gateway.services.storage import StorageClient


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_storage_client():
    """Mock storage client for testing"""
    client = AsyncMock(spec=StorageClient)
    client.create_order.return_value = {"id": "test-order-id-123"}
    return client


@pytest.mark.asyncio
async def test_create_order(client, mock_storage_client):
    """POST /orders creates order in storage and returns id"""

    with (
        patch("main.get_storage", return_value=mock_storage_client),
        patch("main.get_messaging") as mock_msg,
    ):
        # Test data
        task_data = {
            "bbox": [-122.4, 37.7, -122.3, 37.8],
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-02T00:00:00Z",
            "provider": "test_provider",
        }

        response = client.post("/orders", json=task_data)

        assert response.status_code == 200
        data = response.json()
        assert "orderId" in data
        assert data["orderId"] == "test-order-id-123"
        assert "sseUrl" in data

        # Verify storage client was called
        mock_storage_client.create_order.assert_called_once()
        (arg,), _ = mock_storage_client.create_order.call_args
        assert isinstance(arg, OrderCreate)
        assert arg.bbox == [-122.4, 37.7, -122.3, 37.8]


@pytest.mark.asyncio
async def test_create_order_missing_fields(client):
    """Missing required order fields returns 400"""

    payload = {"provider": "test_provider"}
    response = client.post("/orders", json=payload)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_storage_client_error_handling(client, mock_storage_client):
    """Storage client exception becomes 400 from POST /orders"""

    mock_storage_client.create_order.side_effect = Exception("boom")
    with (
        patch("main.get_storage", return_value=mock_storage_client),
        patch("main.get_messaging"),
    ):
        payload = {
            "bbox": [-122.4, 37.7, -122.3, 37.8],
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-02T00:00:00Z",
        }
        response = client.post("/orders", json=payload)
        assert response.status_code == 400


def test_health_endpoint(client):
    """Test health endpoint still works"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
