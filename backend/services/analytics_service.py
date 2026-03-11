from decimal import Decimal
from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from sqlalchemy import case

from backend.models.subsidy import Subsidy
from backend.models.disbursement import Disbursement

from backend.models.subsidy import Subsidy
from backend.models.scoring_history import ScoringHistory
from sqlalchemy import func

def get_summary(db: Session):
    total_subsidies = db.query(Subsidy).count()

    active_subsidies = db.query(Subsidy).filter(Subsidy.status == "active").count()

    expired_subsidies = db.query(Subsidy).filter(Subsidy.status == "expired").count()

    total_allocation = db.query(func.coalesce(func.sum(Subsidy.total_allocation), 0)).scalar()

    total_disbursed = db.query(func.coalesce(func.sum(Disbursement.amount), 0)).scalar()

    completion_rate = Decimal("0")

    if total_allocation and total_allocation > 0:
        completion_rate = (Decimal(total_disbursed) / Decimal(total_allocation)) * 100

    return {
        "total_subsidies": total_subsidies,
        "active_subsidies": active_subsidies,
        "expired_subsidies": expired_subsidies,
        "total_allocation": total_allocation,
        "total_disbursed": total_disbursed,
        "completion_rate_percent": completion_rate.quantize(Decimal("0.01")),
    }


def get_sector_distribution(db: Session):
    results = (
        db.query(
            Subsidy.sector,
            func.sum(Subsidy.total_allocation)
        )
        .group_by(Subsidy.sector)
        .all()
    )

    return [
        {"sector": r[0], "total_allocation": r[1]}
        for r in results
    ]


def get_risk_distribution(db: Session):
    low = db.query(Subsidy).filter(Subsidy.risk_score < 40).count()
    medium = db.query(Subsidy).filter(Subsidy.risk_score.between(40, 70)).count()
    high = db.query(Subsidy).filter(Subsidy.risk_score > 70).count()

    return {
        "low_risk": low,
        "medium_risk": medium,
        "high_risk": high,
    }

from typing import Optional


def get_high_risk_subsidies(
    db: Session,
    limit: int = 10,
    sector: Optional[str] = None
):
    query = db.query(Subsidy).filter(Subsidy.risk_score >= 70)

    if sector:
        query = query.filter(Subsidy.sector == sector)

    results = (
        query
        .order_by(Subsidy.risk_score.desc(), Subsidy.id.asc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": s.id,
            "title": s.title,
            "sector": s.sector,
            "risk_score": s.risk_score,
            "transparency_score": s.transparency_score,
            "is_flagged": s.is_flagged,
        }
        for s in results
    ]


def get_year_trends(db: Session):
    results = (
        db.query(
            extract("year", Subsidy.start_date).label("year"),
            func.sum(Subsidy.total_allocation)
        )
        .group_by("year")
        .order_by("year")
        .all()
    )

    return [
        {"year": int(r[0]), "total_allocation": r[1]}
        for r in results
        if r[0] is not None
    ]


def get_subsidy_score(db: Session, subsidy_id: int):
    subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()

    if not subsidy:
        return None

    return {
        "subsidy_id": subsidy.id,
        "risk_score": subsidy.risk_score,
        "transparency_score": subsidy.transparency_score,
    }

def get_sector_risk_overview(db: Session):
    results = (
        db.query(
            Subsidy.sector,
            func.avg(Subsidy.risk_score),
            func.count(Subsidy.id),
            func.sum(Subsidy.total_allocation),
            func.sum(
                case(
                    (Subsidy.is_flagged == True, 1),
                    else_=0
                )
            )
        )
        .group_by(Subsidy.sector)
        .all()
    )

    return [
        {
            "sector": r[0],
            "avg_risk_score": round(float(r[1] or 0), 2),
            "subsidy_count": r[2],
            "total_allocation": float(r[3] or 0),
            "flagged_count": r[4] or 0,
        }
        for r in results
    ]

def get_risk_trend(db: Session, subsidy_id: int):
    records = (
        db.query(ScoringHistory)
        .filter(ScoringHistory.subsidy_id == subsidy_id)
        .order_by(ScoringHistory.calculated_at.asc())
        .all()
    )

    return [
        {
            "calculated_at": r.calculated_at,
            "risk_score": r.risk_score,
            "transparency_score": r.transparency_score,
        }
        for r in records
    ]