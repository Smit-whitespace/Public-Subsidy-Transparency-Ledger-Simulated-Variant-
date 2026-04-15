from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    subsidy_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("subsidies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(String(100), index=True)

    severity: Mapped[str] = mapped_column(String(50))

    description: Mapped[str] = mapped_column(Text)

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )   