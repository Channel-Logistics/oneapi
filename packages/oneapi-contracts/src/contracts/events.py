import uuid
from pydantic import BaseModel, Field
from datetime import datetime

class EventCreate(BaseModel):
    type: str
    data: dict = Field(default_factory=dict)


class EventRead(EventCreate):
    id: uuid.UUID
    order_id: uuid.UUID
    created_at: datetime
