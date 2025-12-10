"""
backend/services/auth_service.py

Auth service helpers: password hashing, verification, and basic user CRUD/auth helpers.
"""

from typing import Optional
from datetime import datetime, timedelta
import hashlib
import hmac
import os
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.models.user import User as UserModel
from backend.schemas.user import UserCreate


# Security constants for PBKDF2 hashing
PBKDF2_ITERATIONS = 200_000
SALT_SIZE = 16

# Note: This implementation uses stdlib PBKDF2-HMAC-SHA256 for simplicity and zero external dependencies.
# Production systems may prefer passlib or delegating to an external secrets management service.


def get_password_hash(password: str) -> str:
    """
    Hash a plain-text password using PBKDF2-HMAC-SHA256.
    
    Returns a storage string in the format:
    pbkdf2_sha256$<iterations>$<salt_hex>$<derived_key_hex>
    
    Args:
        password: Plain-text password to hash
    
    Returns:
        Hashed password string suitable for storage
    
    Raises:
        ValueError: If password is empty or whitespace-only
    """
    if not password or not password.strip():
        raise ValueError("Password cannot be empty or whitespace-only")
    
    # Generate a random salt for this password (16 bytes)
    salt = os.urandom(SALT_SIZE)
    
    # Derive key using PBKDF2-HMAC-SHA256 with 200k iterations
    derived_key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        PBKDF2_ITERATIONS
    )
    
    # Store as: algorithm$iterations$salt_hex$derived_key_hex
    salt_hex = salt.hex()
    dk_hex = derived_key.hex()
    
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_hex}${dk_hex}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verify a plain-text password against a stored hash.
    
    Uses constant-time comparison to avoid timing attacks.
    
    Args:
        plain_password: Plain-text password to verify
        stored_hash: Stored hash string from get_password_hash
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Parse stored hash: pbkdf2_sha256$iterations$salt_hex$dk_hex
        parts = stored_hash.split('$')
        if len(parts) != 4 or parts[0] != 'pbkdf2_sha256':
            # TODO: Log malformed hash warning for debugging
            # logger.warning(f"Malformed hash format: {stored_hash[:20]}...")
            return False
        
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        stored_dk = bytes.fromhex(parts[3])
        
        # Recompute derived key with same parameters
        computed_dk = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt,
            iterations
        )
        
        # Use constant-time comparison to avoid timing attacks
        return hmac.compare_digest(computed_dk, stored_dk)
        
    except (ValueError, IndexError) as e:
        # TODO: Log parsing error for debugging
        # logger.warning(f"Error parsing stored hash: {e}")
        return False


def get_user_by_username(db: Session, username: str) -> Optional[UserModel]:
    """
    Retrieve a user by username.
    
    Args:
        db: SQLAlchemy session
        username: Username to search for (should be pre-normalized by caller)
    
    Returns:
        UserModel if found, None otherwise
    """
    return db.query(UserModel).filter(UserModel.username == username).first()


def create_user(db: Session, user_in: UserCreate, commit: bool = True) -> UserModel:
    """
    Create a new user with hashed password.
    
    Args:
        db: SQLAlchemy session
        user_in: Validated UserCreate schema
        commit: Whether to commit immediately (default True)
    
    Returns:
        Created UserModel instance
    
    Raises:
        ValueError: If username already exists
        RuntimeError: If database operation fails
    """
    try:
        # Check if username already exists
        existing_user = get_user_by_username(db, user_in.username)
        if existing_user:
            raise ValueError(f"Username '{user_in.username}' already exists")
        
        # Hash the plain-text password
        hashed_password = get_password_hash(user_in.password)
        
        # Create user model
        user = UserModel(
            username=user_in.username,
            hashed_password=hashed_password,
            is_admin=user_in.is_admin
        )
        
        db.add(user)
        
        if commit:
            db.commit()
            db.refresh(user)
        
        return user
        
    except ValueError:
        # Re-raise ValueError (username exists) as-is for caller to handle
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"DB error while creating user: {str(e)}")


def authenticate_user(db: Session, username: str, password: str) -> Optional[UserModel]:
    """
    Authenticate a user by username and password.
    
    Args:
        db: SQLAlchemy session
        username: Username to authenticate
        password: Plain-text password to verify
    
    Returns:
        UserModel if authentication succeeds, None otherwise
    """
    user = get_user_by_username(db, username)
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


__all__ = ["get_password_hash", "verify_password", "get_user_by_username", "create_user", "authenticate_user"]

# Test hint: create a temp sqlite Session, call create_user(db, UserCreate(...)), then assert authenticate_user(db, username, password) is not None.