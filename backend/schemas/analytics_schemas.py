from decimal import Decimal
from typing import List, Dict
from pydantic import BaseModel


class SummaryResponse(BaseModel):
    total_subsidies: int
    active_subsidies: int
    expired_subsidies: int
    total_allocation: Decimal
    total_disbursed: Decimal
    completion_rate_percent: Decimal


class SectorDistributionItem(BaseModel):
    sector: str
    total_allocation: Decimal


class RiskDistributionResponse(BaseModel):
    low_risk: int
    medium_risk: int
    high_risk: int


class YearTrendItem(BaseModel):
    year: int
    total_allocation: Decimal


class SubsidyScoreResponse(BaseModel):
    subsidy_id: int
    risk_score: Decimal
    transparency_score: Decimal