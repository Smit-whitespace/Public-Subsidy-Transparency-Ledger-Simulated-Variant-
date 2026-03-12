"""
backend/routes/public_routes.py

Public transparency endpoints accessible without authentication.
Designed for citizens, journalists, and the general public to browse
subsidy data, view analytics, and access transparency scores.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from backend.database.connection import get_db
from backend.models.subsidy import Subsidy
from backend.models.project import Project
from backend.models.disbursement import Disbursement
from backend.services.analytics_service import (
    get_summary,
    get_sector_distribution,
    get_year_trends,
    get_risk_distribution,
)
from backend.services.fund_flow_service import (
    get_fund_flow_summary,
    get_fund_flow_by_sector,
)


router = APIRouter(prefix="/public", tags=["Public Transparency"])


@router.get("/subsidies")
def public_list_subsidies(
    sector: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Subsidy)

    if sector:
        query = query.filter(Subsidy.sector == sector)

    if status:
        query = query.filter(Subsidy.status == status)

    if q:
        term = f"%{q}%"
        query = query.filter(
            or_(
                Subsidy.title.ilike(term),
                Subsidy.recipient.ilike(term),
            )
        )

    total = query.count()

    subsidies = (
        query.order_by(Subsidy.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "items": [
            {
                "id": s.id,
                "title": s.title,
                "recipient": s.recipient,
                "sector": s.sector,
                "total_allocation": str(s.total_allocation),
                "currency": s.currency,
                "status": s.status.value if hasattr(s.status, "value") else str(s.status),
                "risk_score": str(s.risk_score),
                "transparency_score": str(s.transparency_score),
                "start_date": s.start_date.isoformat() if s.start_date else None,
                "end_date": s.end_date.isoformat() if s.end_date else None,
            }
            for s in subsidies
        ],
    }


@router.get("/subsidies/{subsidy_id}")
def public_get_subsidy(
    subsidy_id: int,
    db: Session = Depends(get_db),
):
    subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()

    if not subsidy:
        raise HTTPException(status_code=404, detail="Subsidy not found")

    projects = (
        db.query(Project)
        .filter(Project.subsidy_id == subsidy_id)
        .all()
    )

    disbursements = (
        db.query(Disbursement)
        .filter(Disbursement.subsidy_id == subsidy_id)
        .all()
    )

    total_disbursed = sum(float(d.amount) for d in disbursements)
    allocation = float(subsidy.total_allocation or 0)

    return {
        "subsidy": {
            "id": subsidy.id,
            "title": subsidy.title,
            "recipient": subsidy.recipient,
            "sector": subsidy.sector,
            "total_allocation": str(subsidy.total_allocation),
            "currency": subsidy.currency,
            "description": subsidy.description,
            "status": subsidy.status.value if hasattr(subsidy.status, "value") else str(subsidy.status),
            "risk_score": str(subsidy.risk_score),
            "transparency_score": str(subsidy.transparency_score),
            "start_date": subsidy.start_date.isoformat() if subsidy.start_date else None,
            "end_date": subsidy.end_date.isoformat() if subsidy.end_date else None,
            "created_at": subsidy.created_at.isoformat() if subsidy.created_at else None,
        },
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "status": p.status,
                "owner": p.owner,
                "start_date": p.start_date.isoformat() if p.start_date else None,
                "end_date": p.end_date.isoformat() if p.end_date else None,
            }
            for p in projects
        ],
        "disbursement_summary": {
            "count": len(disbursements),
            "total_disbursed": total_disbursed,
            "remaining": max(0, allocation - total_disbursed),
            "completion_percent": round((total_disbursed / allocation * 100) if allocation > 0 else 0, 2),
        },
    }


@router.get("/analytics/summary")
def public_analytics_summary(db: Session = Depends(get_db)):
    return get_summary(db)


@router.get("/analytics/sector-distribution")
def public_sector_distribution(db: Session = Depends(get_db)):
    return get_sector_distribution(db)


@router.get("/analytics/year-trends")
def public_year_trends(db: Session = Depends(get_db)):
    return get_year_trends(db)


@router.get("/analytics/risk-distribution")
def public_risk_distribution(db: Session = Depends(get_db)):
    return get_risk_distribution(db)


@router.get("/analytics/fund-flow")
def public_fund_flow_summary(db: Session = Depends(get_db)):
    return get_fund_flow_summary(db)


@router.get("/analytics/fund-flow/sectors")
def public_fund_flow_sectors(db: Session = Depends(get_db)):
    return get_fund_flow_by_sector(db)


@router.get("/transparency-scores")
def public_transparency_scores(
    limit: int = Query(20, ge=1, le=100),
    sector: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Subsidy)

    if sector:
        query = query.filter(Subsidy.sector == sector)

    subsidies = (
        query.order_by(Subsidy.transparency_score.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": s.id,
            "title": s.title,
            "sector": s.sector,
            "recipient": s.recipient,
            "transparency_score": str(s.transparency_score),
            "risk_score": str(s.risk_score),
            "status": s.status.value if hasattr(s.status, "value") else str(s.status),
        }
        for s in subsidies
    ]


@router.get("/sectors")
def public_list_sectors(db: Session = Depends(get_db)):
    results = (
        db.query(
            Subsidy.sector,
            func.count(Subsidy.id).label("count"),
            func.sum(Subsidy.total_allocation).label("total_allocation"),
        )
        .group_by(Subsidy.sector)
        .all()
    )

    return [
        {
            "sector": r[0],
            "subsidy_count": r[1],
            "total_allocation": str(r[2] or 0),
        }
        for r in results
    ]
