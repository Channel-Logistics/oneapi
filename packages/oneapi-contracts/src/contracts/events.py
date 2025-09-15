import uuid
from datetime import datetime
from typing import Dict
from pydantic import BaseModel, Field, ConfigDict

class EventBase(BaseModel):
    """Shared fields for Events."""
    model_config = ConfigDict(extra='forbid')

    type: str
    data: Dict = Field(default_factory=dict)

class EventCreate(EventBase):
    """Create: requires type; data defaults to empty dict."""
    pass

class EventRead(EventBase):
    """Read: adds database-generated fields; ORM-friendly."""
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    id: uuid.UUID
    order_id: uuid.UUID
    created_at: datetime
