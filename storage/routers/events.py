from contracts import EventCreate, EventRead
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db

router = APIRouter(prefix="/orders/{order_id}/events", tags=["events"])


@router.get("", response_model=list[EventRead])
def list_events(
    order_id: str,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    if not db.get(models.Order, order_id):
        raise HTTPException(status_code=404, detail="order not found")
    stmt = (
        select(models.Event)
        .where(models.Event.order_id == order_id)
        .order_by(models.Event.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt))


@router.post("", response_model=EventRead, status_code=201)
def create_event(order_id: str, payload: EventCreate, db: Session = Depends(get_db)):
    if not db.get(models.Order, order_id):
        raise HTTPException(status_code=404, detail="order not found")
    obj = models.Event(order_id=order_id, **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
