// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SubsidyProofRegistry
 * @notice On-chain registry for recording SHA-256 proof hashes of subsidy records.
 * @dev Allows any address to register a bytes32 proof (SHA-256 hash), assigns a unique proofId,
 * and provides lookup by id or hash. Owner can revoke proofs. Does not store full records on-chain.
 * 
 * Gas Optimization Notes:
 * - Uses bytes32 for compact storage (32 bytes vs dynamic string/bytes).
 * - Events are the primary mechanism for off-chain indexing - index proofs via logs.
 * - Contract stores only digests, not full payloads - compute SHA-256 off-chain.
 * 
 * Security Notes:
 * - Contract cannot access transaction hash from within EVM - clients read tx hash from receipt.
 * - Duplicate proofs are rejected to prevent replay/collisions.
 * - Revoked proofs remain in storage for historical audit but marked revoked.
 */
contract SubsidyProofRegistry {
    
    // ============ Storage Structures ============
    
    /**
     * @dev Proof record containing registration metadata.
     */
    struct Proof {
        uint256 id;
        address submitter;
        bytes32 proofHash;
        uint256 timestamp;
        bool revoked;
    }
    
    /// @dev Mapping from proof ID to Proof struct
    mapping(uint256 => Proof) private proofsById;
    
    /// @dev Mapping from proof hash to proof ID (0 means not registered)
    mapping(bytes32 => uint256) private idByHash;
    
    /// @dev Next proof ID to assign (starts at 1 for truthiness checks)
    uint256 private nextProofId;
    
    /// @dev Contract owner address for access control
    address public owner;
    
    
    // ============ Events ============
    
    /**
     * @dev Emitted when a new proof is registered.
     * @param proofId Unique identifier assigned to the proof
     * @param submitter Address that registered the proof
     * @param proofHash SHA-256 hash of the proof data
     * @param timestamp Block timestamp of registration
     */
    event ProofRegistered(
        uint256 indexed proofId,
        address indexed submitter,
        bytes32 indexed proofHash,
        uint256 timestamp
    );
    
    /**
     * @dev Emitted when a proof is revoked by owner.
     * @param proofId Unique identifier of the revoked proof
     * @param revokedBy Address that revoked the proof (owner)
     * @param timestamp Block timestamp of revocation
     */
    event ProofRevoked(
        uint256 indexed proofId,
        address indexed revokedBy,
        uint256 timestamp
    );
    
    /**
     * @dev Emitted when contract ownership is transferred.
     * @param previousOwner Previous owner address
     * @param newOwner New owner address
     */
    event OwnershipTransferred(
        address indexed previousOwner,
        address indexed newOwner
    );
    
    
    // ============ Modifiers ============
    
    /**
     * @dev Throws if called by any account other than the owner.
     */
    modifier onlyOwner() {
        require(msg.sender == owner, "Ownable: caller is not the owner");
        _;
    }
    
    
    // ============ Constructor ============
    
    /**
     * @dev Initializes contract with msg.sender as owner and nextProofId at 1.
     */
    constructor() {
        owner = msg.sender;
        nextProofId = 1; // Start at 1 to use 0 as "not found" sentinel
        emit OwnershipTransferred(address(0), msg.sender);
    }
    
    
    // ============ Ownership Functions ============
    
    /**
     * @dev Transfers ownership of the contract to a new account.
     * @param newOwner Address of the new owner
     */
    function transferOwnership(address newOwner) public onlyOwner {
        require(newOwner != address(0), "New owner is zero address");
        address oldOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
    
    /**
     * @dev Renounces ownership, leaving the contract without an owner.
     * @notice This will disable owner-only functions like revokeProof.
     */
    function renounceOwnership() public onlyOwner {
        address oldOwner = owner;
        owner = address(0);
        emit OwnershipTransferred(oldOwner, address(0));
    }
    
    
    // ============ Core Registry Functions ============
    
    /**
     * @dev Registers a new proof hash on-chain.
     * @param proofHash SHA-256 hash of proof data (32 bytes)
     * @return Unique proof ID assigned to this registration
     * 
     * Requirements:
     * - proofHash must not be zero (bytes32(0))
     * - proofHash must not already be registered
     * 
     * Gas Notes:
     * - Using bytes32 keeps storage compact (32 bytes vs dynamic bytes)
     * - Clients should compute SHA-256 off-chain and pass the digest
     * - Events are indexed for efficient off-chain querying
     */
    function registerProof(bytes32 proofHash) external returns (uint256) {
        require(proofHash != bytes32(0), "Zero proof hash");
        require(idByHash[proofHash] == 0, "Proof already registered");
        
        // Assign new proof ID
        uint256 id = nextProofId;
        nextProofId += 1;
        
        // Store proof record
        proofsById[id] = Proof({
            id: id,
            submitter: msg.sender,
            proofHash: proofHash,
            timestamp: block.timestamp,
            revoked: false
        });
        
        // Index by hash for lookup
        idByHash[proofHash] = id;
        
        // Emit event for off-chain indexing
        emit ProofRegistered(id, msg.sender, proofHash, block.timestamp);
        
        return id;
    }
    
    /**
     * @dev Retrieves proof details by proof ID.
     * @param proofId Unique proof identifier
     * @return id Proof ID
     * @return submitter Address that submitted the proof
     * @return proofHash SHA-256 hash of the proof
     * @return timestamp Block timestamp of registration
     * @return revoked Whether the proof has been revoked
     */
    function getProof(uint256 proofId) 
        external 
        view 
        returns (
            uint256 id,
            address submitter,
            bytes32 proofHash,
            uint256 timestamp,
            bool revoked
        ) 
    {
        require(proofId > 0 && proofId < nextProofId, "Proof not found");
        
        Proof memory proof = proofsById[proofId];
        return (
            proof.id,
            proof.submitter,
            proof.proofHash,
            proof.timestamp,
            proof.revoked
        );
    }
    
    /**
     * @dev Returns proof ID for a given proof hash.
     * @param proofHash SHA-256 hash to lookup
     * @return Proof ID (0 if not registered)
     * 
     * Note: Returning 0 indicates the proof hash is not registered.
     */
    function getProofIdByHash(bytes32 proofHash) external view returns (uint256) {
        return idByHash[proofHash];
    }
    
    /**
     * @dev Checks if a proof hash is registered.
     * @param proofHash SHA-256 hash to check
     * @return True if registered, false otherwise
     */
    function isProofRegistered(bytes32 proofHash) external view returns (bool) {
        return idByHash[proofHash] != 0;
    }
    
    /**
     * @dev Revokes a proof by marking it as revoked (owner only).
     * @param proofId Unique proof identifier to revoke
     * 
     * Note: Does not clear idByHash mapping to preserve historical record.
     * Revoked proofs remain queryable but marked as revoked for audit trail.
     */
    function revokeProof(uint256 proofId) external onlyOwner {
        require(proofId > 0 && proofId < nextProofId, "Proof not found");
        require(!proofsById[proofId].revoked, "Proof already revoked");
        
        proofsById[proofId].revoked = true;
        
        emit ProofRevoked(proofId, msg.sender, block.timestamp);
    }
    
    /**
     * @dev Returns the total number of proofs registered.
     * @return Total count of registered proofs
     */
    function totalProofs() external view returns (uint256) {
        return nextProofId > 0 ? nextProofId - 1 : 0;
    }
    
    /**
     * @dev Returns the most recent proof ID.
     * @return Latest proof ID (0 if no proofs registered)
     */
    function latestProofId() external view returns (uint256) {
        return nextProofId > 0 ? nextProofId - 1 : 0;
    }
}

/**
 * ============ Testing & Deployment Notes ============
 * 
 * Example Usage (ethers.js):
 * 
 * // Deploy contract
 * const Registry = await ethers.getContractFactory("SubsidyProofRegistry");
 * const registry = await Registry.deploy();
 * await registry.deployed();
 * 
 * // Register a proof
 * const proofHash = ethers.utils.sha256(ethers.utils.toUtf8Bytes(JSON.stringify(subsidyData)));
 * const tx = await registry.registerProof(proofHash);
 * const receipt = await tx.wait();
 * 
 * // Extract proof ID from event
 * const event = receipt.events?.find(e => e.event === 'ProofRegistered');
 * const proofId = event?.args?.proofId;
 * 
 * // Query proof by ID
 * const proof = await registry.getProof(proofId);
 * console.log(proof);
 * 
 * // Check if hash is registered
 * const isRegistered = await registry.isProofRegistered(proofHash);
 * 
 * Testing Recommendations:
 * - Test duplicate rejection: register same hash twice, expect revert
 * - Test zero hash rejection: register bytes32(0), expect revert
 * - Test event emission: verify ProofRegistered event with correct parameters
 * - Test revoke: owner can revoke, non-owner cannot
 * - Test ownership transfer: verify only owner can transfer/renounce
 * - Test gas costs: measure registerProof gas usage for optimization
 * - Index events off-chain: use event logs for efficient proof discovery
 * 
 * Gas Optimization:
 * - Average registerProof cost: ~50-70k gas (first registration higher due to storage)
 * - Use events for querying rather than on-chain iteration
 * - Consider batching multiple registrations if needed
 * 
 * Security Considerations:
 * - Anyone can register proofs (permissionless by design)
 * - Only owner can revoke proofs
 * - Consider adding pause mechanism for emergency situations
 * - Verify proof hashes match expected format before registration
 * - Monitor for spam registrations if deployed on mainnet
 */