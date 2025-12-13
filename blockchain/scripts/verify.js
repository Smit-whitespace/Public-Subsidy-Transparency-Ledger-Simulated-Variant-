"use strict";

// Script: verify.js — verify SubsidyProofRegistry on Etherscan
// Usage: npx hardhat run blockchain/scripts/verify.js --network <network> <contractAddress>
// Note: Configure Etherscan API keys in hardhat.config.js before running
// Example: npx hardhat run blockchain/scripts/verify.js --network sepolia 0x1234567890abcdef1234567890abcdef12345678

const hre = require("hardhat");

async function main() {
  console.log("Starting contract verification on Etherscan...\n");
  
  // Get contract address from CLI
  const address = process.argv[2];
  if (!address || address.length < 42) {
    throw new Error("Contract address required\nUsage: npx hardhat run blockchain/scripts/verify.js --network <network> <contractAddress>");
  }
  
  console.log("Contract address:", address);
  
  // Get network info
  const network = await hre.ethers.provider.getNetwork();
  console.log("Network:", network.name, "(chainId:", network.chainId + ")");
  
  // Check if Etherscan configuration exists
  if (!hre.config.etherscan || !hre.config.etherscan.apiKey) {
    console.log("\nWarning: No Etherscan configuration found for this network");
    console.log("Configure etherscan.apiKey in hardhat.config.js");
  }
  
  // Run verification
  console.log("\nVerifying contract on Etherscan...");
  
  try {
    await hre.run("verify:verify", {
      address,
      constructorArguments: []
    });
    
    console.log("\n✓ Verification successful for:", address);
    console.log("View on explorer:", getExplorerUrl(network.chainId, address));
    
  } catch (error) {
    // Handle already verified contracts gracefully
    if (error.message && error.message.toLowerCase().includes("already verified")) {
      console.log("\n✓ Contract already verified:", address);
      console.log("View on explorer:", getExplorerUrl(network.chainId, address));
    } else {
      throw error;
    }
  }
}

function getExplorerUrl(chainId, address) {
  // Map common chain IDs to explorer URLs
  const explorers = {
    1: "https://etherscan.io/address/",
    5: "https://goerli.etherscan.io/address/",
    11155111: "https://sepolia.etherscan.io/address/",
    137: "https://polygonscan.com/address/",
    80001: "https://mumbai.polygonscan.com/address/"
  };
  
  const baseUrl = explorers[chainId];
  return baseUrl ? baseUrl + address : "Unknown network";
}

main().catch((err) => {
  console.error("Verify failed:", err.message || err);
  process.exit(1);
});