"""
backend/utils/validators.py

Small validation & sanitization helpers: emails, UUIDs, ISO datetimes, currency codes, slugs, filenames, and pagination param validation.
"""

from __future__ import annotations
import re
from typing import Optional, Tuple
from datetime import datetime
from decimal import Decimal, InvalidOperation
import uuid
import unicodedata
from pathlib import Path


def is_valid_email(value: str) -> bool:
    """
    Check if value looks like a reasonable email address.
    
    Uses a conservative regex pattern - not RFC-compliant but catches most cases.
    For production, consider a dedicated email validation library.
    
    Args:
        value: String to validate
    
    Returns:
        True if looks like an email, False otherwise
    """
    if not isinstance(value, str) or not value:
        return False
    
    # Conservative email pattern: local@domain.tld
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, value.strip()))


def is_valid_uuid(value: str) -> bool:
    """
    Check if value is a valid UUID (v1-v5).
    
    Args:
        value: String to validate
    
    Returns:
        True if valid UUID, False otherwise
    """
    if not isinstance(value, str):
        return False
    
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def parse_iso8601_datetime(value: str) -> datetime:
    """
    Parse ISO8601-like datetime string into datetime object.
    
    Accepts formats like "2023-01-02T15:04:05" with optional timezone.
    Does not support all RFC 3339 variants - use for common cases only.
    
    Args:
        value: ISO8601 datetime string
    
    Returns:
        Parsed datetime object
    
    Raises:
        ValueError: If string cannot be parsed
    """
    if not isinstance(value, str) or not value:
        raise ValueError("Invalid ISO8601 datetime")
    
    try:
        # Try standard fromisoformat (handles most cases)
        return datetime.fromisoformat(value.strip())
    except ValueError:
        pass
    
    # Try with Z suffix (common in JSON)
    try:
        clean = value.strip().replace('Z', '+00:00')
        return datetime.fromisoformat(clean)
    except ValueError:
        raise ValueError("Invalid ISO8601 datetime")


def parse_decimal_amount(value: str | int | float | Decimal) -> Decimal:
    """
    Safely convert value to Decimal for monetary amounts.
    
    Rejects negative or zero values.
    
    Args:
        value: Amount as string, int, float, or Decimal
    
    Returns:
        Decimal representation
    
    Raises:
        ValueError: If conversion fails or value is non-positive
    """
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Invalid decimal amount: {value}")
    
    if decimal_value <= 0:
        raise ValueError(f"Amount must be positive, got: {decimal_value}")
    
    return decimal_value


def validate_currency_code(code: str) -> bool:
    """
    Validate currency code format (3-letter alphabetic).
    
    Structural check only - does not verify against ISO 4217 list.
    For strict validation, use a maintained currency code database.
    
    Args:
        code: Currency code to validate
    
    Returns:
        True if format is valid, False otherwise
    """
    if not isinstance(code, str):
        return False
    
    # Normalize and check format
    normalized = code.strip().upper()
    
    # Must be exactly 3 alphabetic characters
    return len(normalized) == 3 and normalized.isalpha()


def validate_slug(value: str, max_length: int = 100) -> str:
    """
    Normalize input into a safe URL slug.
    
    Rules:
    - Lowercase
    - Replace whitespace and invalid chars with hyphens
    - Remove non-ASCII characters
    - Collapse multiple hyphens
    - Strip leading/trailing hyphens
    - Enforce max_length
    
    Args:
        value: String to slugify
        max_length: Maximum length for slug
    
    Returns:
        Normalized slug string
    
    Raises:
        ValueError: If resulting slug is empty or exceeds max_length
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Cannot create slug from empty value")
    
    # Normalize unicode characters (decompose accents, etc)
    normalized = unicodedata.normalize('NFKD', value)
    
    # Remove non-ASCII characters
    ascii_str = normalized.encode('ascii', 'ignore').decode('ascii')
    
    # Lowercase and strip
    slug = ascii_str.lower().strip()
    
    # Replace whitespace and invalid chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    
    # Collapse multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Strip leading/trailing hyphens
    slug = slug.strip('-')
    
    # Validate length
    if not slug:
        raise ValueError("Slug cannot be empty after normalization")
    
    if len(slug) > max_length:
        raise ValueError(f"Slug exceeds maximum length of {max_length}")
    
    return slug


def sanitize_filename(name: str) -> str:
    """
    Return a safe filename stripped of path separators and control characters.
    
    Removes path components and dangerous characters while preserving extension.
    Always returns basename only - no directory traversal.
    
    Args:
        name: Filename to sanitize
    
    Returns:
        Sanitized filename
    
    Raises:
        ValueError: If input is invalid or results in empty name
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Filename cannot be empty")
    
    # Get basename only (removes any path components)
    base = Path(name).name
    
    # Remove control characters and path separators
    # Keep alphanumeric, dots, hyphens, underscores
    sanitized = re.sub(r'[^\w\s.-]', '', base)
    
    # Collapse multiple spaces/dots
    sanitized = re.sub(r'\s+', '_', sanitized)
    sanitized = re.sub(r'\.+', '.', sanitized)
    
    # Strip leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Prevent directory traversal patterns
    if sanitized in ('', '.', '..') or '/' in sanitized or '\\' in sanitized:
        raise ValueError("Invalid filename")
    
    if not sanitized:
        raise ValueError("Filename is empty after sanitization")
    
    return sanitized


def validate_pagination_params(
    limit: int,
    offset: int,
    *,
    max_limit: int = 1000
) -> Tuple[int, int]:
    """
    Validate pagination parameters.
    
    Ensures limit and offset are valid non-negative integers within bounds.
    
    Args:
        limit: Number of items per page (must be 1 to max_limit)
        offset: Number of items to skip (must be >= 0)
        max_limit: Maximum allowed limit value
    
    Returns:
        Validated (limit, offset) tuple
    
    Raises:
        ValueError: If parameters are invalid
    """
    # Validate types
    if not isinstance(limit, int) or not isinstance(offset, int):
        raise ValueError("Limit and offset must be integers")
    
    # Validate limit range
    if limit < 1:
        raise ValueError(f"Limit must be >= 1, got {limit}")
    
    if limit > max_limit:
        raise ValueError(f"Limit must be <= {max_limit}, got {limit}")
    
    # Validate offset
    if offset < 0:
        raise ValueError(f"Offset must be >= 0, got {offset}")
    
    return (limit, offset)


def safe_filename_to_path(name: str, base: Optional[str] = None) -> Path:
    """
    Convert filename to safe Path, optionally joined to base directory.
    
    Uses sanitize_filename to ensure basename safety, then joins to base.
    Prevents absolute paths and directory traversal.
    
    Note: This is a convenience helper, not a security silver-bullet.
    Always perform additional validation in production contexts.
    
    Args:
        name: Filename to convert
        base: Optional base directory to join to
    
    Returns:
        Safe Path object
    
    Raises:
        ValueError: If filename is invalid or attempts directory traversal
    """
    # Sanitize the filename first
    safe_name = sanitize_filename(name)
    
    # Create Path from sanitized name
    file_path = Path(safe_name)
    
    # Ensure not absolute
    if file_path.is_absolute():
        raise ValueError("Filename cannot be an absolute path")
    
    # Join to base if provided
    if base is not None:
        base_path = Path(base)
        result_path = base_path / file_path
        
        # Verify result doesn't escape base directory
        try:
            # Use resolve to check for traversal attempts
            resolved_base = base_path.resolve()
            resolved_result = result_path.resolve()
            
            # Check if result is under base
            try:
                resolved_result.relative_to(resolved_base)
            except ValueError:
                raise ValueError("Path attempts to escape base directory")
            
            return result_path
            
        except (OSError, RuntimeError):
            raise ValueError("Invalid path construction")
    
    return file_path


__all__ = [
    "is_valid_email",
    "is_valid_uuid",
    "parse_iso8601_datetime",
    "parse_decimal_amount",
    "validate_currency_code",
    "validate_slug",
    "sanitize_filename",
    "validate_pagination_params",
    "safe_filename_to_path"
]

# Test hint: unit-test each validator with valid/invalid inputs; for filenames test join with a tmpdir to ensure path safety.