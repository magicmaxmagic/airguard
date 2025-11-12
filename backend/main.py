from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List
import schemas
import models

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./airguard.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AirGuard API", description="Intrusion detection API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "AirGuard API is running"}


@app.post("/events/", response_model=schemas.NoiseEvent)
def create_noise_event(event: schemas.NoiseEventCreate, db: Session = Depends(get_db)):
    db_event = models.NoiseEvent(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@app.get("/events/", response_model=List[schemas.NoiseEvent])
def read_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    events = db.query(models.NoiseEvent).offset(skip).limit(limit).all()
    return events


@app.get("/events/{event_id}", response_model=schemas.NoiseEvent)
def read_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.NoiseEvent).filter(models.NoiseEvent.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
