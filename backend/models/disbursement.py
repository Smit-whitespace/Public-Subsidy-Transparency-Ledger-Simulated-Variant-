"""
backend/models/disbursement.py

Defines the Disbursement model for tracking individual payment releases tied to subsidies.

Each disbursement record represents a single payment or fund transfer that was made as part
of a subsidy's lifecycle. A subsidy may have multiple disbursements over time (installments,
milestone payments, etc.), and this model captures the amount, timing, and reference details
for each one.

The model uses ondelete="SET NULL" on the subsidy foreign key to preserve audit trails even
if the parent subsidy is deleted from the system. This design choice prioritizes historical
data retention over strict referential integrity, which is common in financial applications
where you want to maintain records of all transactions indefinitely.

Schema changes should always be applied via Alembic migrations rather than using create_all
in production environments. This ensures proper version control and rollback capabilities for
your database schema evolution.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


__all__ = ["Disbursement"]


class Disbursement(Base):
    """
    Records individual payment/disbursement transactions for subsidies.
    
    This model captures the financial details of actual payments made to beneficiaries or
    recipients as part of subsidy programs. Each disbursement is linked to a parent subsidy
    via subsidy_id, but the foreign key uses ondelete="SET NULL" to ensure that disbursement
    records remain queryable even if the parent subsidy is removed (soft-deleted or purged).
    
    Why Numeric instead of Float for amounts:
    Financial calculations require exact decimal precision to avoid rounding errors that can
    accumulate over many transactions. The Numeric type with Decimal in Python ensures that
    amounts like 10.25 are stored and computed exactly as 10.25, not as a floating-point
    approximation like 10.249999999. This is critical for compliance, auditing, and avoiding
    penny discrepancies in financial reporting.
    
    Example usage in the REPL:
        disbursement = Disbursement(subsidy_id=1, amount=Decimal("5000.00"), currency="INR")
    """
    
    __tablename__ = "disbursements"
    
    # Primary key for this disbursement record. The index is implicit on primary keys but
    # we include it explicitly in the documentation for clarity about query performance.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Foreign key to the parent subsidy. We use ondelete="SET NULL" so that if the subsidy
    # is deleted, this disbursement record remains in the database with a null subsidy_id
    # rather than being cascade-deleted. This preserves the historical audit trail of all
    # payments that were actually made, even if the subsidy program is later discontinued.
    # The index accelerates queries like "find all disbursements for subsidy #42".
    subsidy_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("subsidies.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # The monetary amount of this disbursement. We use Numeric(18, 2) to store amounts with
    # up to 18 total digits and 2 decimal places, which is standard for most currency values.
    # This gives us a range from -9,999,999,999,999,999.99 to +9,999,999,999,999,999.99,
    # which is more than sufficient for individual disbursement amounts. Using Decimal in
    # Python code (rather than float) ensures we never lose precision in calculations.
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False
    )
    
    # ISO 4217 three-letter currency code (e.g., "INR", "USD", "EUR"). We default to "INR"
    # since this project appears to focus on Indian subsidies, but the field can be changed
    # if disbursements occur in other currencies. The String(3) constraint matches the ISO
    # standard length for currency codes.
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR"
    )
    
    # External reference or transaction ID from payment gateways, banking systems, or other
    # financial platforms. This helps reconcile disbursements with external records and is
    # nullable because not all disbursements may have an external reference at creation time.
    reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    
    # Timestamp of when this disbursement was executed or recorded in the system. The
    # server_default ensures the database sets this automatically on INSERT, providing a
    # reliable audit timestamp that doesn't depend on application code. We index this field
    # because disbursements are often queried by date range (e.g., "all payments in Q3 2024").
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Free-form text field for storing additional context about this disbursement. This might
    # include approval notes, beneficiary information, payment method details, or reasons for
    # any special handling. Using String with a generous length limit keeps the field indexable
    # if needed, while still accommodating substantial notes.
    notes: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )
    
    def amount_as_decimal(self) -> Decimal:
        """
        Return the disbursement amount as a Python Decimal object.
        
        This convenience method ensures you always get a proper Decimal instance for the
        amount field, which is important when performing financial calculations that require
        exact precision. While SQLAlchemy already returns Decimal for Numeric columns, this
        method makes the type guarantee explicit in your business logic code.
        
        Returns:
            The disbursement amount as a Decimal, suitable for exact arithmetic operations.
        """
        # The amount column is already stored as Decimal by SQLAlchemy, but we make this
        # explicit with a helper method to signal to other developers that this value should
        # always be treated as Decimal (never float) in calculations.
        return Decimal(str(self.amount))
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this disbursement record to a JSON-serializable dictionary.
        
        This method transforms the ORM model into a plain Python dict suitable for API
        responses or logging. Special handling is applied to Decimal and datetime fields
        which aren't natively JSON-serializable in Python's standard library.
        
        The amount field is converted to a string to prevent JSON serialization issues and
        to ensure exact decimal representation in the output (e.g., "5000.00" rather than
        5000.0 which could lose trailing zeros). The date field is converted to ISO 8601
        format which is widely supported and human-readable.
        
        Returns:
            A dictionary containing all disbursement fields in JSON-compatible formats.
        """
        return {
            "id": self.id,
            "subsidy_id": self.subsidy_id,
            # Convert Decimal to string to preserve exact decimal precision in JSON output
            # and avoid issues with JavaScript's number type which uses float representation
            "amount": str(self.amount),
            "currency": self.currency,
            "reference": self.reference,
            # Convert datetime to ISO 8601 string format for standardized representation
            # across different systems and time zones
            "date": self.date.isoformat() if self.date else None,
            "notes": self.notes,
        }