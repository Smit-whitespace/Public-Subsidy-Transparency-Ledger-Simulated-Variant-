"""
backend/services/fund_flow_service.py

Fund Flow Visualization - Track the movement of funds from:
Subsidy → Project → Disbursement

Provides API endpoints for visualizing fund distribution.
"""

from decimal import Decimal
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.subsidy import Subsidy
from backend.models.project import Project
from backend.models.disbursement import Disbursement


def get_fund_flow_summary(db: Session) -> Dict[str, Any]:
    """
    Get overall fund flow summary across all subsidies.
    """
    # Total subsidies and allocations
    total_subsidies = db.query(Subsidy).count()
    total_allocation = db.query(
        func.coalesce(func.sum(Subsidy.total_allocation), 0)
    ).scalar() or Decimal(0)
    
    # Total projects
    total_projects = db.query(Project).count()
    
    # Total disbursements
    total_disbursements = db.query(Disbursement).count()
    total_disbursed = db.query(
        func.coalesce(func.sum(Disbursement.amount), 0)
    ).scalar() or Decimal(0)
    
    # Calculate flow percentages
    disbursement_rate = 0
    if float(total_allocation) > 0:
        disbursement_rate = (float(total_disbursed) / float(total_allocation)) * 100
    
    project_rate = 0
    if total_subsidies > 0:
        project_rate = (total_projects / total_subsidies) * 100
    
    return {
        "total_subsidies": total_subsidies,
        "total_allocation": float(total_allocation),
        "total_projects": total_projects,
        "projects_per_subsidy": round(project_rate, 2),
        "total_disbursements": total_disbursements,
        "total_disbursed": float(total_disbursed),
        "disbursement_rate_percent": round(disbursement_rate, 2),
        "remaining_to_disburse": float(total_allocation) - float(total_disbursed)
    }


def get_subsidy_fund_flow(db: Session, subsidy_id: int) -> Dict[str, Any]:
    """
    Get detailed fund flow for a specific subsidy.
    Shows: Subsidy → Projects → Disbursements
    """
    subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()
    
    if not subsidy:
        return {"error": "Subsidy not found"}
    
    # Get projects linked to this subsidy
    projects = db.query(Project).filter(
        Project.subsidy_id == subsidy_id
    ).all()
    
    # Get disbursements for this subsidy
    disbursements = db.query(Disbursement).filter(
        Disbursement.subsidy_id == subsidy_id
    ).all()
    
    # Calculate flows
    subsidy_data = {
        "id": subsidy.id,
        "title": subsidy.title,
        "recipient": subsidy.recipient,
        "sector": subsidy.sector,
        "total_allocation": float(subsidy.total_allocation or 0),
        "status": str(subsidy.status.value) if hasattr(subsidy.status, 'value') else str(subsidy.status)
    }
    
    # Project flows
    project_flows = []
    for project in projects:
        # Get disbursements for this project (if linked to subsidy)
        project_disbursements = [
            d for d in disbursements 
            if d.subsidy_id == subsidy_id  # Simplified - project links via subsidy
        ]
        
        project_flows.append({
            "id": project.id,
            "name": project.name,
            "owner": project.owner,
            "status": project.status,
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "end_date": project.end_date.isoformat() if project.end_date else None,
            "disbursement_count": len(project_disbursements),
            "total_disbursed": sum(float(d.amount) for d in project_disbursements)
        })
    
    # Disbursement details
    disbursement_details = [
        {
            "id": d.id,
            "amount": float(d.amount),
            "currency": d.currency,
            "date": d.date.isoformat() if d.date else None,
            "approval_status": d.approval_status,
            "is_late": d.is_late,
            "is_suspicious": d.is_suspicious,
            "reference": d.reference
        }
        for d in disbursements
    ]
    
    total_disbursed = sum(float(d.amount) for d in disbursements)
    allocation = float(subsidy.total_allocation or 0)
    
    return {
        "subsidy": subsidy_data,
        "projects": project_flows,
        "disbursements": disbursement_details,
        "summary": {
            "project_count": len(projects),
            "disbursement_count": len(disbursements),
            "total_disbursed": total_disbursed,
            "remaining_allocation": max(0, allocation - total_disbursed),
            "disbursement_percentage": round((total_disbursed / allocation * 100) if allocation > 0 else 0, 2)
        }
    }


def get_fund_flow_by_sector(db: Session) -> List[Dict[str, Any]]:
    """
    Get fund flow breakdown by sector.
    """
    results = db.query(
        Subsidy.sector,
        func.count(Subsidy.id).label("subsidy_count"),
        func.sum(Subsidy.total_allocation).label("total_allocation"),
    ).group_by(Subsidy.sector).all()
    
    sector_flows = []
    for row in results:
        sector = row[0]
        subsidy_count = row[1]
        allocation = float(row[2] or 0)
        
        # Get project count for this sector
        project_count = db.query(Project).join(Subsidy).filter(
            Subsidy.sector == sector
        ).count()
        
        # Get disbursement count and total for this sector
        disbursement_data = db.query(
            func.count(Disbursement.id).label("count"),
            func.coalesce(func.sum(Disbursement.amount), 0).label("total")
        ).join(Subsidy).filter(Subsidy.sector == sector).first()
        
        disbursement_count = disbursement_data[0] if disbursement_data else 0
        disbursed = float(disbursement_data[1]) if disbursement_data else 0
        
        sector_flows.append({
            "sector": sector,
            "subsidy_count": subsidy_count,
            "project_count": project_count,
            "total_allocation": allocation,
            "disbursement_count": disbursement_count,
            "total_disbursed": disbursed,
            "disbursement_rate_percent": round((disbursed / allocation * 100) if allocation > 0 else 0, 2)
        })
    
    return sector_flows


def get_fund_flow_timeline(db: Session, subsidy_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get timeline of fund flow events.
    Can filter by subsidy or get all.
    """
    timeline = []
    
    if subsidy_id:
        # Get specific subsidy timeline
        subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()
        if subsidy:
            timeline.append({
                "date": subsidy.created_at.isoformat() if subsidy.created_at else None,
                "event_type": "subsidy_created",
                "entity_id": subsidy.id,
                "description": f"Subsidy created: {subsidy.title}",
                "amount": float(subsidy.total_allocation or 0)
            })
        
        projects = db.query(Project).filter(Project.subsidy_id == subsidy_id).all()
        for project in projects:
            timeline.append({
                "date": project.created_at.isoformat() if project.created_at else None,
                "event_type": "project_created",
                "entity_id": project.id,
                "description": f"Project created: {project.name}",
                "amount": None
            })
        
        disbursements = db.query(Disbursement).filter(
            Disbursement.subsidy_id == subsidy_id
        ).order_by(Disbursement.date.asc()).all()
        
        for d in disbursements:
            timeline.append({
                "date": d.date.isoformat() if d.date else None,
                "event_type": "disbursement",
                "entity_id": d.id,
                "description": f"Disbursement of {d.amount} {d.currency}",
                "amount": float(d.amount)
            })
    else:
        # Get all events (limit to recent 100)
        # Subsidies
        recent_subsidies = db.query(Subsidy).order_by(
            Subsidy.created_at.desc()
        ).limit(50).all()
        
        for s in recent_subsidies:
            timeline.append({
                "date": s.created_at.isoformat() if s.created_at else None,
                "event_type": "subsidy_created",
                "entity_id": s.id,
                "description": f"Subsidy: {s.title}",
                "amount": float(s.total_allocation or 0)
            })
        
        # Disbursements
        recent_disbursements = db.query(Disbursement).order_by(
            Disbursement.date.desc()
        ).limit(50).all()
        
        for d in recent_disbursements:
            timeline.append({
                "date": d.date.isoformat() if d.date else None,
                "event_type": "disbursement",
                "entity_id": d.id,
                "description": f"Disbursement",
                "amount": float(d.amount)
            })
    
    # Sort by date descending
    timeline.sort(key=lambda x: x["date"] or "", reverse=True)
    
    return {
        "events": timeline[:100],  # Limit to 100 events
        "total_events": len(timeline)
    }