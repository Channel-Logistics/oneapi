from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from ..db import get_db
from .. import models
from contracts import OrderCreate, OrderRead, OrderUpdate, OrderStatus

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderRead])
def list_orders(
    db: Session = Depends(get_db),
    status: OrderStatus | None = None,
    start_from: datetime | None = None,
    end_to: datetime | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    stmt = select(models.Order)
    conds = []
    if status:
        conds.append(models.Order.status == status)
    if start_from:
        conds.append(models.Order.start_date >= start_from)
    if end_to:
        conds.append(models.Order.end_date <= end_to)
    if conds:
        stmt = stmt.where(and_(*conds))
    stmt = stmt.order_by(models.Order.created_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.post("", response_model=OrderRead, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    obj = models.Order(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: str, db: Session = Depends(get_db)):
    obj = db.get(models.Order, order_id)
    if not obj:
        raise HTTPException(status_code=404, detail="order not found")
    return obj


@router.patch("/{order_id}", response_model=OrderRead)
def update_order(order_id: str, payload: OrderUpdate, db: Session = Depends(get_db)):
    obj = db.get(models.Order, order_id)
    if not obj:
        raise HTTPException(status_code=404, detail="order not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: str, db: Session = Depends(get_db)):
    obj = db.get(models.Order, order_id)
    if not obj:
        return
    db.delete(obj)
    db.commit()
