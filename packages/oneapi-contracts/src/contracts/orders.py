from datetime import datetime
from typing import  List, Tuple, Annotated, TypeAlias
from pydantic import BaseModel, Field
from .orders_status import OrderStatus

Lon = Annotated[float, Field(ge=-180, le=180)]
Lat = Annotated[float, Field(ge=-90,  le=90)]

Coordinate: TypeAlias = Tuple[Lon, Lat]

class OrderCreate(BaseModel):
    bbox: Annotated[List[Coordinate], Field(min_length=2, max_length=2)]
    time_start: datetime
    time_end: datetime

class OrderOut(BaseModel):
    id: str
    status: OrderStatus
    created_at: datetime
