"""
backend/test/test_disbursement.py

Unit tests for disbursement service: amount normalization, CRUD operations, and financial calculations.
"""

import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from backend.database.connection import Base
from backend.services.disbursement_service import (
    normalize_amount,
    create_disbursement,
    get_disbursement_by_id,
    list_disbursements,
    update_disbursement,
    delete_disbursement,
    total_disbursed_for_subsidy,
)
from backend.schemas.disbursement import DisbursementCreate, DisbursementUpdate


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


def test_normalize_amount_accepts_various_inputs() -> None:
    """
    Test that normalize_amount handles string, float, and Decimal inputs correctly.
    
    Verifies proper quantization to 2 decimal places.
    """
    # Test string input
    assert normalize_amount("1000.50") == Decimal("1000.50")
    
    # Test float input (quantized to 2 decimals)
    result = normalize_amount(1000.5)
    assert result == Decimal("1000.50")
    
    # Test Decimal input with extra precision (should quantize to 2 decimals)
    assert normalize_amount(Decimal("1000.500")) == Decimal("1000.50")
    
    # Test integer-like input
    assert normalize_amount("100") == Decimal("100.00")


def test_normalize_amount_rejects_invalid_or_nonpositive() -> None:
    """
    Test that normalize_amount raises ValueError for invalid or non-positive inputs.
    """
    # Test invalid string
    with pytest.raises(ValueError):
        normalize_amount("not-a-number")
    
    # Test negative amount
    with pytest.raises(ValueError):
        normalize_amount("-10")
    
    # Test zero amount
    with pytest.raises(ValueError):
        normalize_amount("0")
    
    # Test negative decimal
    with pytest.raises(ValueError):
        normalize_amount(Decimal("-5.50"))


def test_create_and_get_disbursement(db_session) -> None:
    """
    Test creating and retrieving a disbursement record.
    
    Verifies that:
    - Disbursement can be created successfully
    - Fields are stored correctly
    - Record can be retrieved by ID
    """
    # Create disbursement
    disb_in = DisbursementCreate(
        subsidy_id=1,
        amount="1500.75",
        currency="INR",
        reference="TX-1"
    )
    
    d = create_disbursement(db_session, disb_in)
    
    # Assert disbursement was created
    assert d.id is not None
    assert d.subsidy_id == 1
    assert d.amount == Decimal("1500.75")
    assert d.currency == "INR"
    assert d.reference == "TX-1"
    
    # Retrieve by ID
    fetched = get_disbursement_by_id(db_session, d.id)
    assert fetched is not None
    assert fetched.id == d.id
    assert fetched.amount == d.amount


def test_list_disbursements_filters_and_pagination(db_session) -> None:
    """
    Test listing disbursements with filters and pagination.
    
    Verifies:
    - Filtering by subsidy_id works
    - Amount range filters work
    - Pagination respects limit and offset
    """
    # Create disbursements for different subsidies with varying amounts
    disb1 = create_disbursement(db_session, DisbursementCreate(
        subsidy_id=2, amount="100.00", currency="INR", reference="TX-A"
    ))
    disb2 = create_disbursement(db_session, DisbursementCreate(
        subsidy_id=2, amount="200.00", currency="INR", reference="TX-B"
    ))
    disb3 = create_disbursement(db_session, DisbursementCreate(
        subsidy_id=3, amount="300.00", currency="INR", reference="TX-C"
    ))
    disb4 = create_disbursement(db_session, DisbursementCreate(
        subsidy_id=2, amount="400.00", currency="INR", reference="TX-D"
    ))
    
    # Test filtering by subsidy_id
    results = list_disbursements(db_session, subsidy_id=2, limit=10, offset=0)
    assert len(results) == 3
    assert all(d.subsidy_id == 2 for d in results)
    
    # Test amount range filtering
    results = list_disbursements(
        db_session,
        min_amount=Decimal("50.00"),
        max_amount=Decimal("250.00")
    )
    assert len(results) == 2
    assert all(Decimal("50.00") <= d.amount <= Decimal("250.00") for d in results)
    
    # Test pagination with limit
    results = list_disbursements(db_session, subsidy_id=2, limit=2, offset=0)
    assert len(results) == 2
    
    # Test pagination with offset
    results_page2 = list_disbursements(db_session, subsidy_id=2, limit=2, offset=2)
    assert len(results_page2) == 1


def test_update_disbursement_amount_and_notes(db_session) -> None:
    """
    Test updating disbursement fields.
    
    Verifies that amount and notes can be updated successfully.
    """
    # Create initial disbursement
    disb_in = DisbursementCreate(
        subsidy_id=1,
        amount="500.00",
        currency="INR",
        reference="TX-UPDATE",
        notes="Original notes"
    )
    disb = create_disbursement(db_session, disb_in)
    
    # Update amount and notes
    changes = DisbursementUpdate(
        amount="750.25",
        notes="Updated notes"
    )
    
    updated = update_disbursement(db_session, disb.id, changes)
    
    # Assert updates were applied
    assert updated.id == disb.id
    assert updated.amount == Decimal("750.25")
    assert updated.notes == "Updated notes"
    
    # Verify persistence by fetching again
    fetched = get_disbursement_by_id(db_session, disb.id)
    assert fetched.amount == Decimal("750.25")
    assert fetched.notes == "Updated notes"


def test_delete_disbursement(db_session) -> None:
    """
    Test deleting a disbursement record.
    
    Verifies that:
    - Disbursement can be deleted
    - Deleted record no longer exists in database
    """
    # Create disbursement
    disb_in = DisbursementCreate(
        subsidy_id=1,
        amount="100.00",
        currency="INR",
        reference="TX-DELETE"
    )
    disb = create_disbursement(db_session, disb_in)
    disb_id = disb.id
    
    # Verify it exists
    assert get_disbursement_by_id(db_session, disb_id) is not None
    
    # Delete disbursement
    delete_disbursement(db_session, disb_id)
    
    # Verify it no longer exists
    assert get_disbursement_by_id(db_session, disb_id) is None


def test_total_disbursed_for_subsidy(db_session) -> None:
    """
    Test calculating total disbursed amount for a subsidy.
    
    Verifies:
    - Sum calculation is correct
    - Returns Decimal with proper quantization
    - Returns zero for subsidy with no disbursements
    """
    # Create multiple disbursements for subsidy_id 5
    create_disbursement(db_session, DisbursementCreate(
        subsidy_id=5, amount="100.00", currency="INR", reference="TX-1"
    ))
    create_disbursement(db_session, DisbursementCreate(
        subsidy_id=5, amount="200.50", currency="INR", reference="TX-2"
    ))
    create_disbursement(db_session, DisbursementCreate(
        subsidy_id=5, amount="150.25", currency="INR", reference="TX-3"
    ))
    
    # Calculate total
    total = total_disbursed_for_subsidy(db_session, subsidy_id=5)
    
    # Expected: 100.00 + 200.50 + 150.25 = 450.75
    assert total == Decimal("450.75")
    
    # Test subsidy with no disbursements returns zero
    total_empty = total_disbursed_for_subsidy(db_session, subsidy_id=999)
    assert total_empty == Decimal("0.00")


# Run tests: pytest -q backend/test/test_disbursement.py