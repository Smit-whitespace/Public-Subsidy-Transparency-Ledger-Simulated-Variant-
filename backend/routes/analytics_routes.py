from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from fastapi import Query
from typing import Optional

from backend.database.connection import get_db
from backend.services.analytics_service import (
    get_summary,
    get_sector_distribution,
    get_risk_distribution,
    get_year_trends,
    get_subsidy_score,
    get_high_risk_subsidies,
    get_sector_risk_overview,
    get_risk_trend,
)
from backend.schemas.analytics_schemas import (
    SummaryResponse,
    SectorDistributionItem,
    RiskDistributionResponse,
    YearTrendItem,
    SubsidyScoreResponse,
)
from typing import List

from backend.services.risk_engine import compute_risk_breakdown
from backend.schemas.risk_schemas import RiskBreakdownResponse
from backend.models.subsidy import Subsidy

from backend.core.permissions import Permissions
from backend.core.security import require_permission

from backend.services.anomaly_detection import get_anomaly_summary, check_subsidy_anomalies
from backend.ai.fraud_network import get_fraud_network_analysis
from backend.services.fund_flow_service import (
    get_fund_flow_summary,
    get_subsidy_fund_flow,
    get_fund_flow_by_sector,
    get_fund_flow_timeline,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=SummaryResponse)
def summary(db: Session = Depends(get_db)):
    return get_summary(db)


@router.get("/sector-distribution", response_model=List[SectorDistributionItem])
def sector_distribution(db: Session = Depends(get_db)):
    return get_sector_distribution(db)


@router.get("/risk-distribution", response_model=RiskDistributionResponse)
def risk_distribution(db: Session = Depends(get_db)):
    return get_risk_distribution(db)


@router.get("/year-trends", response_model=List[YearTrendItem])
def year_trends(db: Session = Depends(get_db)):
    return get_year_trends(db)


@router.get("/subsidy/{subsidy_id}/score", response_model=SubsidyScoreResponse)
def subsidy_score(subsidy_id: int, db: Session = Depends(get_db)):
    result = get_subsidy_score(db, subsidy_id)

    if not result:
        raise HTTPException(status_code=404, detail="Subsidy not found")

    return result

@router.get("/subsidy/{subsidy_id}/risk-breakdown", response_model=RiskBreakdownResponse)
def subsidy_risk_breakdown(subsidy_id: int, db: Session = Depends(get_db)):
    subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()

    if not subsidy:
        raise HTTPException(status_code=404, detail="Subsidy not found")

    result = compute_risk_breakdown(db, subsidy)

    return {
        "subsidy_id": subsidy.id,
        "risk_score": result["risk_score"],
        "transparency_score": result["transparency_score"],
        "breakdown": result["breakdown"],
    }

@router.get("/high-risk-subsidies")
def high_risk_subsidies(
    limit: int = Query(10, ge=1, le=50),
    sector: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    return get_high_risk_subsidies(
        db=db,
        limit=limit,
        sector=sector
    )


@router.get("/sector-risk-overview")
def sector_risk_overview(db: Session = Depends(get_db)):
    return get_sector_risk_overview(db)


@router.get("/subsidy/{subsidy_id}/risk-trend")
def subsidy_risk_trend(subsidy_id: int, db: Session = Depends(get_db)):
    return get_risk_trend(db, subsidy_id)

# ============================================================
# ANOMALY DETECTION ENDPOINTS
# ============================================================

@router.get("/anomalies")
def anomaly_summary(db: Session = Depends(get_db)):
    """
    Get summary of all anomaly detections in the system.
    Returns alerts by severity, type, and highest risk subsidies.
    """
    return get_anomaly_summary(db)


@router.get("/subsidy/{subsidy_id}/anomalies")
def subsidy_anomalies(subsidy_id: int, db: Session = Depends(get_db)):
    """
    Get anomaly detection results for a specific subsidy.
    """
    return {
        "subsidy_id": subsidy_id,
        "anomalies": check_subsidy_anomalies(db, subsidy_id)
    }