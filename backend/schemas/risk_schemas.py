from decimal import Decimal
from typing import Dict
from pydantic import BaseModel


class RiskBreakdownResponse(BaseModel):
    subsidy_id: int
    risk_score: Decimal
    transparency_score: Decimal
    breakdown: Dict[str, Decimal]