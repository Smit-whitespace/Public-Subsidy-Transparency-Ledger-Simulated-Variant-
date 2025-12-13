"""
backend/test/test_auth.py

Unit tests for authentication service: password hashing, verification, user creation, and authentication.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from backend.database.connection import Base
from backend.models.user import User as UserModel
from backend.services.auth_service import (
    get_password_hash,
    verify_password,
    create_user,
    get_user_by_username,
    authenticate_user
)
from backend.schemas.user import UserCreate


@pytest.fixture
def db_session():
    """
    Create an in-memory SQLite database for isolated testing.
    
    Yields:
        SQLAlchemy Session instance with all tables created
    """
    # Create in-memory SQLite engine
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    
    # Create session factory
    SessionLocal = sessionmaker(bind=engine)
    
    # Create all tables from Base metadata
    Base.metadata.create_all(bind=engine)
    
    # Create and yield session
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_password_hash_and_verify() -> None:
    """
    Test password hashing and verification.
    
    Verifies that:
    - Hashed password is not equal to plain password
    - Correct password verifies successfully
    - Incorrect password fails verification
    """
    plain_password = "s3cret!"
    
    # Hash the password
    hashed = get_password_hash(plain_password)
    
    # Assert hash is non-empty and different from plain password
    assert hashed
    assert isinstance(hashed, str)
    assert hashed != plain_password
    
    # Verify correct password
    assert verify_password(plain_password, hashed) is True
    
    # Verify incorrect password fails
    assert verify_password("wrong-password", hashed) is False


def test_create_and_authenticate_user(db_session) -> None:
    """
    Test user creation, retrieval, and authentication.
    
    Verifies that:
    - User can be created successfully
    - User can be retrieved by username
    - Authentication succeeds with correct credentials
    - Authentication fails with incorrect credentials
    """
    # Create user
    user_in = UserCreate(username="alice_test", password="strong-pass")
    user = create_user(db_session, user_in)
    
    # Assert user was created with ID
    assert user.id is not None
    assert user.username == user_in.username.strip().lower()
    
    # Retrieve user by username
    fetched_user = get_user_by_username(db_session, user.username)
    assert fetched_user is not None
    assert fetched_user.id == user.id
    assert fetched_user.username == user.username
    
    # Authenticate with correct credentials
    authenticated_user = authenticate_user(db_session, user.username, "strong-pass")
    assert authenticated_user is not None
    assert authenticated_user.id == user.id
    
    # Authentication fails with wrong password
    failed_auth = authenticate_user(db_session, user.username, "wrong-password")
    assert failed_auth is None
    
    # Authentication fails with non-existent username
    failed_auth = authenticate_user(db_session, "nonexistent_user", "strong-pass")
    assert failed_auth is None


def test_create_user_duplicate_username_raises(db_session) -> None:
    """
    Test that creating a user with duplicate username raises an error.
    
    Verifies that attempting to create a second user with the same username
    raises either ValueError or IntegrityError.
    """
    # Create first user successfully
    user_in = UserCreate(username="bob_test", password="test-password")
    user = create_user(db_session, user_in)
    assert user.id is not None
    
    # Attempt to create duplicate user - should raise ValueError or IntegrityError
    duplicate_user_in = UserCreate(username="bob_test", password="different-password")
    
    with pytest.raises((ValueError, IntegrityError)):
        create_user(db_session, duplicate_user_in)


# Run these tests with: pytest -q backend/test/test_auth.py