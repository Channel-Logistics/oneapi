from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import db as db_module
from .routers import events, order_providers, orders, providers
from .settings import settings as default_settings


def create_app(
    *,
    settings=default_settings,
    session_override=None,
) -> FastAPI:
    """
    Build and wire a new FastAPI app instance.
    - settings: allows injecting a custom Settings for tests
    - session_override: allows injecting a custom get_db for tests
    """
    app = FastAPI(title=settings.APP_NAME, version="0.1.0")

    app.get("/health")(lambda: {"ok": True, "service": settings.APP_NAME})

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # include your routers
    app.include_router(providers.router)
    app.include_router(events.router)
    app.include_router(order_providers.router)
    app.include_router(orders.router)

    # test-time DB override
    if session_override is not None:
        app.dependency_overrides[db_module.get_db] = session_override

    return app
