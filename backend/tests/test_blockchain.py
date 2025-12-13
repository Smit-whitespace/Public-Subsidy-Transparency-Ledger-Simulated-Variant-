"""
backend/test/test_blockchain.py

Unit tests for blockchain service: stub mode behavior, input validation, and read-path testing.
"""

import pytest

from backend.services.blockchain_service import (
    write_proof_to_chain,
    read_proof_from_chain,
    get_latest_proof_for_hash
)
from backend.config import settings


def test_write_proof_stub_mode_returns_stub_dict(monkeypatch) -> None:
    """
    Test that write_proof_to_chain returns a stub dict when RPC is not configured.
    
    Verifies that:
    - Function returns a dict in stub mode
    - on_chain flag is False
    - Hash value is preserved
    - Message indicates stub mode
    """
    # Force stub mode by clearing blockchain configuration
    monkeypatch.setattr(settings, "BLOCKCHAIN_RPC", "")
    monkeypatch.setattr(settings, "CONTRACT_ADDRESS", "")
    
    # Valid 64-character hex hash (SHA-256)
    test_hash = "a" * 64
    
    # Call write_proof_to_chain in stub mode
    result = write_proof_to_chain(test_hash)
    
    # Assert stub mode behavior
    assert isinstance(result, dict)
    assert result.get("on_chain") is False
    assert test_hash in result.get("hash", "")
    
    # Check message indicates stub/not configured
    message = result.get("message", "").lower()
    assert "stub" in message or "not configured" in message


def test_write_proof_invalid_hash_raises() -> None:
    """
    Test that write_proof_to_chain validates hash format.
    
    Verifies that invalid hash formats raise ValueError before any network calls.
    """
    # Test various invalid hash formats
    invalid_hashes = [
        "xyz",  # Not hex
        "abc123",  # Too short
        "Z" * 64,  # Invalid hex characters
        "",  # Empty
        "abc" * 20,  # Wrong length (60 chars)
    ]
    
    for invalid_hash in invalid_hashes:
        with pytest.raises(ValueError):
            write_proof_to_chain(invalid_hash)


def test_read_proof_stub_mode_returns_not_configured(monkeypatch) -> None:
    """
    Test that read_proof_from_chain returns stub message when not configured.
    
    Verifies that:
    - Function returns a dict in stub mode
    - on_chain flag is False
    - proof_id is preserved in response
    - Message indicates not configured
    """
    # Force stub mode
    monkeypatch.setattr(settings, "BLOCKCHAIN_RPC", "")
    monkeypatch.setattr(settings, "CONTRACT_ADDRESS", "")
    
    proof_id = 123
    
    # Call read_proof_from_chain in stub mode
    result = read_proof_from_chain(proof_id)
    
    # Assert stub mode behavior
    assert isinstance(result, dict)
    assert result.get("on_chain") is False
    assert result.get("proof_id") == proof_id
    
    # Check message indicates not configured
    message = result.get("message", "").lower()
    assert "not configured" in message or "stub" in message


def test_get_latest_proof_for_hash_stub_returns_none(monkeypatch) -> None:
    """
    Test that get_latest_proof_for_hash returns None in stub mode.
    
    Verifies that the function returns None when blockchain is not configured,
    rather than attempting network calls or raising exceptions.
    """
    # Force stub mode
    monkeypatch.setattr(settings, "BLOCKCHAIN_RPC", "")
    monkeypatch.setattr(settings, "CONTRACT_ADDRESS", "")
    
    # Valid 64-character hex hash
    test_hash = "b" * 64
    
    # Call get_latest_proof_for_hash in stub mode
    result = get_latest_proof_for_hash(test_hash)
    
    # Assert returns None in stub mode
    assert result is None


# Run: pytest -q backend/test/test_blockchain.py