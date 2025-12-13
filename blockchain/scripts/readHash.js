"use strict";

// Script: readhash.js — query SubsidyProofRegistry for a proofId from a hash
// Usage: npx hardhat run blockchain/scripts/readhash.js --network <network> <hash> <contractAddress>
// Example: npx hardhat run blockchain/scripts/readhash.js --network localhost 0xabc...def 0x5FbDB2315678afecb367f032d93F642f64180aa3

const hre = require("hardhat");

function normalizeHash(input) {
  // Normalize hash to bytes32 format (0x-prefixed, 66 chars total)
  if (!input) {
    throw new Error("Hash input is required");
  }
  
  let normalized;
  
  if (input.startsWith("0x")) {
    // Already prefixed - validate length
    if (input.length !== 66) {
      throw new Error("Invalid SHA-256 hash format: 0x-prefixed hash must be 66 characters (0x + 64 hex)");
    }
    normalized = input.toLowerCase();
  } else {
    // Raw hex - validate length and add prefix
    if (input.length !== 64) {
      throw new Error("Invalid SHA-256 hash format: raw hex hash must be 64 characters");
    }
    // Validate hex characters
    if (!/^[0-9a-fA-F]+$/.test(input)) {
      throw new Error("Invalid SHA-256 hash format: must contain only hexadecimal characters");
    }
    normalized = "0x" + input.toLowerCase();
  }
  
  return normalized;
}

async function main() {
  console.log("Querying SubsidyProofRegistry for proof by hash...\n");
  
  // Get hash argument from CLI
  const hashArg = process.argv[2];
  if (!hashArg) {
    throw new Error("Hash argument is required\nUsage: npx hardhat run blockchain/scripts/readhash.js --network <network> <hash> <contractAddress>");
  }
  
  // Get contract address from CLI
  const contractAddress = process.argv[3];
  if (!contractAddress) {
    throw new Error("Contract address is required\nUsage: npx hardhat run blockchain/scripts/readhash.js --network <network> <hash> <contractAddress>");
  }
  
  // Normalize and validate hash input
  const normalizedHash = normalizeHash(hashArg);
  console.log("Querying hash:", normalizedHash);
  console.log("Contract address:", contractAddress);
  
  // Get network info
  const network = await hre.ethers.provider.getNetwork();
  console.log("Network:", network.name, "(chainId:", network.chainId + ")\n");
  
  // Load contract factory and attach to deployed instance
  const Registry = await hre.ethers.getContractFactory("SubsidyProofRegistry");
  const registry = Registry.attach(contractAddress);
  
  // Query proof ID by hash
  console.log("Calling getProofIdByHash...");
  const proofId = await registry.getProofIdByHash(normalizedHash);
  
  // Display result
  if (proofId.isZero()) {
    console.log("\n✗ No proof found for hash", normalizedHash);
  } else {
    console.log("\n✓ Proof ID for", normalizedHash + ":", proofId.toString());
    
    // Optionally fetch full proof details
    try {
      const proof = await registry.getProof(proofId);
      console.log("\nProof details:");
      console.log("  ID:", proof.id.toString());
      console.log("  Submitter:", proof.submitter);
      console.log("  Hash:", proof.proofHash);
      console.log("  Timestamp:", new Date(proof.timestamp.toNumber() * 1000).toISOString());
      console.log("  Revoked:", proof.revoked);
    } catch (detailsError) {
      console.log("\nNote: Could not fetch full proof details");
    }
  }
}

main().catch((err) => {
  console.error("Error:", err.message || err);
  process.exit(1);
});