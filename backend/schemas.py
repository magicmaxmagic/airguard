from pydantic import BaseModel
from datetime import datetime

class EventBase(BaseModel):
    device_id: str
    type: str
    value: float
    timestamp: datetime

class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: int
    class Config:
        orm_mode = True