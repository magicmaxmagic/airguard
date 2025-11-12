import os
import logging
from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, constr, condecimal
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# === Configuration === #
load_dotenv()
DB_URL = os.getenv("DB_URL", "sqlite:///./airguard.db")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("airguard")

# === DB setup === #
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    type = Column(String)
    value = Column(Float)
    timestamp = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# === API === #
app = FastAPI(title="AirGuard API v0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class EventIn(BaseModel):
    device_id: constr(min_length=2)
    type: str
    value: condecimal(gt=0)
    timestamp: datetime

@app.get("/")
def health():
    return {"status": "ok", "version": "0.1"}

@app.post("/events/")
def add_event(event: EventIn, db: Session = Depends(get_db)):
    row = Event(**event.dict())
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info(f"Event received: {row.device_id} {row.value}")
    return {"status": "received", "id": row.id}

@app.get("/events/")
def list_events(db: Session = Depends(get_db)):
    rows = db.query(Event).order_by(Event.timestamp.desc()).limit(200).all()
    return [dict(
        id=r.id,
        device_id=r.device_id,
        type=r.type,
        value=r.value,
        timestamp=r.timestamp.isoformat(),
        created_at=r.created_at.isoformat(),
    ) for r in rows]