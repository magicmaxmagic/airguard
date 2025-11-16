from sqlalchemy.orm import Session
from . import models, schemas
import logging
from datetime import datetime

logger = logging.getLogger("AirGuard")

def create_event(db: Session, event: schemas.EventCreate):
    """Insère un nouvel événement dans la base de données."""
    try:
        logger.info(f"📝 Tentative d'insertion : {event.device_id} | {event.type} | {event.value:.2f} dB")

        db_event = models.Event(**event.dict())
        db.add(db_event)
        db.commit()
        db.refresh(db_event)

        logger.info(f"✅ Insertion réussie (ID={db_event.id}) à {datetime.utcnow().isoformat()} — "
                    f"{db_event.value:.2f} dB par {db_event.device_id}")

        return db_event

    except Exception as e:
        logger.error(f"❌ Erreur d’insertion dans la DB : {e}")
        db.rollback()
        raise

def get_all_events(db: Session):
    """Retourne tous les événements triés par timestamp."""
    events = db.query(models.Event).order_by(models.Event.timestamp.desc()).all()
    logger.info(f"📦 {len(events)} événements récupérés depuis la base.")
    return events