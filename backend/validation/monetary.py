"""
backend/validation/monetary.py

Validators for monetary values, currency codes, and allocation ranges.
"""

from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple
from pydantic import validator


# ISO 4217 currency codes commonly used in government transparency platforms
SUPPORTED_CURRENCIES = {
    "INR", "USD", "EUR", "GBP", "JPY", "CNY", "AUD", "CAD", "CHF", "SGD"
}

# Maximum allocation (100 billion - reasonable for government subsidies)
MAX_ALLOCATION = Decimal("100_000_000_000")
# Minimum allocation (1 rupee/unit)
MIN_ALLOCATION = Decimal("0.01")


def validate_amount(amount: any) -> Decimal:
    """
    Validate a monetary amount.
    
    Args:
        amount: The amount to validate (can be string, int, float, or Decimal)
    
    Returns:
        Decimal value of the amount
    
    Raises:
        ValueError: If amount is invalid or out of range
    """
    try:
        decimal_amount = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValueError(f"Invalid amount format: {amount}") from e
    
    if decimal_amount < 0:
        raise ValueError("Amount cannot be negative")
    
    if decimal_amount > MAX_ALLOCATION:
        raise ValueError(f"Amount exceeds maximum allowed: {MAX_ALLOCATION}")
    
    return decimal_amount


def validate_currency_code(code: str) -> str:
    """
    Validate ISO 4217 currency code.
    
    Args:
        code: Three-letter currency code
    
    Returns:
        Uppercase currency code
    
    Raises:
        ValueError: If currency code is invalid
    """
    if not code:
        raise ValueError("Currency code cannot be empty")
    
    code_upper = code.strip().upper()
    
    if len(code_upper) != 3:
        raise ValueError("Currency code must be exactly 3 characters")
    
    if code_upper not in SUPPORTED_CURRENCIES:
        raise ValueError(
            f"Unsupported currency code: {code_upper}. "
            f"Supported: {', '.join(SUPPORTED_CURRENCIES)}"
        )
    
    return code_upper


def validate_allocation_range(
    allocation: Decimal,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None
) -> Tuple[Decimal, Decimal]:
    """
    Validate allocation falls within acceptable range.
    
    Args:
        allocation: The allocation amount to validate
        min_amount: Optional minimum (defaults to MIN_ALLOCATION)
        max_amount: Optional maximum (defaults to MAX_ALLOCATION)
    
    Returns:
        Tuple of (validated_allocation, effective_min)
    
    Raises:
        ValueError: If allocation is out of range
    """
    effective_min = min_amount if min_amount is not None else MIN_ALLOCATION
    effective_max = max_amount if max_amount is not None else MAX_ALLOCATION
    
    if allocation < effective_min:
        raise ValueError(
            f"Allocation {allocation} below minimum {effective_min}"
        )
    
    if allocation > effective_max:
        raise ValueError(
            f"Allocation {allocation} exceeds maximum {effective_max}"
        )
    
    return allocation, effective_min


# Pydantic validator versions for use in schemas
class MonetaryValidator:
    """Mixin class providing Pydantic validators for monetary fields."""
    
    @validator("amount")
    def validate_amount_field(cls, v):
        """Validate amount field in Pydantic schemas."""
        return validate_amount(v)
    
    @validator("currency")
    def validate_currency_field(cls, v):
        """Validate currency field in Pydantic schemas."""
        return validate_currency_code(v)
    
    @validator("total_allocation")
    def validate_allocation_field(cls, v):
        """Validate total_allocation field in Pydantic schemas."""
        return validate_amount(v)