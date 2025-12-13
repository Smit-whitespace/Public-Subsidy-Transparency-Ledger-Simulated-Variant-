"""
backend/utils/hashing.py

Lightweight hashing utilities used across the application (SHA-256 helpers, hex encoding, and defensive validation).
"""

from __future__ import annotations
from typing import Union
import hashlib


def sha256_of(value: Union[str, bytes]) -> str:
    """
    Compute the SHA-256 hex digest of a string or bytes input.
    
    Returns a 64-character lowercase hex string.
    
    Args:
        value: String or bytes to hash
    
    Returns:
        SHA-256 hash as lowercase hex string (64 characters)
    
    Raises:
        ValueError: If value is empty or not str/bytes
    
    Example:
        >>> sha256_of("hello")
        '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
    """
    # Validate input type
    if not isinstance(value, (str, bytes)):
        raise ValueError(f"Value must be str or bytes, got {type(value).__name__}")
    
    # Handle string vs bytes
    if isinstance(value, str):
        if not value:
            raise ValueError("Cannot hash empty value")
        data = value.encode('utf-8')
    else:
        if not value:
            raise ValueError("Cannot hash empty value")
        data = value
    
    # Compute and return SHA-256 hex digest
    return hashlib.sha256(data).hexdigest()


def sha256_verify(value: Union[str, bytes], expected_hex: str) -> bool:
    """
    Recompute SHA-256 of the given value and compare with expected_hex safely.
    
    Returns True if hashes match, False otherwise.
    Never raises exceptions for comparison errors.
    
    Args:
        value: String or bytes to hash
        expected_hex: Expected SHA-256 hex digest (64 characters)
    
    Returns:
        True if computed hash matches expected_hex, False otherwise
    
    Example:
        >>> sha256_verify("hello", "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")
        True
    """
    # Validate expected_hex format
    if not is_valid_sha256_hex(expected_hex):
        return False
    
    # Try to compute hash and compare
    try:
        computed = sha256_of(value)
        return computed.lower() == expected_hex.lower()
    except (ValueError, TypeError):
        # If hashing fails for any reason, return False
        return False


def is_valid_sha256_hex(value: str) -> bool:
    """
    Quick check: is the given string a valid 64-char hex SHA-256 digest?
    
    Validates that the string is exactly 64 characters and contains only
    valid hexadecimal characters (0-9, a-f, A-F).
    
    Args:
        value: String to validate
    
    Returns:
        True if valid SHA-256 hex format, False otherwise
    
    Example:
        >>> is_valid_sha256_hex("a" * 64)
        True
        >>> is_valid_sha256_hex("xyz")
        False
    """
    # Must be a string
    if not isinstance(value, str):
        return False
    
    # Must be exactly 64 characters
    if len(value) != 64:
        return False
    
    # All characters must be valid hex (0-9, a-f, A-F)
    try:
        int(value, 16)
        return True
    except ValueError:
        return False


__all__ = ["sha256_of", "sha256_verify", "is_valid_sha256_hex"]