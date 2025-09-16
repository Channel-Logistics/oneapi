from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db import get_db
from .. import models
from contracts import ProviderCreate, ProviderRead, ProviderUpdate

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=list[ProviderRead])
def list_providers(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    stmt = select(models.Provider).limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.post("", response_model=ProviderRead, status_code=201)
def create_provider(payload: ProviderCreate, db: Session = Depends(get_db)):
    exists = db.scalar(select(models.Provider).where(models.Provider.slug == payload.slug))
    if exists:
        raise HTTPException(status_code=409, detail="slug already exists")
    obj = models.Provider(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{provider_id}", response_model=ProviderRead)
def get_provider(provider_id: str, db: Session = Depends(get_db)):
    obj = db.get(models.Provider, provider_id)
    if not obj:
        raise HTTPException(status_code=404, detail="provider not found")
    return obj


@router.patch("/{provider_id}", response_model=ProviderRead)
def update_provider(provider_id: str, payload: ProviderUpdate, db: Session = Depends(get_db)):
    obj = db.get(models.Provider, provider_id)
    if not obj:
        raise HTTPException(status_code=404, detail="provider not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{provider_id}", status_code=204)
def delete_provider(provider_id: str, db: Session = Depends(get_db)):
    obj = db.get(models.Provider, provider_id)
    if not obj:
        raise HTTPException(status_code=404, detail="provider not found")
    db.delete(obj)
    db.commit()
    return obj
