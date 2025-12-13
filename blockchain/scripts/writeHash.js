"use strict";

// Script: writeHash.js — register a SHA-256 proof in SubsidyProofRegistry
// Usage: npx hardhat run blockchain/scripts/writeHash.js --network <network> <sha256> <contractAddress>
// Example: npx hardhat run blockchain/scripts/writeHash.js --network localhost 0xabc...def 0x5FbDB2315678afecb367f032d93F642f64180aa3
// Note: SHA-256 hash must be computed off-chain (32 bytes). Contract must be already deployed.

const hre = require("hardhat");

function normalizeHash(input) {
  if (!input) {
    throw new Error("Hash input is required");
  }
  
  let normalized = input.toLowerCase();
  
  // Add 0x prefix if missing
  if (!normalized.startsWith("0x")) {
    normalized = "0x" + normalized;
  }
  
  // Validate length (must be 66 chars: 0x + 64 hex)
  if (normalized.length !== 66) {
    throw new Error("Invalid SHA-256 hash format: must be 64 hex characters (with or without 0x prefix)");
  }
  
  // Validate hex characters
  if (!/^0x[0-9a-f]{64}$/.test(normalized)) {
    throw new Error("Invalid SHA-256 hash format: must contain only hexadecimal characters");
  }
  
  return normalized;
}

async function main() {
  console.log("Registering SHA-256 proof in SubsidyProofRegistry...\n");
  
  // Read CLI arguments
  const hashArg = process.argv[2];
  const contractAddress = process.argv[3];
  
  if (!hashArg) {
    throw new Error("Hash argument is required\nUsage: npx hardhat run blockchain/scripts/writeHash.js --network <network> <sha256> <contractAddress>");
  }
  
  if (!contractAddress) {
    throw new Error("Contract address is required\nUsage: npx hardhat run blockchain/scripts/writeHash.js --network <network> <sha256> <contractAddress>");
  }
  
  // Normalize and validate hash
  const proofHash = normalizeHash(hashArg);
  console.log("Proof hash:", proofHash);
  console.log("Contract address:", contractAddress);
  
  // Get network info
  const network = await hre.ethers.provider.getNetwork();
  console.log("Network:", network.name, "(chainId:", network.chainId + ")");
  
  // Get signer
  const [signer] = await hre.ethers.getSigners();
  console.log("Signer:", signer.address);
  
  const balance = await signer.getBalance();
  console.log("Balance:", hre.ethers.utils.formatEther(balance), "ETH\n");
  
  // Attach to deployed contract
  const Registry = await hre.ethers.getContractFactory("SubsidyProofRegistry");
  const registry = Registry.attach(contractAddress);
  
  // Check if hash is already registered
  console.log("Checking if hash is already registered...");
  const existingId = await registry.getProofIdByHash(proofHash);
  if (!existingId.isZero()) {
    console.log("\n✗ Hash already registered with proof ID:", existingId.toString());
    console.log("Use readhash.js to view details");
    return;
  }
  
  // Send transaction to register proof
  console.log("Sending transaction to register proof...");
  const tx = await registry.registerProof(proofHash);
  console.log("Transaction sent:", tx.hash);
  console.log("Waiting for confirmation...\n");
  
  // Wait for transaction confirmation
  const receipt = await tx.wait();
  console.log("Transaction confirmed in block:", receipt.blockNumber);
  console.log("Gas used:", receipt.gasUsed.toString());
  
  // Extract proof ID from event logs
  let proofId = null;
  for (const log of receipt.logs) {
    if (log.address.toLowerCase() === contractAddress.toLowerCase()) {
      try {
        const parsed = registry.interface.parseLog(log);
        if (parsed.name === "ProofRegistered") {
          proofId = parsed.args.proofId;
          break;
        }
      } catch (_) {
        // Skip unparseable logs
      }
    }
  }
  
  // Display result
  if (proofId) {
    console.log("\n✓ Registered proof. ID:", proofId.toString());
    console.log("Hash:", proofHash);
    console.log("Submitter:", signer.address);
  } else {
    console.log("\n✓ Registered, but could not parse proofId from logs");
    console.log("Query with: npx hardhat run blockchain/scripts/readhash.js --network", network.name, proofHash, contractAddress);
  }
}

main().catch((err) => {
  console.error("Error:", err.message || err);
  process.exit(1);
});