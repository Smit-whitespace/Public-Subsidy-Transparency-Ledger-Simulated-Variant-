"""
backend/tests/test_auth.py

Unit tests for authentication service.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from backend.database.connection import Base
from backend.services.auth_service import (
    get_password_hash,
    verify_password,
    create_user,
    get_user_by_username,
    authenticate_user,
)
from backend.schemas.user import UserCreate


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_password_hash_and_verify():
    password = "s3cret!"

    hashed = get_password_hash(password)

    assert hashed
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_create_and_authenticate_user(db_session):
    user_in = UserCreate(
        username="alice_test",
        password="strong-pass"
    )

    user = create_user(db_session, user_in)

    assert user.id is not None
    assert user.username == "alice_test"

    fetched = get_user_by_username(db_session, "alice_test")

    assert fetched is not None
    assert fetched.id == user.id

    authenticated = authenticate_user(
        db_session,
        "alice_test",
        "strong-pass"
    )

    assert authenticated is not None
    assert authenticated.id == user.id

    failed = authenticate_user(
        db_session,
        "alice_test",
        "wrong-password"
    )

    assert failed is None


def test_create_user_duplicate_username_raises(db_session):
    user = UserCreate(
        username="bob_test",
        password="password"
    )

    create_user(db_session, user)

    duplicate = UserCreate(
        username="bob_test",
        password="another"
    )

    with pytest.raises((ValueError, IntegrityError)):
        create_user(db_session, duplicate)