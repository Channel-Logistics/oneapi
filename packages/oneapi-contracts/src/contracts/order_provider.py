
import uuid
from typing import  Literal, Optional
from pydantic import BaseModel, Field


OrderProviderStatus = Literal["pending", "processing", "done", "failed"]

class OrderProviderCreate(BaseModel):
    order_id: uuid.UUID
    provider_id: uuid.UUID
    status: OrderProviderStatus = "pending"
    meta: dict = Field(default_factory=dict)


class OrderProviderRead(OrderProviderCreate):
    id: uuid.UUID
    last_error: Optional[str] = None


class OrderProviderUpdate(BaseModel):
    status: Optional[OrderProviderStatus] = None
    meta: Optional[dict] = None
    last_error: Optional[str] = None
