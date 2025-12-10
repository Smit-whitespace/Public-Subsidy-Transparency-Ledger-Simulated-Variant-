"""
backend/services/disbursement_service.py

Disbursement service: transactional helpers to create, fetch, list, update, and delete disbursement records. Normalizes monetary inputs to Decimal.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

from backend.models.disbursement import Disbursement as DisbursementModel
from backend.schemas.disbursement import DisbursementCreate, DisbursementUpdate, Disbursement as DisbursementSchema


# Quantize currency amounts to 2 decimal places for consistent storage
DECIMAL_QUANTIZE = Decimal("0.01")


def normalize_amount(value: object) -> Decimal:
    """
    Convert and normalize monetary value to Decimal with 2 decimal places.
    
    Accepts string, float, or Decimal input and returns a properly quantized Decimal.
    Rejects negative or zero amounts.
    
    Args:
        value: Monetary amount as str, float, or Decimal
    
    Returns:
        Normalized Decimal with 2 decimal places
    
    Raises:
        ValueError: If value is invalid, not a number, or non-positive
    """
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Invalid amount value: {value}. Must be a valid number.")
    
    if decimal_value <= 0:
        raise ValueError(f"Amount must be positive, got: {decimal_value}")
    
    # Quantize to 2 decimal places using banker's rounding
    return decimal_value.quantize(DECIMAL_QUANTIZE, rounding=ROUND_HALF_UP)


def create_disbursement(db: Session, disb_in: DisbursementCreate, commit: bool = True) -> DisbursementModel:
    """
    Create and persist a new disbursement record.
    
    Args:
        db: SQLAlchemy session
        disb_in: Validated DisbursementCreate schema
        commit: Whether to commit immediately (default True)
    
    Returns:
        Created DisbursementModel instance
    
    Raises:
        RuntimeError: If database operation fails
    """
    try:
        # Normalize amount to Decimal with proper quantization
        normalized_amount = normalize_amount(disb_in.amount)
        
        # Create disbursement model with explicit field mapping
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
        
        return disbursement
        
    except ValueError:
        # Re-raise validation errors as-is
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError("DB error while creating disbursement")


def get_disbursement_by_id(db: Session, disbursement_id: int) -> Optional[DisbursementModel]:
    """
    Retrieve a single disbursement record by ID.
    
    Args:
        db: SQLAlchemy session
        disbursement_id: Primary key of disbursement record
    
    Returns:
        DisbursementModel if found, None otherwise
    """
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
    """
    List disbursement records with optional filters and pagination.
    
    Args:
        db: SQLAlchemy session
        subsidy_id: Filter by subsidy ID (optional)
        min_amount: Minimum amount filter as Decimal (optional)
        max_amount: Maximum amount filter as Decimal (optional)
        limit: Maximum number of records to return (must be >= 1)
        offset: Number of records to skip (must be >= 0)
    
    Returns:
        List of DisbursementModel instances
    
    Raises:
        ValueError: If limit or offset are invalid
        RuntimeError: If database operation fails
    """
    if limit < 1:
        raise ValueError(f"limit must be >= 1, got {limit}")
    if offset < 0:
        raise ValueError(f"offset must be >= 0, got {offset}")
    
    try:
        query = db.query(DisbursementModel)
        
        if subsidy_id is not None:
            query = query.filter(DisbursementModel.subsidy_id == subsidy_id)
        
        if min_amount is not None:
            # Accept Decimal directly; callers should normalize if needed
            query = query.filter(DisbursementModel.amount >= min_amount)
        
        if max_amount is not None:
            query = query.filter(DisbursementModel.amount <= max_amount)
        
        # Order by date descending (most recent first)
        query = query.order_by(DisbursementModel.date.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
        
    except SQLAlchemyError as e:
        raise RuntimeError("DB error while listing disbursements")


def update_disbursement(
    db: Session,
    disbursement_id: int,
    changes: DisbursementUpdate,
    commit: bool = True
) -> DisbursementModel:
    """
    Update an existing disbursement record with partial changes.
    
    Args:
        db: SQLAlchemy session
        disbursement_id: Primary key of disbursement to update
        changes: DisbursementUpdate schema with fields to update
        commit: Whether to commit immediately (default True)
    
    Returns:
        Updated DisbursementModel instance
    
    Raises:
        ValueError: If disbursement not found
        RuntimeError: If database operation fails
    """
    disbursement = get_disbursement_by_id(db, disbursement_id)
    if not disbursement:
        raise ValueError("Disbursement not found")
    
    try:
        update_data = changes.dict(exclude_unset=True)
        
        # Normalize amount if provided
        if "amount" in update_data and update_data["amount"] is not None:
            update_data["amount"] = normalize_amount(update_data["amount"])
        
        # Apply updates to model
        for field, value in update_data.items():
            setattr(disbursement, field, value)
        
        if commit:
            db.commit()
            db.refresh(disbursement)
        
        return disbursement
        
    except ValueError:
        # Re-raise validation errors as-is
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError("DB error while updating disbursement")


def delete_disbursement(db: Session, disbursement_id: int, commit: bool = True) -> None:
    """
    Delete a disbursement record.
    
    Note: This performs a hard delete. Production systems may prefer soft-delete
    (is_deleted flag) to maintain audit trail and referential integrity.
    
    Args:
        db: SQLAlchemy session
        disbursement_id: Primary key of disbursement to delete
        commit: Whether to commit immediately (default True)
    
    Raises:
        ValueError: If disbursement not found
        RuntimeError: If database operation fails
    """
    disbursement = get_disbursement_by_id(db, disbursement_id)
    if not disbursement:
        raise ValueError("Disbursement not found")
    
    try:
        db.delete(disbursement)
        
        if commit:
            db.commit()
            
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError("DB error while deleting disbursement")


def total_disbursed_for_subsidy(db: Session, subsidy_id: int) -> Decimal:
    """
    Calculate the total amount disbursed for a given subsidy.
    
    Args:
        db: SQLAlchemy session
        subsidy_id: ID of the subsidy to sum disbursements for
    
    Returns:
        Total amount as Decimal (quantized to 2 decimal places), or Decimal(0) if no disbursements
    """
    try:
        result = db.query(func.sum(DisbursementModel.amount)).filter(
            DisbursementModel.subsidy_id == subsidy_id
        ).scalar()
        
        if result is None:
            return Decimal("0.00")
        
        # Ensure result is Decimal and properly quantized
        total = Decimal(str(result))
        return total.quantize(DECIMAL_QUANTIZE, rounding=ROUND_HALF_UP)
        
    except SQLAlchemyError as e:
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

# Test hint: use in-memory sqlite Session, call create_disbursement(db, DisbursementCreate(...)), then assert total_disbursed_for_subsidy(db, subsidy_id) returns expected Decimal.