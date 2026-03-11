# backend/routes/risk_event_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database.connection import get_db
from backend.models.risk_event import RiskEvent
from backend.services.risk_event_service import (
    create_risk_event,
    list_risk_events,
    delete_risk_event,
)
from backend.core.permission_guard import require_roles


router = APIRouter(prefix="/risk-events", tags=["risk-events"])


# ---------------------------------------------------------
# CREATE EVENT (ADMIN + AUDITOR)
# ---------------------------------------------------------

@router.post("/", response_model=dict)
def create_event(
    subsidy_id: int,
    event_type: str,
    severity: str,
    description: str,
    db: Session = Depends(get_db),
    user = Depends(require_roles("admin", "auditor"))
):

    if severity not in ["low", "medium", "high"]:
        raise HTTPException(status_code=400, detail="Severity must be low, medium, or high")

    event = create_risk_event(
        db=db,
        subsidy_id=subsidy_id,
        event_type=event_type,
        severity=severity,
        description=description,
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
# LIST EVENTS (PUBLIC / AUTHENTICATED)
# ---------------------------------------------------------

@router.get("/", response_model=List[dict])
def list_events(
    subsidy_id: int | None = None,
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
# DELETE EVENT (ADMIN ONLY)
# ---------------------------------------------------------

@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_roles("admin"))
):

    try:
        delete_risk_event(db, event_id)
        return {"message": "Risk event deleted"}

    except ValueError:
        raise HTTPException(status_code=404, detail="Risk event not found")