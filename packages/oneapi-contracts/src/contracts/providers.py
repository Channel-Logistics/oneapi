from datetime import datetime
from pydantic import BaseModel, Field
from typing import List

class ProviderBase(BaseModel):
    slug: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=128)
    sensor_types: List[str] = []
    active: bool = True

class ProviderCreate(ProviderBase):
    pass

class ProviderOut(ProviderBase):
    id: str
    created_at: datetime
