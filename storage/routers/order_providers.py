from contracts import (
    OrderProviderCreate,
    OrderProviderRead,
    OrderProviderStatus,
    OrderProviderUpdate,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db

router = APIRouter(prefix="/order-providers", tags=["order_providers"])


@router.get("", response_model=list[OrderProviderRead])
def list_order_providers(
    db: Session = Depends(get_db),
    order_id: str | None = None,
    provider_id: str | None = None,
    status: OrderProviderStatus | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    stmt = select(models.OrderProvider)
    conds = []
    if order_id:
        conds.append(models.OrderProvider.order_id == order_id)
    if provider_id:
        conds.append(models.OrderProvider.provider_id == provider_id)
    if status:
        conds.append(models.OrderProvider.status == status)
    if conds:
        stmt = stmt.where(and_(*conds))
    stmt = stmt.order_by(models.OrderProvider.id.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.post("", response_model=OrderProviderRead, status_code=201)
def create_order_provider(payload: OrderProviderCreate, db: Session = Depends(get_db)):
    if not db.get(models.Order, payload.order_id):
        raise HTTPException(status_code=404, detail="order not found")
    if not db.get(models.Provider, payload.provider_id):
        raise HTTPException(status_code=404, detail="provider not found")
    obj = models.OrderProvider(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{id}", response_model=OrderProviderRead)
def get_order_provider(id: str, db: Session = Depends(get_db)):
    obj = db.get(models.OrderProvider, id)
    if not obj:
        raise HTTPException(status_code=404, detail="order_provider not found")
    return obj


@router.patch("/{id}", response_model=OrderProviderRead)
def update_order_provider(
    id: str, payload: OrderProviderUpdate, db: Session = Depends(get_db)
):
    obj = db.get(models.OrderProvider, id)
    if not obj:
        raise HTTPException(status_code=404, detail="order_provider not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{id}", status_code=204)
def delete_order_provider(id: str, db: Session = Depends(get_db)):
    obj = db.get(models.OrderProvider, id)
    if not obj:
        return
    db.delete(obj)
    db.commit()
