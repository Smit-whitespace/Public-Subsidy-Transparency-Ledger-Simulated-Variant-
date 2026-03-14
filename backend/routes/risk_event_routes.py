# backend/routes/risk_event_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from backend.database.connection import get_db
from backend.models.risk_event import RiskEvent
from backend.services.risk_event_service import (
    create_risk_event,
    list_risk_events,
    delete_risk_event,
)
from backend.core.permission_guard import require_roles


router = APIRouter(prefix="/risk-events", tags=["risk-events"])

VALID_SEVERITIES = ["low", "medium", "high"]


class RiskEventCreate(BaseModel):
    subsidy_id: int
    event_type: str
    severity: str
    description: str


class RiskEventUpdate(BaseModel):
    event_type: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None


# ---------------------------------------------------------
# CREATE EVENT (ADMIN + AUDITOR)
# ---------------------------------------------------------

@router.post("/", response_model=dict, status_code=201)
def create_event(
    payload: RiskEventCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("admin", "auditor"))
):
    if payload.severity not in VALID_SEVERITIES:
        raise HTTPException(status_code=400, detail="Severity must be low, medium, or high")

    event = create_risk_event(
        db=db,
        subsidy_id=payload.subsidy_id,
        event_type=payload.event_type,
        severity=payload.severity,
        description=payload.description,
    )

    return {
        "id": event.id,
        "subsidy_id": event.subsidy_id,
        "event_type": event.event_type,
        "severity": event.severity,
        "description": event.description,
        "detected_at": event.detected_at,
    }


# ---------------------------------------------------------
# LIST EVENTS
# ---------------------------------------------------------

@router.get("/", response_model=List[dict])
def list_events(
    subsidy_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    events = list_risk_events(db, subsidy_id=subsidy_id)
    return [
        {
            "id": e.id,
            "subsidy_id": e.subsidy_id,
            "event_type": e.event_type,
            "severity": e.severity,
            "description": e.description,
            "detected_at": e.detected_at,
        }
        for e in events
    ]


# ---------------------------------------------------------
# GET SINGLE EVENT
# ---------------------------------------------------------

@router.get("/{event_id}", response_model=dict)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
):
    event = db.query(RiskEvent).filter(RiskEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Risk event not found")
    return {
        "id": event.id,
        "subsidy_id": event.subsidy_id,
        "event_type": event.event_type,
        "severity": event.severity,
        "description": event.description,
        "detected_at": event.detected_at,
    }


# ---------------------------------------------------------
# UPDATE EVENT (ADMIN ONLY)
# ---------------------------------------------------------

@router.patch("/{event_id}", response_model=dict)
def update_event(
    event_id: int,
    payload: RiskEventUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("admin"))
):
    event = db.query(RiskEvent).filter(RiskEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Risk event not found")

    if payload.severity and payload.severity not in VALID_SEVERITIES:
        raise HTTPException(status_code=400, detail="Severity must be low, medium, or high")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)

    return {
        "id": event.id,
        "subsidy_id": event.subsidy_id,
        "event_type": event.event_type,
        "severity": event.severity,
        "description": event.description,
        "detected_at": event.detected_at,
    }


# ---------------------------------------------------------
# DELETE EVENT (ADMIN ONLY)
# ---------------------------------------------------------

@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles("admin"))
):
    try:
        delete_risk_event(db, event_id)
        return {"message": "Risk event deleted"}
    except ValueError:
        raise HTTPException(status_code=404, detail="Risk event not found")