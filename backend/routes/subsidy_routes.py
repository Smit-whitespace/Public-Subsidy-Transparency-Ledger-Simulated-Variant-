"""
backend/routes/subsidy_routes.py

FastAPI router for managing public subsidy records (CRUD + blockchain proof integration).
Provides endpoints for listing, creating, updating, deleting subsidies and publishing/reading proofs on-chain.
"""

from decimal import Decimal, InvalidOperation
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.core.permission_guard import require_roles

try:
    from backend.dependencies import get_db
except ImportError:
    from backend.database.connection import get_db

from backend.models.subsidy import Subsidy

try:
    from backend.schemas.subsidy import Subsidy as SubsidySchema, SubsidyCreate, SubsidyUpdate
except ImportError:
    from pydantic import BaseModel

    class SubsidySchema(BaseModel):
        id: int
        title: str
        recipient: str
        amount: Decimal
        currency: Optional[str] = "INR"
        description: Optional[str] = None
        meta_data: Optional[str] = None
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
        meta_data: Optional[str] = None
        start_date: Optional[datetime] = None
        end_date: Optional[datetime] = None

    class SubsidyUpdate(BaseModel):
        title: Optional[str] = None
        recipient: Optional[str] = None
        amount: Optional[float | Decimal | str] = None
        currency: Optional[str] = None
        description: Optional[str] = None
        meta_data: Optional[str] = None
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


router = APIRouter(tags=["subsidies"])


def safe_decimal(value) -> Decimal:
    """Convert numeric input to Decimal safely."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid numeric value: {value}"
        )


# ---------------------------------------------------------
# LIST
# ---------------------------------------------------------

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

    query = db.query(Subsidy)

    if q:
        term = f"%{q}%"
        query = query.filter(
            or_(
                Subsidy.title.ilike(term),
                Subsidy.recipient.ilike(term),
                Subsidy.description.ilike(term)
            )
        )

    if min_amount is not None:
        query = query.filter(Subsidy.total_allocation >= safe_decimal(min_amount))

    if max_amount is not None:
        query = query.filter(Subsidy.total_allocation <= safe_decimal(max_amount))

    if is_active is not None:
        query = query.filter(Subsidy.is_active == is_active)

    return (
        query.order_by(Subsidy.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


# ---------------------------------------------------------
# GET SINGLE
# ---------------------------------------------------------

@router.get("/{subsidy_id}", response_model=SubsidySchema)
def get_subsidy(subsidy_id: int, db: Session = Depends(get_db)):

    subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()

    if not subsidy:
        raise HTTPException(status_code=404, detail="Subsidy not found")

    return subsidy


# ---------------------------------------------------------
# CREATE (ADMIN ONLY)
# ---------------------------------------------------------

@router.post(
    "/",
    response_model=SubsidySchema,
    status_code=status.HTTP_201_CREATED
)
def create_subsidy(
    subsidy_data: SubsidyCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("admin"))
):

    try:
        subsidy = Subsidy(
            title=subsidy_data.title,
            recipient=subsidy_data.recipient,
            sector=subsidy_data.sector,
            total_allocation=safe_decimal(subsidy_data.total_allocation),
            currency=subsidy_data.currency or "INR",
            description=subsidy_data.description,
            meta_data=subsidy_data.meta_data,
            status=subsidy_data.status or "active",
            is_active=subsidy_data.is_active if subsidy_data.is_active is not None else True,
            start_date=subsidy_data.start_date,
            end_date=subsidy_data.end_date
        )

        db.add(subsidy)
        db.commit()
        db.refresh(subsidy)

        return subsidy

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
# ---------------------------------------------------------
# UPDATE (ADMIN ONLY)
# ---------------------------------------------------------

@router.patch("/{subsidy_id}", response_model=SubsidySchema)
def update_subsidy(
    subsidy_id: int,
    subsidy_data: SubsidyUpdate,
    db: Session = Depends(get_db),
    user = Depends(require_roles("admin"))
):

    subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()

    if not subsidy:
        raise HTTPException(status_code=404, detail="Subsidy not found")

    try:
        updates = subsidy_data.dict(exclude_unset=True)

        if "amount" in updates:
            updates["amount"] = safe_decimal(updates["amount"])

        for field, value in updates.items():
            setattr(subsidy, field, value)

        db.commit()
        db.refresh(subsidy)

        return subsidy

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update subsidy")


# ---------------------------------------------------------
# DELETE (ADMIN ONLY)
# ---------------------------------------------------------

@router.delete("/{subsidy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subsidy(
    subsidy_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_roles("admin"))
):

    subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()

    if not subsidy:
        raise HTTPException(status_code=404, detail="Subsidy not found")

    try:
        db.delete(subsidy)
        db.commit()
        return None

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete subsidy")


# ---------------------------------------------------------
# CREATE BLOCKCHAIN PROOF (ADMIN ONLY)
# ---------------------------------------------------------

@router.post("/{subsidy_id}/proof", status_code=status.HTTP_201_CREATED)
def create_subsidy_proof(
    subsidy_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_roles("admin"))
):

    subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()

    if not subsidy:
        raise HTTPException(status_code=404, detail="Subsidy not found")

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
            result = blockchain_service.write_proof_to_chain(hash_value)

            if result and "proof_id" in result:
                subsidy.proof_id = result["proof_id"]
                db.commit()

            return {
                "subsidy_id": subsidy.id,
                "hash": hash_value,
                "tx_hash": result.get("tx_hash"),
                "proof_id": result.get("proof_id"),
                "on_chain": True
            }

        except Exception:
            return {
                "subsidy_id": subsidy.id,
                "hash": hash_value,
                "on_chain": False,
                "error": "Blockchain service error"
            }

    return {
        "subsidy_id": subsidy.id,
        "hash": hash_value,
        "on_chain": False,
        "message": "Blockchain service not configured"
    }


# ---------------------------------------------------------
# GET PROOF
# ---------------------------------------------------------

@router.get("/{subsidy_id}/proof")
def get_subsidy_proof(
    subsidy_id: int,
    db: Session = Depends(get_db)
):

    subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()

    if not subsidy:
        raise HTTPException(status_code=404, detail="Subsidy not found")

    if not subsidy.proof_id:
        raise HTTPException(status_code=404, detail="No proof recorded")

    if BLOCKCHAIN_AVAILABLE:
        proof = blockchain_service.read_proof_from_chain(subsidy.proof_id)

        return {
            "subsidy_id": subsidy.id,
            "proof_id": subsidy.proof_id,
            "proof_data": proof,
            "on_chain": True
        }

    return {
        "subsidy_id": subsidy.id,
        "proof_id": subsidy.proof_id,
        "on_chain": False,
        "message": "Blockchain service not configured"
    }