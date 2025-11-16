from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from .database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    type = Column(String, default="noise")
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Event id={self.id} device={self.device_id} value={self.value:.2f}dB @ {self.timestamp}>"