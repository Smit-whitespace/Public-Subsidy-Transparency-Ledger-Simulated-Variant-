# backend/services/disbursement_service.py

from typing import List, Optional
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

from backend.models.disbursement import Disbursement as DisbursementModel
from backend.models.subsidy import Subsidy as SubsidyModel

from backend.schemas.disbursement import DisbursementCreate, DisbursementUpdate

from backend.services.risk_engine import recalculate_subsidy_score
from backend.services.risk_event_service import create_risk_event


DECIMAL_QUANTIZE = Decimal("0.01")


# ==========================================================
# AMOUNT NORMALIZATION
# ==========================================================

def normalize_amount(value: object) -> Decimal:

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Invalid amount value: {value}")

    if decimal_value <= 0:
        raise ValueError("Amount must be positive")

    return decimal_value.quantize(DECIMAL_QUANTIZE, rounding=ROUND_HALF_UP)


# ==========================================================
# ANOMALY DETECTION ENGINE
# ==========================================================

def detect_disbursement_anomalies(
    db: Session,
    subsidy_id: int,
    amount: Decimal
) -> None:
    """
    Basic anomaly detection rules for disbursements.

    Rules:
    1. Disbursement > 40% of subsidy allocation
    2. More than 3 disbursements within 24 hours
    3. Disbursement amount > 2x historical average
    """

    subsidy = db.query(SubsidyModel).filter_by(id=subsidy_id).first()

    if not subsidy:
        return

    # -----------------------------------------
    # Rule 1: Large allocation percentage
    # -----------------------------------------

    if subsidy.total_allocation and subsidy.total_allocation > 0:

        ratio = amount / subsidy.total_allocation

        if ratio > Decimal("0.40"):

            create_risk_event(
                db=db,
                subsidy_id=subsidy_id,
                event_type="large_disbursement",
                severity="medium",
                description="Disbursement exceeds 40% of subsidy allocation"
            )

    # -----------------------------------------
    # Rule 2: Rapid disbursements
    # -----------------------------------------

    window_start = datetime.utcnow() - timedelta(hours=24)

    count_recent = (
        db.query(func.count(DisbursementModel.id))
        .filter(
            DisbursementModel.subsidy_id == subsidy_id,
            DisbursementModel.date >= window_start
        )
        .scalar()
    )

    if count_recent and count_recent >= 3:

        create_risk_event(
            db=db,
            subsidy_id=subsidy_id,
            event_type="rapid_disbursements",
            severity="medium",
            description="Multiple disbursements detected within 24 hours"
        )

    # -----------------------------------------
    # Rule 3: Amount spike
    # -----------------------------------------

    avg_amount = (
        db.query(func.avg(DisbursementModel.amount))
        .filter(DisbursementModel.subsidy_id == subsidy_id)
        .scalar()
    )

    if avg_amount:

        avg_decimal = Decimal(str(avg_amount))

        if amount > avg_decimal * Decimal("2"):

            create_risk_event(
                db=db,
                subsidy_id=subsidy_id,
                event_type="amount_spike",
                severity="high",
                description="Disbursement significantly exceeds historical average"
            )


# ==========================================================
# CREATE
# ==========================================================

def create_disbursement(
    db: Session,
    disb_in: DisbursementCreate,
    commit: bool = True
) -> DisbursementModel:

    try:

        normalized_amount = normalize_amount(disb_in.amount)

        disbursement = DisbursementModel(
            subsidy_id=disb_in.subsidy_id,
            amount=normalized_amount,
            currency=disb_in.currency,
            reference=disb_in.reference,
            date=disb_in.date,
            notes=disb_in.notes
        )

        db.add(disbursement)

        if commit:

            db.commit()
            db.refresh(disbursement)

            # ---------------------------------
            # Run anomaly detection
            # ---------------------------------

            detect_disbursement_anomalies(
                db,
                disbursement.subsidy_id,
                normalized_amount
            )

            # ---------------------------------
            # Recalculate risk score
            # ---------------------------------

            recalculate_subsidy_score(db, disbursement.subsidy_id)

        return disbursement

    except ValueError:
        raise

    except SQLAlchemyError:
        db.rollback()
        raise RuntimeError("DB error while creating disbursement")


# ==========================================================
# READ
# ==========================================================

def get_disbursement_by_id(
    db: Session,
    disbursement_id: int
) -> Optional[DisbursementModel]:

    return db.query(DisbursementModel).filter_by(id=disbursement_id).first()


def list_disbursements(
    db: Session,
    *,
    subsidy_id: Optional[int] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    limit: int = 50,
    offset: int = 0
) -> List[DisbursementModel]:

    if limit < 1:
        raise ValueError("limit must be >= 1")

    if offset < 0:
        raise ValueError("offset must be >= 0")

    try:

        query = db.query(DisbursementModel)

        if subsidy_id is not None:
            query = query.filter(DisbursementModel.subsidy_id == subsidy_id)

        if min_amount is not None:
            query = query.filter(DisbursementModel.amount >= min_amount)

        if max_amount is not None:
            query = query.filter(DisbursementModel.amount <= max_amount)

        return (
            query.order_by(DisbursementModel.date.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    except SQLAlchemyError:
        raise RuntimeError("DB error while listing disbursements")


# ==========================================================
# UPDATE
# ==========================================================

def update_disbursement(
    db: Session,
    disbursement_id: int,
    changes: DisbursementUpdate,
    commit: bool = True
) -> DisbursementModel:

    disbursement = get_disbursement_by_id(db, disbursement_id)

    if not disbursement:
        raise ValueError("Disbursement not found")

    try:

        update_data = changes.dict(exclude_unset=True)

        if "amount" in update_data and update_data["amount"] is not None:
            update_data["amount"] = normalize_amount(update_data["amount"])

        for field, value in update_data.items():
            setattr(disbursement, field, value)

        if commit:

            db.commit()
            db.refresh(disbursement)

            recalculate_subsidy_score(db, disbursement.subsidy_id)

        return disbursement

    except ValueError:
        raise

    except SQLAlchemyError:
        db.rollback()
        raise RuntimeError("DB error while updating disbursement")


# ==========================================================
# DELETE
# ==========================================================

def delete_disbursement(
    db: Session,
    disbursement_id: int,
    commit: bool = True
) -> None:

    disbursement = get_disbursement_by_id(db, disbursement_id)

    if not disbursement:
        raise ValueError("Disbursement not found")

    subsidy_id = disbursement.subsidy_id

    try:

        db.delete(disbursement)

        if commit:

            db.commit()

            recalculate_subsidy_score(db, subsidy_id)

    except SQLAlchemyError:
        db.rollback()
        raise RuntimeError("DB error while deleting disbursement")


# ==========================================================
# AGGREGATION
# ==========================================================

def total_disbursed_for_subsidy(
    db: Session,
    subsidy_id: int
) -> Decimal:

    try:

        result = (
            db.query(func.sum(DisbursementModel.amount))
            .filter(DisbursementModel.subsidy_id == subsidy_id)
            .scalar()
        )

        if result is None:
            return Decimal("0.00")

        total = Decimal(str(result))

        return total.quantize(
            DECIMAL_QUANTIZE,
            rounding=ROUND_HALF_UP
        )

    except SQLAlchemyError:
        raise RuntimeError("DB error while computing total disbursed")


__all__ = [
    "normalize_amount",
    "create_disbursement",
    "get_disbursement_by_id",
    "list_disbursements",
    "update_disbursement",
    "delete_disbursement",
    "total_disbursed_for_subsidy"
]