from unittest.mock import MagicMock
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from storage.app import create_app
from storage import db as db_module


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest_asyncio.fixture
async def async_client(mock_session):
    """
    In-process FastAPI client with the DB dependency overridden to our mock.
    Useful when we want to drive the route through FastAPI (status codes, etc).
    """
    def _override():
        yield mock_session

    app = create_app()

    app.dependency_overrides[db_module.get_session] = _override
    if hasattr(db_module, "get_db"):
        app.dependency_overrides[db_module.get_db] = _override

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
