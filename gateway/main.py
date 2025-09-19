from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.orders import router as orders_router
from services.messaging import Messaging
from services.storage import StorageClient
from settings import get_settings

settings = get_settings()
AMQP_URL = settings.amqp_url
STORAGE_URL = str(settings.storage_url)


app = FastAPI(title="Gateway - Orders + SSE")

ALLOWED_ORIGINS = settings.cors_allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    app.state.messaging = Messaging(AMQP_URL)
    await app.state.messaging.start()
    app.state.storage = StorageClient(STORAGE_URL)
    app.state.settings = settings


@app.on_event("shutdown")
async def shutdown():
    if getattr(app.state, "messaging", None):
        await app.state.messaging.stop()
    if getattr(app.state, "storage", None):
        await app.state.storage.close()


def get_messaging():
    return app.state.messaging


def get_storage():
    return app.state.storage


def get_settings_dep():
    return app.state.settings


app.include_router(orders_router)


@app.get("/health")
def health():
    return {"ok": True}
