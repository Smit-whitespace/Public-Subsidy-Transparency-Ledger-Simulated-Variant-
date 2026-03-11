# backend/services/subsidy_service.py

from typing import List, Optional, Dict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_

from backend.models.subsidy import Subsidy as SubsidyModel
from backend.schemas.subsidy import SubsidyCreate, SubsidyUpdate
from backend.services.risk_engine import recalculate_subsidy_score


DECIMAL_QUANTIZE = Decimal("0.01")


# ==========================================================
# Utilities
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
# CREATE
# ==========================================================

def create_subsidy(
    db: Session,
    subsidy_in: SubsidyCreate,
    commit: bool = True
) -> SubsidyModel:

    try:
        normalized_allocation = normalize_amount(subsidy_in.total_allocation)

        subsidy = SubsidyModel(
            title=subsidy_in.title,
            recipient=subsidy_in.recipient,
            sector=subsidy_in.sector,
            total_allocation=normalized_allocation,
            currency=subsidy_in.currency,
            description=subsidy_in.description,
            meta_data=subsidy_in.meta_data,
            status=subsidy_in.status or "planned",
            is_active=subsidy_in.is_active if subsidy_in.is_active is not None else True,
            start_date=subsidy_in.start_date,
            end_date=subsidy_in.end_date,
        )

        db.add(subsidy)

        if commit:
            db.commit()
            db.refresh(subsidy)

            # 🔥 Immediately calculate baseline risk
            recalculate_subsidy_score(db, subsidy.id)

        return subsidy

    except ValueError:
        raise
    except SQLAlchemyError:
        db.rollback()
        raise RuntimeError("DB error while creating subsidy")


# ==========================================================
# READ
# ==========================================================

def get_subsidy_by_id(
    db: Session,
    subsidy_id: int
) -> Optional[SubsidyModel]:

    return db.query(SubsidyModel).filter_by(id=subsidy_id).first()


def list_subsidies(
    db: Session,
    *,
    q: Optional[str] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    is_active: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0
) -> List[SubsidyModel]:

    if limit < 1 or limit > 1000:
        raise ValueError("limit must be between 1 and 1000")

    if offset < 0:
        raise ValueError("offset must be >= 0")

    try:
        query = db.query(SubsidyModel)

        if q:
            term = f"%{q}%"
            query = query.filter(
                or_(
                    SubsidyModel.title.ilike(term),
                    SubsidyModel.recipient.ilike(term),
                    SubsidyModel.description.ilike(term)
                )
            )

        if min_amount is not None:
            query = query.filter(SubsidyModel.total_allocation >= min_amount)

        if max_amount is not None:
            query = query.filter(SubsidyModel.total_allocation <= max_amount)

        if is_active is not None:
            query = query.filter(SubsidyModel.is_active == is_active)

        return (
            query.order_by(SubsidyModel.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    except SQLAlchemyError:
        raise RuntimeError("DB error while listing subsidies")


# ==========================================================
# UPDATE
# ==========================================================

def update_subsidy(
    db: Session,
    subsidy_id: int,
    changes: SubsidyUpdate,
    commit: bool = True
) -> SubsidyModel:

    subsidy = get_subsidy_by_id(db, subsidy_id)

    if not subsidy:
        raise ValueError("Subsidy not found")

    try:
        update_data = changes.dict(exclude_unset=True)

        # Normalize total_allocation if present
        if "total_allocation" in update_data and update_data["total_allocation"] is not None:
            update_data["total_allocation"] = normalize_amount(update_data["total_allocation"])

        for field, value in update_data.items():
            setattr(subsidy, field, value)

        if commit:
            db.commit()
            db.refresh(subsidy)

            # 🔥 Critical: recalc risk after ANY meaningful subsidy change
            recalculate_subsidy_score(db, subsidy.id)

        return subsidy

    except ValueError:
        raise
    except SQLAlchemyError:
        db.rollback()
        raise RuntimeError("DB error while updating subsidy")


# ==========================================================
# DELETE
# ==========================================================

def delete_subsidy(
    db: Session,
    subsidy_id: int,
    commit: bool = True
) -> None:

    subsidy = get_subsidy_by_id(db, subsidy_id)

    if not subsidy:
        raise ValueError("Subsidy not found")

    try:
        db.delete(subsidy)

        if commit:
            db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise RuntimeError("DB error while deleting subsidy")

# ==========================================================
# FIND SUBSIDIES BY RECEPIENT
# ==========================================================
def find_subsidies_by_recipient(
    db,
    recipient: str,
    limit: int = 50,
    offset: int = 0,
):
    return (
        db.query(SubsidyModel)
        .filter(SubsidyModel.recipient.ilike(f"%{recipient}%"))
        .offset(offset)
        .limit(limit)
        .all()
    )

# ==========================================================
# FINANCIAL SUMMARY
# ==========================================================

def total_authorized_and_disbursed(
    db: Session,
    subsidy_id: int
) -> Dict[str, Decimal]:

    subsidy = get_subsidy_by_id(db, subsidy_id)

    if not subsidy:
        raise ValueError("Subsidy not found")

    try:
        from backend.models.disbursement import Disbursement as DisbursementModel

        authorized = subsidy.total_allocation

        disbursed_result = (
            db.query(func.sum(DisbursementModel.amount))
            .filter(DisbursementModel.subsidy_id == subsidy_id)
            .scalar()
        )

        disbursed = Decimal("0.00") if disbursed_result is None else Decimal(str(disbursed_result))
        remaining = authorized - disbursed

        return {
            "authorized": authorized.quantize(DECIMAL_QUANTIZE, rounding=ROUND_HALF_UP),
            "disbursed": disbursed.quantize(DECIMAL_QUANTIZE, rounding=ROUND_HALF_UP),
            "remaining": remaining.quantize(DECIMAL_QUANTIZE, rounding=ROUND_HALF_UP),
        }

    except SQLAlchemyError:
        raise RuntimeError("DB error while computing subsidy financial summary")