# --- ensure repo root is on sys.path so "import storage" works ---
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Walk upwards until we find a folder that contains the "storage" package
for p in [HERE] + list(HERE.parents):
    if (p / "storage" / "__init__.py").exists():
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))  # p is the repo root (parent of "storage")
        break
else:
    raise RuntimeError("Could not find repo root containing the 'storage' package")
# ----------------------------------------------------------------

from unittest.mock import MagicMock
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from storage.app import create_app
from storage import db as db_module
from storage.routers import events as events_router_mod  # the module we test


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest_asyncio.fixture
async def ac(mock_session):
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
