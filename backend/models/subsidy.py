from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
import enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class SubsidyStatus(str, enum.Enum):
    planned = "planned"
    active = "active"
    completed = "completed"
    expired = "expired"
    suspended = "suspended"


class Subsidy(Base):
    __tablename__ = "subsidies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    recipient: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    sector: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    total_allocation: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")

    description: Mapped[Optional[str]] = mapped_column(Text)

    meta_data: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[SubsidyStatus] = mapped_column(
        Enum(SubsidyStatus),
        default=SubsidyStatus.planned,
        nullable=False,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )

    transparency_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("100.00"), nullable=False
    )

    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "recipient": self.recipient,
            "sector": self.sector,
            "total_allocation": self.total_allocation,
            "currency": self.currency,
            "description": self.description,
            "meta_data": self.meta_data,
            "status": self.status.value if hasattr(self.status, 'value') else str(self.status),
            "is_active": self.is_active,
            "is_flagged": self.is_flagged,
            "risk_score": self.risk_score,
            "transparency_score": self.transparency_score,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


Index("ix_sector_status", Subsidy.sector, Subsidy.status)