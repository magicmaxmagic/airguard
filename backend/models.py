from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class NoiseEvent(Base):
    __tablename__ = "noise_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    noise_level = Column(Float)
    location = Column(String)
    device_id = Column(String)
