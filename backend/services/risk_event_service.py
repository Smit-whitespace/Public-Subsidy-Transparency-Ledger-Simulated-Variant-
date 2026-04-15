# backend/services/risk_event_service.py

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.models.risk_event import RiskEvent
from backend.services.risk_engine import recalculate_subsidy_score


# ==========================================================
# CREATE
# ==========================================================

def create_risk_event(
    db: Session,
    subsidy_id: int,
    event_type: str,
    severity: str,
    description: str,
    commit: bool = True,
) -> RiskEvent:
    """
    Create a risk event and trigger recalculation.
    """

    try:
        event = RiskEvent(
            subsidy_id=subsidy_id,
            event_type=event_type,
            severity=severity,
            description=description,
        )

        db.add(event)

        if commit:
            db.commit()
            db.refresh(event)

            # 🔥 Critical: Recalculate risk after event creation
            recalculate_subsidy_score(db, subsidy_id)
            db.commit()

        return event

    except SQLAlchemyError:
        db.rollback()
        raise RuntimeError("DB error while creating risk event")


# ==========================================================
# READ
# ==========================================================

def get_risk_event_by_id(
    db: Session,
    event_id: int
) -> Optional[RiskEvent]:

    return db.query(RiskEvent).filter(RiskEvent.id == event_id).first()


def list_risk_events(
    db: Session,
    subsidy_id: Optional[int] = None
) -> List[RiskEvent]:

    query = db.query(RiskEvent)

    if subsidy_id is not None:
        query = query.filter(RiskEvent.subsidy_id == subsidy_id)

    return query.order_by(RiskEvent.detected_at.desc()).all()


# ==========================================================
# DELETE
# ==========================================================

def delete_risk_event(
    db: Session,
    event_id: int,
    commit: bool = True
) -> None:

    event = get_risk_event_by_id(db, event_id)

    if not event:
        raise ValueError("Risk event not found")

    subsidy_id = event.subsidy_id

    try:
        db.delete(event)

        if commit:
            db.commit()

            # 🔥 Recalculate after deletion
            recalculate_subsidy_score(db, subsidy_id)
            db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise RuntimeError("DB error while deleting risk event")