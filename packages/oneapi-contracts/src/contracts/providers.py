import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProviderBase(BaseModel):
    """Shared read/write fields."""

    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=128)
    sensor_types: List[str] = Field(default_factory=list)
    active: bool = True

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, v: str) -> str:
        nv = v.strip().lower()
        if " " in nv:
            raise ValueError("slug must not contain spaces; use dashes/underscores")
        return nv


class ProviderCreate(ProviderBase):
    """Create requires slug & name; others default."""

    # Inherit constraints and defaults; no changes needed
    pass


class ProviderUpdate(BaseModel):
    """Patch: everything optional; forbid unknown fields."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    sensor_types: Optional[List[str]] = None
    active: Optional[bool] = None


class ProviderRead(ProviderBase):
    """Read model; safe to validate from ORM objects."""

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: uuid.UUID
    created_at: datetime
