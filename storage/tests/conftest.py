import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport, Client
from fastapi.testclient import TestClient

from unittest.mock import MagicMock

from storage.app import create_app
from storage import db as db_module
from storage.routers import events as events_router_mod  # the module we test
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.db import Base

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def client(_integration_db):
    """
    Synchronous in-process FastAPI client for integration tests.
    Uses real database connections.
    """
    app = create_app()
    with TestClient(app) as client:
        yield client


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


@pytest.fixture(scope="session")
def _pg_container():
    """
    Session-scoped Postgres container for integration/e2e tests.
    """
    from testcontainers.postgres import PostgresContainer
    with PostgresContainer("postgres:16") as pg:
        yield pg


@pytest.fixture(scope="session")
def _integration_db(_pg_container):
    """
    Create a SQLAlchemy engine/session bound to the container and initialize schema,
    rebinding storage.db module-level engine/session so app dependencies use it.
    """
    url = _pg_container.get_connection_url()
    url = url.replace("postgresql+psycopg2", "postgresql+psycopg")

    engine = create_engine(url, future=True)
    TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    # Create schema
    Base.metadata.create_all(engine)

    # Rebind
    original_engine = getattr(db_module, "_engine", None)
    original_session_local = getattr(db_module, "SessionLocal", None)
    db_module._engine = engine
    db_module.SessionLocal = TestSessionLocal

    try:
        yield {"engine": engine, "SessionLocal": TestSessionLocal}
    finally:
        # Restore and cleanup
        if original_engine is not None:
            db_module._engine = original_engine
        if original_session_local is not None:
            db_module.SessionLocal = original_session_local
        Base.metadata.drop_all(engine)
