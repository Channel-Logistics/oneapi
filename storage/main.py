from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .settings import settings
from .routers import providers, events, order_providers, orders

app = FastAPI(title=settings.APP_NAME, version="0.1.0")

@app.get("/health")
def health():
    return JSONResponse({"ok": True, "service": settings.APP_NAME})

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(providers.router)
app.include_router(events.router)
app.include_router(order_providers.router)
app.include_router(orders.router)

