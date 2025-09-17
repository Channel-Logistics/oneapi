import uuid
from enum import StrEnum
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderProviderStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class OrderProviderBase(BaseModel):
    """Shared fields between create/read."""

    model_config = ConfigDict(extra="forbid")

    order_id: uuid.UUID
    provider_id: uuid.UUID
    status: OrderProviderStatus = OrderProviderStatus.PENDING
    meta: Dict = Field(default_factory=dict)


class OrderProviderCreate(OrderProviderBase):
    """Create: order_id and provider_id required; status defaults to 'pending'."""

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v):
        if isinstance(v, str):
            return OrderProviderStatus(v.lower())
        return v


class OrderProviderUpdate(BaseModel):
    """Patch: all fields optional."""

    model_config = ConfigDict(extra="forbid")

    status: Optional[OrderProviderStatus] = None
    meta: Optional[Dict] = None
    last_error: Optional[str] = None


class OrderProviderRead(OrderProviderBase):
    """Read: adds id and error info; safe for ORM validation."""

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: uuid.UUID
    last_error: Optional[str] = None
