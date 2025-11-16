from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models, schemas, crud
from .database import engine, SessionLocal
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

# Crée la base de données si elle n’existe pas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AirGuard API", version="1.0")

# Autoriser le dashboard à accéder à l’API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dépendance de session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"status": "ok", "message": "AirGuard API is running"}


@app.post("/events/", response_model=schemas.Event)
def create_event(event: schemas.EventCreate, db: Session = Depends(get_db)):
    return crud.create_event(db, event)


@app.get("/events/", response_model=list[schemas.Event])
def get_events(db: Session = Depends(get_db)):
    return crud.get_all_events(db)