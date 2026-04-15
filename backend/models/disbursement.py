from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class Disbursement(Base):
    __tablename__ = "disbursements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    subsidy_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("subsidies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    currency: Mapped[str] = mapped_column(String(3), default="INR")

    reference: Mapped[Optional[str]] = mapped_column(String(255))

    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    approval_status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True
    )

    approved_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    proof_document_url: Mapped[Optional[str]] = mapped_column(String(500))

    is_late: Mapped[bool] = mapped_column(Boolean, default=False)

    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    notes: Mapped[Optional[str]] = mapped_column(String(1000))

    def to_dict(self):
        return {
            "id": self.id,
            "subsidy_id": self.subsidy_id,
            "amount": self.amount,
            "currency": self.currency,
            "reference": self.reference,
            "date": self.date.isoformat() if self.date else None,
            "approval_status": self.approval_status,
            "approved_by": self.approved_by,
            "proof_document_url": self.proof_document_url,
            "is_late": self.is_late,
            "is_suspicious": self.is_suspicious,
            "notes": self.notes,
        }