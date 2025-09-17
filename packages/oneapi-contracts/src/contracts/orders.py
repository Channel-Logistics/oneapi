import uuid
from datetime import datetime
from enum import StrEnum
from typing import Annotated, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


Lon = Annotated[float, Field(ge=-180, le=180)]
Lat = Annotated[float, Field(ge=-90, le=90)]
Coordinate = Tuple[Lon, Lat]
BBox = Annotated[List[float], Field(min_length=4, max_length=4)]


class OrderBase(BaseModel):
    """Shared read/write fields (write paths may override requiredness)."""

    model_config = ConfigDict(extra="forbid")

    bbox: BBox
    start_date: datetime
    end_date: datetime
    status: OrderStatus = OrderStatus.PENDING

    @field_validator("bbox")
    @classmethod
    def bbox_order(cls, v: Optional[List[float]]):
        if v is None:
            return v
        min_lon, min_lat, max_lon, max_lat = v
        if not (min_lon < max_lon and min_lat < max_lat):
            raise ValueError(
                "bbox must be [minLon, minLat, maxLon, maxLat] with min < max"
            )
        return v


class OrderCreate(OrderBase):
    """Create requires bbox, start_date, end_date; status still defaults to 'pending'."""

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, end: datetime, info):
        start = info.data.get("start_date")
        if start and end <= start:
            raise ValueError("end_date must be strictly greater than start_date")
        return end

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v):
        if isinstance(v, str):
            return OrderStatus(v.lower())
        return v


class OrderUpdate(BaseModel):
    """Patch: all optional; forbid unknown fields."""

    model_config = ConfigDict(extra="forbid")
    bbox: Optional[BBox] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[OrderStatus] = None

    @field_validator("end_date")
    @classmethod
    def end_after_start_if_both(cls, end: Optional[datetime], info):
        start = info.data.get("start_date")
        if start and end and end <= start:
            raise ValueError("end_date must be strictly greater than start_date")
        return end


class OrderRead(OrderBase):
    """Read model; safe to validate from ORM objects."""

    model_config = ConfigDict(from_attributes=True, extra="ignore")
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
