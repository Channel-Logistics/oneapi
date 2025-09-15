import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List

class ProviderBase(BaseModel):
    slug: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=128)
    sensor_types: List[str] = []
    active: bool = True

class ProviderCreate(BaseModel):
    slug: str
    name: str
    sensor_types: List[str] = Field(default_factory=list)
    active: bool = True

class ProviderRead(ProviderCreate):
    id: uuid.UUID
    created_at: datetime

class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    sensor_types: Optional[List[str]] = None
    active: Optional[bool] = None
