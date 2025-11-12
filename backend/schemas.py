from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NoiseEventBase(BaseModel):
    noise_level: float
    location: str
    device_id: str


class NoiseEventCreate(NoiseEventBase):
    pass


class NoiseEvent(NoiseEventBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
