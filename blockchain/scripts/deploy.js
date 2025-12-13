"use strict";

// Hardhat deployment script for SubsidyProofRegistry
// Configure networks and Etherscan API keys in hardhat.config.js before deploying

const hre = require("hardhat");

// Sleep utility for verification delay
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function main() {
  console.log("Starting SubsidyProofRegistry deployment...");
  
  // Get deployer account
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with account:", deployer.address);
  
  // Check deployer balance
  const balance = await deployer.getBalance();
  console.log("Account balance:", hre.ethers.utils.formatEther(balance), "ETH");
  
  // Load contract factory
  console.log("\nLoading SubsidyProofRegistry contract factory...");
  const Registry = await hre.ethers.getContractFactory("SubsidyProofRegistry");
  
  // Deploy contract
  console.log("Deploying contract...");
  const registry = await Registry.deploy();
  await registry.deployed();
  
  console.log("\n✓ SubsidyProofRegistry deployed to:", registry.address);
  
  // Verify initial state
  const totalProofs = await registry.totalProofs();
  console.log("Initial totalProofs:", totalProofs.toString());
  
  const owner = await registry.owner();
  console.log("Contract owner:", owner);
  
  // Optional contract verification on Etherscan
  // Only run on non-local networks if Etherscan config exists
  try {
    const network = await hre.ethers.provider.getNetwork();
    const chainId = network.chainId;
    
    // Skip verification on local/hardhat network (chainId 31337)
    if (chainId !== 31337 && hre.config.etherscan && hre.config.etherscan.apiKey) {
      console.log("\nWaiting 60 seconds before Etherscan verification...");
      await sleep(60000);
      
      console.log("Verifying contract on Etherscan...");
      await hre.run("verify:verify", {
        address: registry.address,
        constructorArguments: []
      });
      console.log("✓ Contract verified on Etherscan");
    }
  } catch (verifyError) {
    console.log("\nNote: Etherscan verification skipped or failed");
    console.log("You can verify manually later with:");
    console.log(`npx hardhat verify --network <network> ${registry.address}`);
  }
  
  console.log("\n✓ Deployment complete!");
  console.log("\nContract address:", registry.address);
  console.log("Save this address to your backend configuration (BLOCKCHAIN_CONTRACT_ADDRESS)");
}

main().catch((err) => {
  console.error("Deployment failed:", err);
  process.exit(1);
});