"""
backend/validation/temporal.py

Validators for date ordering, ranges, and pagination inputs.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from pydantic import validator


# Pagination limits
MIN_PAGE = 1
MAX_PAGE = 10000
DEFAULT_PAGE = 1
MIN_PAGE_SIZE = 1
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20

# Date range limits
MIN_DATE = datetime(1900, 1, 1)
MAX_DATE = datetime(2100, 12, 31)


def validate_date_order(
    start_date: Optional[datetime],
    end_date: Optional[datetime]
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Validate that end_date is after start_date.
    
    Args:
        start_date: The start date
        end_date: The end date
    
    Returns:
        Tuple of (start_date, end_date)
    
    Raises:
        ValueError: If end_date is before start_date
    """
    if start_date is not None and end_date is not None:
        if end_date < start_date:
            raise ValueError(
                f"end_date ({end_date}) cannot be before start_date ({start_date})"
            )
    
    return start_date, end_date


def validate_date_range(
    date: datetime,
    min_date: Optional[datetime] = None,
    max_date: Optional[datetime] = None
) -> datetime:
    """
    Validate date falls within acceptable range.
    
    Args:
        date: The date to validate
        min_date: Optional minimum date (defaults to MIN_DATE)
        max_date: Optional maximum date (defaults to MAX_DATE)
    
    Returns:
        The validated date
    
    Raises:
        ValueError: If date is out of range
    """
    effective_min = min_date if min_date is not None else MIN_DATE
    effective_max = max_date if max_date is not None else MAX_DATE
    
    if date < effective_min:
        raise ValueError(f"Date {date} is before minimum {effective_min}")
    
    if date > effective_max:
        raise ValueError(f"Date {date} is after maximum {effective_max}")
    
    return date


def validate_pagination(
    page: Optional[int] = None,
    page_size: Optional[int] = None
) -> Tuple[int, int]:
    """
    Validate pagination parameters.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
    
    Returns:
        Tuple of (validated_page, validated_page_size)
    
    Raises:
        ValueError: If pagination parameters are invalid
    """
    validated_page = page if page is not None else DEFAULT_PAGE
    validated_page_size = page_size if page_size is not None else DEFAULT_PAGE_SIZE
    
    if validated_page < MIN_PAGE:
        raise ValueError(f"Page must be at least {MIN_PAGE}")
    
    if validated_page > MAX_PAGE:
        raise ValueError(f"Page cannot exceed {MAX_PAGE}")
    
    if validated_page_size < MIN_PAGE_SIZE:
        raise ValueError(f"Page size must be at least {MIN_PAGE_SIZE}")
    
    if validated_page_size > MAX_PAGE_SIZE:
        raise ValueError(f"Page size cannot exceed {MAX_PAGE_SIZE}")
    
    return validated_page, validated_page_size


def validate_search_query(query: Optional[str], max_length: int = 200) -> str:
    """
    Validate search query string.
    
    Args:
        query: Search query string
        max_length: Maximum allowed length
    
    Returns:
        Trimmed search query
    
    Raises:
        ValueError: If query is invalid
    """
    if query is None:
        return ""
    
    trimmed = query.strip()
    
    if len(trimmed) > max_length:
        raise ValueError(f"Search query exceeds maximum length of {max_length}")
    
    # Check for dangerous characters (basic sanitization)
    dangerous_patterns = ["<script", "javascript:", "onerror=", "onclick="]
    for pattern in dangerous_patterns:
        if pattern.lower() in trimmed.lower():
            raise ValueError("Search query contains invalid characters")
    
    return trimmed


# Pydantic validator versions for use in schemas
class TemporalValidator:
    """Mixin class providing Pydantic validators for temporal fields."""
    
    @validator("start_date")
    def validate_start_date(cls, v):
        """Validate start_date field."""
        if v is not None:
            validate_date_range(v)
        return v
    
    @validator("end_date")
    def validate_end_date(cls, v):
        """Validate end_date field."""
        if v is not None:
            validate_date_range(v)
        return v
    
    @validator("date")
    def validate_date_field(cls, v):
        """Validate date field."""
        if v is not None:
            validate_date_range(v)
        return v