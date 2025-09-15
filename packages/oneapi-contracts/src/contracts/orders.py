import uuid
from datetime import datetime
from typing import  Literal, List, Tuple, Annotated, TypeAlias, Optional
from pydantic import BaseModel, Field

OrderStatus = Literal["pending", "processing", "done", "failed"]

Lon = Annotated[float, Field(ge=-180, le=180)]
Lat = Annotated[float, Field(ge=-90,  le=90)]

Coordinate: TypeAlias = Tuple[Lon, Lat]

class OrderCreate(BaseModel):
    bbox: Optional[List[float]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: OrderStatus = "pending"

class OrderRead(OrderCreate):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

class OrderUpdate(BaseModel):
    bbox: Optional[List[float]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[OrderStatus] = None

