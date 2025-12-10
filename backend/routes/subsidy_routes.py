"""
backend/routes/subsidy_routes.py

FastAPI router for managing public subsidy records (CRUD + blockchain proof integration).
Provides endpoints for listing, creating, updating, deleting subsidies and publishing/reading proofs on-chain.
"""

from decimal import Decimal, InvalidOperation
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

try:
    from backend.dependencies import get_db
except ImportError:
    from backend.database.connection import get_db

from backend.models.subsidy import Subsidy

try:
    from backend.schemas.subsidy import Subsidy as SubsidySchema, SubsidyCreate, SubsidyUpdate
except ImportError:
    from pydantic import BaseModel, Field
    
    class SubsidySchema(BaseModel):
        id: int
        title: str
        recipient: str
        amount: Decimal
        currency: Optional[str] = "INR"
        description: Optional[str] = None
        metadata: Optional[str] = None
        start_date: Optional[datetime] = None
        end_date: Optional[datetime] = None
        is_active: bool = True
        proof_id: Optional[str] = None
        created_at: datetime
        updated_at: datetime
        
        class Config:
            from_attributes = True
            orm_mode = True
    
    class SubsidyCreate(BaseModel):
        title: str
        recipient: str
        amount: float | Decimal | str
        currency: Optional[str] = "INR"
        description: Optional[str] = None
        metadata: Optional[str] = None
        start_date: Optional[datetime] = None
        end_date: Optional[datetime] = None
    
    class SubsidyUpdate(BaseModel):
        title: Optional[str] = None
        recipient: Optional[str] = None
        amount: Optional[float | Decimal | str] = None
        currency: Optional[str] = None
        description: Optional[str] = None
        metadata: Optional[str] = None
        start_date: Optional[datetime] = None
        end_date: Optional[datetime] = None
        is_active: Optional[bool] = None

try:
    from backend.services import blockchain_service
    BLOCKCHAIN_AVAILABLE = True
except ImportError:
    BLOCKCHAIN_AVAILABLE = False

try:
    from backend.utils.hashing import sha256_of
except ImportError:
    import hashlib
    import json
    def sha256_of(data: dict) -> str:
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


router = APIRouter(prefix="/subsidies", tags=["subsidies"])


def safe_decimal(value) -> Decimal:
    """Convert numeric input to Decimal safely."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid numeric value: {value}"
        )


@router.get("/", response_model=List[SubsidySchema])
def list_subsidies(
    q: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List subsidies with optional filters.
    
    Query params:
    - q: Free-text search across title, recipient, description
    - min_amount / max_amount: Amount range filters
    - is_active: Filter by active status
    - limit / offset: Pagination
    
    Example:
    curl "http://localhost:8000/subsidies/?q=agriculture&min_amount=10000&limit=10"
    """
    query = db.query(Subsidy)
    
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                Subsidy.title.ilike(search_term),
                Subsidy.recipient.ilike(search_term),
                Subsidy.description.ilike(search_term)
            )
        )
    
    if min_amount is not None:
        min_decimal = safe_decimal(min_amount)
        query = query.filter(Subsidy.amount >= min_decimal)
    
    if max_amount is not None:
        max_decimal = safe_decimal(max_amount)
        query = query.filter(Subsidy.amount <= max_decimal)
    
    if is_active is not None:
        query = query.filter(Subsidy.is_active == is_active)
    
    query = query.order_by(Subsidy.created_at.desc())
    query = query.limit(limit).offset(offset)
    
    return query.all()


@router.get("/{subsidy_id}", response_model=SubsidySchema)
def get_subsidy(subsidy_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single subsidy by ID.
    """
    subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()
    if not subsidy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subsidy not found"
        )
    return subsidy


@router.post("/", response_model=SubsidySchema, status_code=status.HTTP_201_CREATED)
def create_subsidy(subsidy_data: SubsidyCreate, db: Session = Depends(get_db)):
    """
    Create a new subsidy record.
    
    Example:
    curl -X POST "http://localhost:8000/subsidies/" -H "Content-Type: application/json" \
         -d '{"title":"Farm Equipment Subsidy","recipient":"Farmer Co-op","amount":"50000.00","currency":"INR"}'
    """
    try:
        amount_decimal = safe_decimal(subsidy_data.amount)
        
        subsidy = Subsidy(
            title=subsidy_data.title,
            recipient=subsidy_data.recipient,
            amount=amount_decimal,
            currency=subsidy_data.currency or "INR",
            description=subsidy_data.description,
            metadata=subsidy_data.metadata,
            start_date=subsidy_data.start_date,
            end_date=subsidy_data.end_date
        )
        
        db.add(subsidy)
        db.commit()
        db.refresh(subsidy)
        
        # TODO: Emit event for downstream processing (e.g., Kafka topic: subsidy.created)
        # event_service.emit("subsidy.created", subsidy.id)
        
        return subsidy
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subsidy record"
        )


@router.patch("/{subsidy_id}", response_model=SubsidySchema)
def update_subsidy(
    subsidy_id: int,
    subsidy_data: SubsidyUpdate,
    db: Session = Depends(get_db)
):
    """
    Partially update a subsidy record.
    """
    subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()
    if not subsidy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subsidy not found"
        )
    
    try:
        update_data = subsidy_data.dict(exclude_unset=True)
        
        if "amount" in update_data:
            update_data["amount"] = safe_decimal(update_data["amount"])
        
        for field, value in update_data.items():
            setattr(subsidy, field, value)
        
        db.commit()
        db.refresh(subsidy)
        
        return subsidy
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subsidy record"
        )


@router.delete("/{subsidy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subsidy(subsidy_id: int, db: Session = Depends(get_db)):
    """
    Delete a subsidy record.
    
    Note: Consider implementing soft-delete (is_deleted flag) for production use.
    """
    subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()
    if not subsidy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subsidy not found"
        )
    
    try:
        db.delete(subsidy)
        db.commit()
        return None
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete subsidy record"
        )


@router.post("/{subsidy_id}/proof", status_code=status.HTTP_201_CREATED)
def create_subsidy_proof(subsidy_id: int, db: Session = Depends(get_db)):
    """
    Compute hash for subsidy record and publish proof to blockchain.
    
    Returns proof metadata including hash and blockchain transaction details.
    """
    subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()
    if not subsidy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subsidy not found"
        )
    
    try:
        canonical_data = {
            "id": subsidy.id,
            "title": subsidy.title,
            "recipient": subsidy.recipient,
            "amount": str(subsidy.amount),
            "currency": subsidy.currency,
            "created_at": subsidy.created_at.isoformat() if subsidy.created_at else None
        }
        
        hash_value = sha256_of(canonical_data)
        
        if BLOCKCHAIN_AVAILABLE:
            try:
                proof_result = blockchain_service.write_proof_to_chain(hash_value)
                
                if proof_result and "proof_id" in proof_result:
                    subsidy.proof_id = proof_result["proof_id"]
                    db.commit()
                    db.refresh(subsidy)
                
                return {
                    "subsidy_id": subsidy.id,
                    "hash": hash_value,
                    "tx_hash": proof_result.get("tx_hash"),
                    "proof_id": proof_result.get("proof_id"),
                    "on_chain": True
                }
            except Exception as bc_error:
                return {
                    "subsidy_id": subsidy.id,
                    "hash": hash_value,
                    "on_chain": False,
                    "error": "Blockchain service error"
                }
        else:
            return {
                "subsidy_id": subsidy.id,
                "hash": hash_value,
                "on_chain": False,
                "message": "Blockchain service not configured"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create proof"
        )


@router.get("/{subsidy_id}/proof")
def get_subsidy_proof(subsidy_id: int, db: Session = Depends(get_db)):
    """
    Retrieve blockchain proof metadata for a subsidy.
    """
    subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()
    if not subsidy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subsidy not found"
        )
    
    if not subsidy.proof_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No proof recorded for this subsidy"
        )
    
    if BLOCKCHAIN_AVAILABLE:
        try:
            proof_data = blockchain_service.read_proof_from_chain(subsidy.proof_id)
            return {
                "subsidy_id": subsidy.id,
                "proof_id": subsidy.proof_id,
                "proof_data": proof_data,
                "on_chain": True
            }
        except Exception as bc_error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve proof from blockchain"
            )
    else:
        return {
            "subsidy_id": subsidy.id,
            "proof_id": subsidy.proof_id,
            "on_chain": False,
            "message": "Blockchain service not configured"
        }