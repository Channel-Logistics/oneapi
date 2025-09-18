from contracts import OrderCreate
from fastapi import APIRouter, BackgroundTasks, Depends
from sse_starlette.sse import EventSourceResponse

from ..services.messaging import Messaging
from ..services.storage import StorageClient

router = APIRouter(prefix="/orders", tags=["orders"])


def get_messaging_dep():
    from ..main import get_messaging

    return get_messaging()


def get_storage_dep():
    from ..main import get_storage

    return get_storage()


@router.post("")
async def create_order(
    payload: OrderCreate,
    bg: BackgroundTasks,
    messaging: Messaging = Depends(get_messaging_dep),
    storage: StorageClient = Depends(get_storage_dep),
):
    created = await storage.create_order(payload)
    order_id = created["id"]
    bg.add_task(messaging.publish_order, order_id, payload.model_dump())
    return {"orderId": order_id, "sseUrl": f"/orders/{order_id}/events"}


@router.get("/{order_id}/events")
async def order_events(
    order_id: str, messaging: Messaging = Depends(get_messaging_dep)
):
    async def event_gen():
        async for evt in messaging.sse_events(order_id):
            yield {"event": evt.get("type", "order.update"), "data": evt}

    resp = EventSourceResponse(event_gen(), ping=15)
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["Connection"] = "keep-alive"
    resp.headers["X-Accel-Buffering"] = "no"
    return resp
