# backend/routes/disbursement_routes.py

from decimal import Decimal, InvalidOperation
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.disbursement import Disbursement as DisbursementModel
from backend.schemas.disbursement import Disbursement, DisbursementCreate, DisbursementUpdate
from backend.core.permission_guard import require_roles


router = APIRouter(tags=["disbursements"])


# ---------------------------------------------------------
# LIST (PUBLIC / AUTHENTICATED)
# ---------------------------------------------------------

@router.get("/", response_model=List[Disbursement])
def list_disbursements(
    subsidy_id: Optional[int] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):

    try:
        query = db.query(DisbursementModel)

        if subsidy_id is not None:
            query = query.filter(DisbursementModel.subsidy_id == subsidy_id)

        if min_amount is not None:
            query = query.filter(DisbursementModel.amount >= Decimal(str(min_amount)))

        if max_amount is not None:
            query = query.filter(DisbursementModel.amount <= Decimal(str(max_amount)))

        query = query.order_by(DisbursementModel.date.desc())
        query = query.offset(offset).limit(limit)

        return query.all()

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while fetching disbursements: {str(e)}"
        )


# ---------------------------------------------------------
# GET SINGLE
# ---------------------------------------------------------

@router.get("/{disbursement_id}", response_model=Disbursement)
def get_disbursement(
    disbursement_id: int,
    db: Session = Depends(get_db),
):

    disbursement = db.query(DisbursementModel).filter(
        DisbursementModel.id == disbursement_id
    ).first()

    if not disbursement:
        raise HTTPException(status_code=404, detail="Disbursement not found")

    return disbursement


# ---------------------------------------------------------
# CREATE (ADMIN ONLY)
# ---------------------------------------------------------

@router.post(
    "/",
    response_model=Disbursement,
    status_code=status.HTTP_201_CREATED
)
def create_disbursement(
    disbursement_data: DisbursementCreate,
    db: Session = Depends(get_db),
    user = Depends(require_roles("admin"))
):

    try:
        data = disbursement_data.dict()
        data["amount"] = Decimal(str(data["amount"]))

        disbursement = DisbursementModel(**data)

        db.add(disbursement)
        db.commit()
        db.refresh(disbursement)

        return disbursement

    except InvalidOperation:
        raise HTTPException(status_code=400, detail="Invalid amount format")

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error while creating disbursement: {str(e)}"
        )


# ---------------------------------------------------------
# UPDATE (ADMIN ONLY)
# ---------------------------------------------------------

@router.patch("/{disbursement_id}", response_model=Disbursement)
def update_disbursement(
    disbursement_id: int,
    disbursement_update: DisbursementUpdate,
    db: Session = Depends(get_db),
    user = Depends(require_roles("admin"))
):

    disbursement = db.query(DisbursementModel).filter(
        DisbursementModel.id == disbursement_id
    ).first()

    if not disbursement:
        raise HTTPException(status_code=404, detail="Disbursement not found")

    try:
        update_data = disbursement_update.dict(exclude_unset=True)

        if "amount" in update_data:
            update_data["amount"] = Decimal(str(update_data["amount"]))

        for field, value in update_data.items():
            setattr(disbursement, field, value)

        db.commit()
        db.refresh(disbursement)

        return disbursement

    except InvalidOperation:
        raise HTTPException(status_code=400, detail="Invalid amount format")

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error while updating disbursement: {str(e)}"
        )


# ---------------------------------------------------------
# DELETE (ADMIN ONLY)
# ---------------------------------------------------------

@router.delete("/{disbursement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_disbursement(
    disbursement_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_roles("admin"))
):

    disbursement = db.query(DisbursementModel).filter(
        DisbursementModel.id == disbursement_id
    ).first()

    if not disbursement:
        raise HTTPException(status_code=404, detail="Disbursement not found")

    try:
        db.delete(disbursement)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error while deleting disbursement: {str(e)}"
        )