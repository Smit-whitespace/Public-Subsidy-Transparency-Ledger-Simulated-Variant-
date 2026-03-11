from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class ScoringHistory(Base):
    __tablename__ = "scoring_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    subsidy_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("subsidies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    transparency_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )