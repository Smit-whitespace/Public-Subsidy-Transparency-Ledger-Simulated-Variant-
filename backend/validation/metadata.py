"""
backend/validation/metadata.py

Validators for metadata JSON structures.
"""

import json
from typing import Any, Dict, Optional


def validate_metadata_json(metadata: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Validate and parse metadata JSON string.
    
    Args:
        metadata: JSON string to validate
    
    Returns:
        Parsed dictionary or None if empty
    
    Raises:
        ValueError: If metadata is invalid JSON
    """
    if metadata is None or metadata.strip() == "":
        return None
    
    try:
        parsed = json.loads(metadata)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in metadata: {e}") from e
    
    if not isinstance(parsed, dict):
        raise ValueError("Metadata must be a JSON object (dictionary)")
    
    # Check for reasonable size (max 1MB as JSON string)
    if len(metadata) > 1_000_000:
        raise ValueError("Metadata exceeds maximum size of 1MB")
    
    return parsed


def validate_required_metadata_fields(
    metadata: Dict[str, Any],
    required_fields: list[str]
) -> None:
    """
    Validate that required fields exist in metadata.
    
    Args:
        metadata: Parsed metadata dictionary
        required_fields: List of required field names
    
    Raises:
        ValueError: If any required field is missing
    """
    missing = [field for field in required_fields if field not in metadata]
    
    if missing:
        raise ValueError(f"Missing required metadata fields: {', '.join(missing)}")


def sanitize_html(input_str: str) -> str:
    """
    Basic HTML sanitization for user input.
    
    Args:
        input_str: String to sanitize
    
    Returns:
        Sanitized string
    """
    if not input_str:
        return ""
    
    # Remove script tags
    sanitized = input_str.replace("<script", "&lt;script")
    sanitized = sanitized.replace("</script>", "&lt;/script>")
    
    # Remove on* event handlers
    dangerous = ["onerror=", "onclick=", "onload=", "onmouseover="]
    for pattern in dangerous:
        sanitized = sanitized.replace(pattern, "")
    
    return sanitized


def validate_string_input(
    value: Optional[str],
    field_name: str,
    max_length: int = 1000,
    allow_empty: bool = True
) -> Optional[str]:
    """
    Validate string input with sanitization.
    
    Args:
        value: String to validate
        field_name: Name of field (for error messages)
        max_length: Maximum allowed length
        allow_empty: Whether empty strings are allowed
    
    Returns:
        Sanitized string
    
    Raises:
        ValueError: If validation fails
    """
    if value is None:
        if allow_empty:
            return None
        raise ValueError(f"{field_name} cannot be None")
    
    # Strip whitespace
    trimmed = value.strip()
    
    if trimmed == "":
        if allow_empty:
            return None
        raise ValueError(f"{field_name} cannot be empty")
    
    if len(trimmed) > max_length:
        raise ValueError(f"{field_name} exceeds maximum length of {max_length}")
    
    # Apply basic sanitization
    return sanitize_html(trimmed)