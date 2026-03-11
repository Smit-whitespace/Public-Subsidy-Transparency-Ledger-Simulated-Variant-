"""
backend/routes/auth_routes.py
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.database.connection import get_db
from backend.models.user import User
from backend.models.audit import AuditRecord
from backend.schemas.auth import Token
from backend.schemas.user import UserRead, UserCreate
from backend.services.auth_service import get_password_hash, verify_password
from backend.utils.jwt import create_token, decode_token

router = APIRouter(tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ==========================================================
# 🔐 CURRENT USER DEPENDENCY
# ==========================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        user_id: Optional[int] = payload.get("user_id")

        if user_id is None:
            raise credentials_exception

    except Exception:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    return user


# ==========================================================
# 🧾 REGISTER
# ==========================================================

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):

    # Explicit uniqueness check
    existing_user = (
        db.query(User)
        .filter(User.username == user_data.username)
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=400,
            detail="Username conflict",
        )

    try:
        new_user = User(
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Audit registration
        db.add(
            AuditRecord(
                entity="user",
                entity_id=new_user.id,
                action="register",
                details=f"User {new_user.username} registered",
            )
        )
        db.commit()

        return new_user

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error during registration",
        )


# ==========================================================
# 🔑 LOGIN
# ==========================================================

@router.post("/login", response_model=Token)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    user = (
        db.query(User)
        .filter(User.username == form_data.username)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )

    token_payload = {
        "user_id": user.id,
        "username": user.username,
    }

    access_token = create_token(token_payload)

    # Audit login
    db.add(
        AuditRecord(
            entity="user",
            entity_id=user.id,
            action="login",
            details=f"User {user.username} logged in",
        )
    )
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# ==========================================================
# 👤 CURRENT USER
# ==========================================================

@router.get("/me", response_model=UserRead)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user