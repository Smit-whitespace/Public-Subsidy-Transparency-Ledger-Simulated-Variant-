"""
backend/dependencies.py

FastAPI dependency helpers: DB session, auth helpers (current user), pagination, and settings accessor.
"""

from typing import Generator, Optional, Tuple
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseSettings

from backend.database.connection import get_db, engine
from backend.config import settings
from backend.services.auth_service import get_user_by_username
from backend.schemas.user import UserRead


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db_session() -> Generator[Session, None, None]:
    """
    Primary database session dependency for route handlers.
    
    Yields a SQLAlchemy Session and ensures proper cleanup.
    Automatically rolls back on exceptions and closes the session.
    
    Yields:
        SQLAlchemy Session instance
    """
    db = None
    try:
        # Get session from connection module
        db_generator = get_db()
        db = next(db_generator)
        yield db
    except SQLAlchemyError as e:
        # Rollback on database errors
        if db:
            db.rollback()
        raise
    except Exception as e:
        # Rollback on any other exceptions
        if db:
            db.rollback()
        raise
    finally:
        # Ensure session is closed
        if db:
            try:
                db.close()
            except Exception:
                pass


def get_settings() -> BaseSettings:
    """
    Settings dependency for routes.
    
    Returns the application settings object. Useful for avoiding
    circular imports in some modules and making settings injectable.
    
    Returns:
        Application settings instance
    """
    return settings


def pagination_params(limit: int = 50, offset: int = 0) -> Tuple[int, int]:
    """
    Pagination parameters dependency with validation.
    
    Validates limit and offset parameters for list endpoints.
    
    Args:
        limit: Maximum number of items to return (1-1000)
        offset: Number of items to skip (>= 0)
    
    Returns:
        Tuple of (limit, offset)
    
    Raises:
        HTTPException: If parameters are invalid
    
    # use as: limit, offset = Depends(pagination_params)
    """
    # Validate limit range
    if limit < 1 or limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 1000"
        )
    
    # Validate offset
    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail="offset must be >= 0"
        )
    
    return (limit, offset)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db_session)
) -> UserRead:
    """
    Get current authenticated user from JWT token.
    
    Decodes the JWT token, extracts user identifier, fetches user from database,
    and returns user information.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
    
    Returns:
        UserRead instance with user information
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Import jwt utilities inside function to avoid import-time dependencies
    try:
        from backend.utils.jwt import decode_token
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT utilities not available"
        )
    
    # Decode token to get payload
    try:
        payload = decode_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract user identifier from payload
    username = payload.get("username")
    user_id = payload.get("user_id")
    
    if not username and not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Fetch user from database
    user = None
    if username:
        user = get_user_by_username(db, username)
    elif user_id:
        # Import User model inside function to avoid circular imports
        from backend.models.user import User as UserModel
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Convert ORM user to Pydantic model
    try:
        return UserRead.from_orm(user)
    except Exception:
        # Fallback: manually construct UserRead if from_orm fails
        return UserRead(
            id=user.id,
            username=user.username,
            is_admin=getattr(user, "is_admin", False),
            created_at=user.created_at
        )


def get_current_active_user(
    current_user: UserRead = Depends(get_current_user)
) -> UserRead:
    """
    Verify that the current user is active.
    
    Checks if user has is_active flag set to True. If user model
    doesn't have is_active attribute, assumes user is active.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        UserRead instance if user is active
    
    Raises:
        HTTPException: If user is inactive
    """
    # Check if user has is_active attribute
    is_active = getattr(current_user, "is_active", True)
    
    if not is_active:
        raise HTTPException(
            status_code=400,
            detail="Inactive user"
        )
    
    return current_user


def get_current_admin_user(
    current_user: UserRead = Depends(get_current_user)
) -> UserRead:
    """
    Verify that the current user has admin privileges.
    
    Checks if user has is_admin or is_superuser flag set to True.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        UserRead instance if user is admin
    
    Raises:
        HTTPException: If user is not admin
    """
    # Check for admin privileges (is_admin or is_superuser)
    is_admin = getattr(current_user, "is_admin", False)
    is_superuser = getattr(current_user, "is_superuser", False)
    
    if not (is_admin or is_superuser):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    
    return current_user


__all__ = [
    "oauth2_scheme",
    "get_db_session",
    "get_settings",
    "pagination_params",
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user"
]

# Test hint: unit-test get_current_user by mocking jwt.decode_token to return a payload and mocking get_user_by_username/db queries.