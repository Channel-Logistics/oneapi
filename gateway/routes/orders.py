from contracts import OrderCreate
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import ValidationError
from services.messaging import Messaging
from services.storage import StorageClient
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/orders", tags=["orders"])


def get_messaging_dep():
    from main import get_messaging

    return get_messaging()


def get_storage_dep():
    from main import get_storage

    return get_storage()


@router.post("")
async def create_order(
    payload: dict,
    bg: BackgroundTasks,
    messaging: Messaging = Depends(get_messaging_dep),
    storage: StorageClient = Depends(get_storage_dep),
):
    try:
        allowed_keys = set(OrderCreate.model_fields.keys())
        filtered = {k: v for k, v in (payload or {}).items() if k in allowed_keys}
        order = OrderCreate(**filtered)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail="Invalid order payload") from e

    try:
        created = await storage.create_order(order)
    except HTTPException:
        # propagate HTTP errors from StorageClient as-is
        raise
    except Exception as e:
        # map unexpected storage errors to 400 as per tests
        raise HTTPException(status_code=400, detail=str(e)) from e

    order_id = created["id"]
    bg.add_task(messaging.publish_order, order_id, order.model_dump())
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
