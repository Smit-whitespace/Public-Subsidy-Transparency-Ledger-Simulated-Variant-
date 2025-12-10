"""
backend/services/blockchain_service.py

Helpers to write/read compact proof records (hashes) to/from a blockchain. Falls back to a safe no-op stub when RPC or web3 is unavailable.
"""

from typing import Optional, Dict, Any
from decimal import Decimal
import json
import os

from backend.config import settings


# Minimal contract ABI fragments for proof registration
# In production, load from a proper ABI file or contract artifact
PROOF_CONTRACT_ABI = [
    {
        "inputs": [{"name": "proof", "type": "bytes32"}],
        "name": "registerProof",
        "outputs": [{"name": "proofId", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "id", "type": "uint256"}],
        "name": "getProof",
        "outputs": [{"name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "id", "type": "uint256"},
            {"indexed": False, "name": "proof", "type": "bytes32"}
        ],
        "name": "ProofRegistered",
        "type": "event"
    }
]


# Production notes:
# - Never hardcode private keys in source code
# - Use KMS/HSM or external signing service (e.g., AWS KMS, Google Cloud KMS, or hardware wallets)
# - Configure gas strategies (e.g., EIP-1559, fast/medium/slow) based on network conditions
# - Implement proper nonce management for concurrent transactions
# - Consider using a transaction relay service for production workloads


def _validate_hash(hash_value: str) -> None:
    """
    Validate that hash_value looks like a valid SHA-256 hex string.
    
    Raises:
        ValueError: If hash is malformed
    """
    if not isinstance(hash_value, str):
        raise ValueError("Hash must be a string")
    
    # Remove 0x prefix if present
    clean_hash = hash_value.lower().replace("0x", "")
    
    if len(clean_hash) != 64:
        raise ValueError(f"Hash must be 64 hex characters (32 bytes), got {len(clean_hash)}")
    
    try:
        int(clean_hash, 16)
    except ValueError:
        raise ValueError(f"Hash must be valid hexadecimal: {hash_value}")


def _is_web3_available() -> bool:
    """Check if web3 and blockchain configuration are available."""
    try:
        import web3
        return bool(
            getattr(settings, 'BLOCKCHAIN_RPC', None) and 
            getattr(settings, 'CONTRACT_ADDRESS', None)
        )
    except ImportError:
        return False


def _serialize_receipt(receipt: Any) -> Dict[str, Any]:
    """
    Extract key fields from transaction receipt for compact storage.
    
    Args:
        receipt: Web3 transaction receipt object
    
    Returns:
        Compact dict with essential receipt data
    """
    try:
        return {
            "blockNumber": receipt.get("blockNumber"),
            "transactionHash": receipt.get("transactionHash", b"").hex() if isinstance(receipt.get("transactionHash"), bytes) else str(receipt.get("transactionHash")),
            "status": receipt.get("status"),
            "gasUsed": receipt.get("gasUsed"),
            "logs_count": len(receipt.get("logs", []))
        }
    except Exception:
        return {"error": "receipt serialization failed"}


def write_proof_to_chain(hash_value: str) -> Dict[str, Any]:
    """
    Record a proof (SHA-256 hash) on-chain and return metadata.
    
    If web3/RPC/contract are not configured, operates in stub mode and returns
    a safe dict indicating no-op status.
    
    Args:
        hash_value: SHA-256 hash as 64-character hex string (with or without 0x prefix)
    
    Returns:
        Dict containing transaction metadata or stub message:
        - on_chain: bool (True if actually written to chain)
        - tx_hash: transaction hash if on_chain
        - proof_id: proof ID returned by contract if available
        - receipt: compact transaction receipt
        - message: descriptive message if in stub mode
    
    Raises:
        ValueError: If hash format is invalid
        RuntimeError: If web3 configured but signing/sending fails
    """
    _validate_hash(hash_value)
    
    # Normalize hash to 0x-prefixed format
    clean_hash = hash_value.lower().replace("0x", "")
    prefixed_hash = f"0x{clean_hash}"
    
    if not _is_web3_available():
        # Stub mode: web3 or configuration not available
        return {
            "on_chain": False,
            "hash": prefixed_hash,
            "message": "web3 or RPC not configured — running in stub mode"
        }
    
    try:
        from web3 import Web3
        from eth_account import Account
        
        # Connect to blockchain RPC
        w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC))
        
        if not w3.is_connected():
            raise RuntimeError("Failed to connect to blockchain RPC")
        
        # Load contract
        contract_address = Web3.to_checksum_address(settings.CONTRACT_ADDRESS)
        contract = w3.eth.contract(address=contract_address, abi=PROOF_CONTRACT_ABI)
        
        # IMPORTANT: In production, use KMS/HSM or external signer service
        # For local development only, you can set BLOCKCHAIN_SIGNER_KEY env var
        # Example: export BLOCKCHAIN_SIGNER_KEY="0x<private_key>"
        signer_key = os.environ.get("BLOCKCHAIN_SIGNER_KEY")
        
        if not signer_key:
            raise RuntimeError(
                "No blockchain signer configured. "
                "Set BLOCKCHAIN_SIGNER_KEY env var for local dev, "
                "or integrate with KMS/external signer for production."
            )
        
        # Create account from private key (only for local dev!)
        account = Account.from_key(signer_key)
        
        # Convert hash to bytes32
        hash_bytes = bytes.fromhex(clean_hash)
        
        # Build transaction
        # TODO: Implement proper gas estimation and EIP-1559 strategy
        nonce = w3.eth.get_transaction_count(account.address)
        
        transaction = contract.functions.registerProof(hash_bytes).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 200000,  # TODO: Estimate gas dynamically
            'gasPrice': w3.eth.gas_price,  # TODO: Use better gas strategy
        })
        
        # Sign transaction
        signed_txn = account.sign_transaction(transaction)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for receipt (synchronous)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        # Parse logs to extract proof_id from ProofRegistered event
        proof_id = None
        try:
            proof_registered_event = contract.events.ProofRegistered()
            logs = proof_registered_event.process_receipt(receipt)
            if logs:
                proof_id = logs[0]['args']['id']
        except Exception as log_error:
            # Log parsing failed; proof_id will remain None
            # TODO: Integrate logging
            # logger.warning(f"Failed to parse ProofRegistered event: {log_error}")
            pass
        
        return {
            "on_chain": True,
            "tx_hash": tx_hash.hex(),
            "proof_id": proof_id,
            "receipt": _serialize_receipt(receipt),
            "hash": prefixed_hash
        }
        
    except ImportError as e:
        raise RuntimeError(f"web3 library not installed: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to write proof to chain: {str(e)}")


def read_proof_from_chain(proof_id: int) -> Dict[str, Any]:
    """
    Fetch on-chain proof data by proof ID.
    
    If web3/RPC/contract are not configured, returns a message indicating stub mode.
    
    Args:
        proof_id: Proof ID to retrieve (positive integer)
    
    Returns:
        Dict containing proof data or stub message:
        - on_chain: bool
        - proof_id: the requested ID
        - hash: the stored hash if found
        - message: descriptive message if not configured
    
    Raises:
        ValueError: If proof_id is invalid
        RuntimeError: If configured but read operation fails
    """
    if not isinstance(proof_id, int) or proof_id < 0:
        raise ValueError(f"proof_id must be a non-negative integer, got {proof_id}")
    
    if not _is_web3_available():
        return {
            "on_chain": False,
            "proof_id": proof_id,
            "message": "web3 or RPC not configured — running in stub mode"
        }
    
    try:
        from web3 import Web3
        
        # Connect to blockchain RPC
        w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC))
        
        if not w3.is_connected():
            raise RuntimeError("Failed to connect to blockchain RPC")
        
        # Load contract
        contract_address = Web3.to_checksum_address(settings.CONTRACT_ADDRESS)
        contract = w3.eth.contract(address=contract_address, abi=PROOF_CONTRACT_ABI)
        
        # Call view function to get proof
        proof_bytes = contract.functions.getProof(proof_id).call()
        
        # Convert bytes32 to hex string
        proof_hex = f"0x{proof_bytes.hex()}"
        
        return {
            "on_chain": True,
            "proof_id": proof_id,
            "hash": proof_hex
        }
        
    except ImportError as e:
        raise RuntimeError(f"web3 library not installed: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to read proof from chain: {str(e)}")


def get_latest_proof_for_hash(hash_value: str) -> Optional[Dict[str, Any]]:
    """
    Try to find an on-chain proof that matches a given hash.
    
    This is a best-effort lookup that scans recent ProofRegistered events.
    If web3/RPC not configured, returns None.
    
    Args:
        hash_value: SHA-256 hash to search for
    
    Returns:
        Dict with proof metadata if found, None otherwise:
        - proof_id: the on-chain proof ID
        - tx_hash: transaction hash
        - blockNumber: block number where registered
    
    Raises:
        ValueError: If hash format is invalid
    """
    _validate_hash(hash_value)
    
    # Normalize hash
    clean_hash = hash_value.lower().replace("0x", "")
    prefixed_hash = f"0x{clean_hash}"
    
    if not _is_web3_available():
        return None
    
    try:
        from web3 import Web3
        
        # Connect to blockchain RPC
        w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC))
        
        if not w3.is_connected():
            return None
        
        # Load contract
        contract_address = Web3.to_checksum_address(settings.CONTRACT_ADDRESS)
        contract = w3.eth.contract(address=contract_address, abi=PROOF_CONTRACT_ABI)
        
        # Scan recent blocks for ProofRegistered events
        # TODO: Implement proper event indexing or use a subgraph for production
        latest_block = w3.eth.block_number
        from_block = max(0, latest_block - 10000)  # Scan last 10k blocks
        
        proof_registered_event = contract.events.ProofRegistered()
        
        # Get logs matching the hash
        hash_bytes = bytes.fromhex(clean_hash)
        logs = proof_registered_event.get_logs(
            fromBlock=from_block,
            toBlock='latest'
        )
        
        # Find matching proof
        for log in logs:
            if log['args']['proof'] == hash_bytes:
                return {
                    "proof_id": log['args']['id'],
                    "tx_hash": log['transactionHash'].hex(),
                    "blockNumber": log['blockNumber']
                }
        
        return None
        
    except Exception as e:
        # TODO: Integrate logging
        # logger.warning(f"Failed to search for proof: {e}")
        return None


__all__ = ["write_proof_to_chain", "read_proof_from_chain", "get_latest_proof_for_hash"]

# Test hint: run write_proof_to_chain in stub mode (no RPC) and assert returned["on_chain"] is False; unit tests for web3 mode should mock web3 provider and contract.