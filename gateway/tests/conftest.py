from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from main import app


@pytest.fixture
def mock_amqp_connection():
    """Mock AMQP connection and channel for testing."""
    mock_conn = AsyncMock()
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()

    mock_channel.get_exchange.return_value = mock_exchange
    mock_conn.channel.return_value = mock_channel

    return mock_conn, mock_channel, mock_exchange


@pytest.fixture
def client():
    """
    Synchronous in-process FastAPI client for integration tests.
    """
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def ac(mock_amqp_connection):
    """
    Async FastAPI client with mocked AMQP dependencies.
    """
    mock_conn, mock_channel, mock_exchange = mock_amqp_connection

    with patch("main.amqp_conn", mock_conn), patch("main.amqp_channel", mock_channel):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.fixture
def client_with_mocked_amqp(mock_amqp_connection):
    """
    Synchronous client with mocked AMQP dependencies.
    """
    mock_conn, mock_channel, mock_exchange = mock_amqp_connection

    with patch("main.amqp_conn", mock_conn), patch("main.amqp_channel", mock_channel):
        with TestClient(app) as client:
            yield client
