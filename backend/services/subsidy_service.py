"""
backend/services/subsidy_service.py

Subsidy service: transactional helpers to create, fetch, list, update, delete subsidies and compute financial summaries. Normalizes monetary inputs to Decimal.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_

from backend.models.subsidy import Subsidy as SubsidyModel
from backend.schemas.subsidy import SubsidyCreate, SubsidyUpdate, Subsidy as SubsidySchema


# Quantize monetary values to 2 decimal places using ROUND_HALF_UP
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


def create_subsidy(db: Session, subsidy_in: SubsidyCreate, commit: bool = True) -> SubsidyModel:
    """
    Create and persist a new subsidy record.
    
    Args:
        db: SQLAlchemy session
        subsidy_in: Validated SubsidyCreate schema
        commit: Whether to commit immediately (default True)
    
    Returns:
        Created SubsidyModel instance
    
    Raises:
        RuntimeError: If database operation fails
    """
    try:
        # Normalize amount to Decimal with proper quantization
        normalized_amount = normalize_amount(subsidy_in.amount)
        
        # Create subsidy model with explicit field mapping
        subsidy = SubsidyModel(
            title=subsidy_in.title,
            recipient=subsidy_in.recipient,
            amount=normalized_amount,
            currency=subsidy_in.currency,
            description=subsidy_in.description,
            metadata=subsidy_in.metadata,
            is_active=subsidy_in.is_active if subsidy_in.is_active is not None else True,
            proof_id=subsidy_in.proof_id,
            start_date=subsidy_in.start_date,
            end_date=subsidy_in.end_date
        )
        
        db.add(subsidy)
        
        if commit:
            db.commit()
            db.refresh(subsidy)
            
            # TODO: Publish event to message queue (e.g., Kafka)
            # from backend.services.event_service import publish_event
            # publish_event("subsidy.created", {"id": subsidy.id, "recipient": subsidy.recipient})
            
            # TODO: Index subsidy in search engine (e.g., ElasticSearch)
            # from backend.services.search_indexer import index_subsidy
            # index_subsidy(subsidy)
            
            # TODO: Optional blockchain proof writing for high-value subsidies
            # from backend.services.blockchain_service import write_proof_to_chain
            # from backend.utils.hashing import sha256_of
            # if subsidy.amount > Decimal("1000000"):
            #     proof_hash = sha256_of({"id": subsidy.id, "amount": str(subsidy.amount)})
            #     write_proof_to_chain(proof_hash)
        
        return subsidy
        
    except ValueError:
        # Re-raise validation errors as-is
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError("DB error while creating subsidy")


def get_subsidy_by_id(db: Session, subsidy_id: int) -> Optional[SubsidyModel]:
    """
    Retrieve a single subsidy record by ID.
    
    Args:
        db: SQLAlchemy session
        subsidy_id: Primary key of subsidy record
    
    Returns:
        SubsidyModel if found, None otherwise
    """
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
    """
    List subsidy records with optional filters and pagination.
    
    Args:
        db: SQLAlchemy session
        q: Free-text search query (searches title, recipient, description)
        min_amount: Minimum amount filter as Decimal (optional)
        max_amount: Maximum amount filter as Decimal (optional)
        is_active: Filter by active status (optional)
        limit: Maximum number of records to return (must be >= 1 and <= 1000)
        offset: Number of records to skip (must be >= 0)
    
    Returns:
        List of SubsidyModel instances
    
    Raises:
        ValueError: If limit or offset are invalid
        RuntimeError: If database operation fails
    """
    if limit < 1 or limit > 1000:
        raise ValueError(f"limit must be >= 1 and <= 1000, got {limit}")
    if offset < 0:
        raise ValueError(f"offset must be >= 0, got {offset}")
    
    try:
        query = db.query(SubsidyModel)
        
        # Apply text search filter
        if q:
            search_term = f"%{q}%"
            query = query.filter(
                or_(
                    SubsidyModel.title.ilike(search_term),
                    SubsidyModel.recipient.ilike(search_term),
                    SubsidyModel.description.ilike(search_term)
                )
            )
        
        # Apply amount range filters
        if min_amount is not None:
            query = query.filter(SubsidyModel.amount >= min_amount)
        
        if max_amount is not None:
            query = query.filter(SubsidyModel.amount <= max_amount)
        
        # Apply active status filter
        if is_active is not None:
            query = query.filter(SubsidyModel.is_active == is_active)
        
        # Order by created_at descending (most recent first)
        query = query.order_by(SubsidyModel.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
        
    except SQLAlchemyError as e:
        raise RuntimeError("DB error while listing subsidies")


def update_subsidy(
    db: Session,
    subsidy_id: int,
    changes: SubsidyUpdate,
    commit: bool = True
) -> SubsidyModel:
    """
    Update an existing subsidy record with partial changes.
    
    Args:
        db: SQLAlchemy session
        subsidy_id: Primary key of subsidy to update
        changes: SubsidyUpdate schema with fields to update
        commit: Whether to commit immediately (default True)
    
    Returns:
        Updated SubsidyModel instance
    
    Raises:
        ValueError: If subsidy not found
        RuntimeError: If database operation fails
    """
    subsidy = get_subsidy_by_id(db, subsidy_id)
    if not subsidy:
        raise ValueError("Subsidy not found")
    
    try:
        update_data = changes.dict(exclude_unset=True)
        
        # Normalize amount if provided
        if "amount" in update_data and update_data["amount"] is not None:
            update_data["amount"] = normalize_amount(update_data["amount"])
        
        # Apply updates to model
        for field, value in update_data.items():
            setattr(subsidy, field, value)
        
        if commit:
            db.commit()
            db.refresh(subsidy)
        
        return subsidy
        
    except ValueError:
        # Re-raise validation errors as-is
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError("DB error while updating subsidy")


def delete_subsidy(db: Session, subsidy_id: int, commit: bool = True) -> None:
    """
    Delete a subsidy record.
    
    Note: This performs a hard delete. Production systems may prefer soft-delete
    (is_deleted flag) to maintain audit trail and referential integrity.
    
    Args:
        db: SQLAlchemy session
        subsidy_id: Primary key of subsidy to delete
        commit: Whether to commit immediately (default True)
    
    Raises:
        ValueError: If subsidy not found
        RuntimeError: If database operation fails
    """
    subsidy = get_subsidy_by_id(db, subsidy_id)
    if not subsidy:
        raise ValueError("Subsidy not found")
    
    try:
        db.delete(subsidy)
        
        if commit:
            db.commit()
            
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError("DB error while deleting subsidy")


def total_authorized_and_disbursed(db: Session, subsidy_id: int) -> Dict[str, Decimal]:
    """
    Calculate authorized, disbursed, and remaining amounts for a subsidy.
    
    Args:
        db: SQLAlchemy session
        subsidy_id: ID of the subsidy
    
    Returns:
        Dict with keys:
        - authorized: total subsidy amount
        - disbursed: sum of disbursements
        - remaining: authorized minus disbursed
    
    Raises:
        ValueError: If subsidy not found
    """
    subsidy = get_subsidy_by_id(db, subsidy_id)
    if not subsidy:
        raise ValueError("Subsidy not found")
    
    try:
        authorized = subsidy.amount
        
        # Import Disbursement model locally to avoid circular dependencies
        from backend.models.disbursement import Disbursement as DisbursementModel
        
        # Calculate total disbursed amount
        disbursed_result = db.query(func.sum(DisbursementModel.amount)).filter(
            DisbursementModel.subsidy_id == subsidy_id
        ).scalar()
        
        disbursed = Decimal("0.00") if disbursed_result is None else Decimal(str(disbursed_result))
        
        # Calculate remaining amount
        remaining = authorized - disbursed
        
        # Quantize all values to 2 decimal places
        return {
            "authorized": authorized.quantize(DECIMAL_QUANTIZE, rounding=ROUND_HALF_UP),
            "disbursed": disbursed.quantize(DECIMAL_QUANTIZE, rounding=ROUND_HALF_UP),
            "remaining": remaining.quantize(DECIMAL_QUANTIZE, rounding=ROUND_HALF_UP)
        }
        
    except SQLAlchemyError as e:
        raise RuntimeError("DB error while computing subsidy financial summary")


def find_subsidies_by_recipient(db: Session, recipient: str, limit: int = 50, offset: int = 0) -> List[SubsidyModel]:
    """
    Find subsidies by recipient name (case-insensitive match).
    
    Args:
        db: SQLAlchemy session
        recipient: Recipient name to search for
        limit: Maximum number of records to return (must be >= 1 and <= 1000)
        offset: Number of records to skip (must be >= 0)
    
    Returns:
        List of SubsidyModel instances
    
    Raises:
        ValueError: If limit or offset are invalid
    """
    if limit < 1 or limit > 1000:
        raise ValueError(f"limit must be >= 1 and <= 1000, got {limit}")
    if offset < 0:
        raise ValueError(f"offset must be >= 0, got {offset}")
    
    try:
        search_pattern = f"%{recipient}%"
        query = db.query(SubsidyModel).filter(
            SubsidyModel.recipient.ilike(search_pattern)
        )
        
        query = query.order_by(SubsidyModel.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
        
    except SQLAlchemyError as e:
        raise RuntimeError("DB error while finding subsidies by recipient")


__all__ = [
    "normalize_amount",
    "create_subsidy",
    "get_subsidy_by_id",
    "list_subsidies",
    "update_subsidy",
    "delete_subsidy",
    "total_authorized_and_disbursed",
    "find_subsidies_by_recipient"
]

# Test hint: use an in-memory sqlite Session, call create_subsidy(db, SubsidyCreate(...)), then assert total_authorized_and_disbursed returns expected Decimals and list_subsidies returns created record.