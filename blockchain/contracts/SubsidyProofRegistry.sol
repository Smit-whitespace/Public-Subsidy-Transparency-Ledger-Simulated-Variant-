// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SubsidyProofRegistry {
    mapping(uint256 => bytes32) public proofs;
    uint256 public count;

    event ProofRegistered(uint256 indexed id, bytes32 proof);

    function registerProof(bytes32 proof) public returns (uint256) {
        count += 1;
        proofs[count] = proof;
        emit ProofRegistered(count, proof);
        return count;
    }

    function getProof(uint256 id) public view returns (bytes32) {
        return proofs[id];
    }
}
