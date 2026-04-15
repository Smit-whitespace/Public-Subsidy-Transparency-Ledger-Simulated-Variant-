"""
backend/routes/demo_routes.py

Public endpoints for demo mode control - no authentication required.
These endpoints allow the frontend to check and toggle demo mode status.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models import Subsidy, Project, Disbursement, RiskEvent
from backend.config import settings
from backend.core.permission_guard import require_roles

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/status")
def get_demo_status():
    """Get current demo mode status - public endpoint."""
    return {
        "demo_mode": settings.DEMO_MODE,
        "message": "Demo mode is ON - data will be auto-seeded on startup" if settings.DEMO_MODE else "Demo mode is OFF - database will remain empty"
    }


@router.post("/toggle")
def toggle_demo_mode(db: Session = Depends(get_db), user = Depends(require_roles("admin"))):
    """Toggle demo mode and optionally seed/clear data - public endpoint."""
    global settings
    
    # Toggle the setting
    settings.DEMO_MODE = not settings.DEMO_MODE
    
    result = {
        "demo_mode": settings.DEMO_MODE,
        "message": "Demo mode enabled" if settings.DEMO_MODE else "Demo mode disabled"
    }
    
    # If enabling, seed data
    if settings.DEMO_MODE:
        try:
            from backend.demo.demo_mode import ensure_demo_data
            seed_result = ensure_demo_data()
            result["seeded"] = seed_result.get("seeded", False)
            result["stats"] = seed_result.get("stats")
        except Exception as e:
            result["error"] = str(e)
    else:
        try:
            deleted_counts = {
                "risk_events": db.query(RiskEvent).delete(),
                "disbursements": db.query(Disbursement).delete(),
                "projects": db.query(Project).delete(),
                "subsidies": db.query(Subsidy).delete()
            }
            db.commit()
            result["message"] += " - All demo data cleared. System now shows empty state."
            result["deleted"] = deleted_counts
        except Exception as e:
            db.rollback()
            result["error"] = str(e)
    
    return result


@router.post("/seed")
def seed_demo_data(db: Session = Depends(get_db), user = Depends(require_roles("admin"))):
    """Manually trigger demo data seeding - public endpoint."""
    try:
        from backend.demo.demo_mode import ensure_demo_data
        result = ensure_demo_data()
        return {
            "status": "success",
            "seeded": result.get("seeded", False),
            "stats": result.get("stats"),
            "message": result.get("message", "Data seeded successfully")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")


@router.post("/clear")
def clear_demo_data(db: Session = Depends(get_db), user = Depends(require_roles("admin"))):
    """Clear all demo data (keep roles and users) - public endpoint."""
    try:
        deleted_counts = {
            "risk_events": db.query(RiskEvent).delete(),
            "disbursements": db.query(Disbursement).delete(),
            "projects": db.query(Project).delete(),
            "subsidies": db.query(Subsidy).delete()
        }
        db.commit()
        
        return {
            "status": "success",
            "deleted": deleted_counts,
            "message": "All demo data cleared. System now shows empty state."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Clear failed: {str(e)}")


@router.get("/stats")
def get_data_stats(db: Session = Depends(get_db)):
    """Get current database statistics - public endpoint."""
    return {
        "subsidies": db.query(Subsidy).count(),
        "projects": db.query(Project).count(),
        "disbursements": db.query(Disbursement).count(),
        "risk_events": db.query(RiskEvent).count(),
        "flagged_subsidies": db.query(Subsidy).filter(Subsidy.is_flagged == True).count(),
        "demo_mode": settings.DEMO_MODE
    }