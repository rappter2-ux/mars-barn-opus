/**
 * Generate a fresh deployer wallet for Base Sepolia testnet.
 * Prints the address (for faucet) and saves key to .env.testnet (gitignored).
 * 
 * Usage: node scripts/generate-wallet.js
 */
const { ethers } = require("ethers");
const fs = require("fs");
const path = require("path");

const wallet = ethers.Wallet.createRandom();

console.log("═".repeat(60));
console.log("Mars Frame Attestation — Deployer Wallet");
console.log("═".repeat(60));
console.log("");
console.log(`Address:     ${wallet.address}`);
console.log(`Private Key: ${wallet.privateKey}`);
console.log("");
console.log("Next steps:");
console.log("  1. Get testnet ETH from a faucet for the address above");
console.log("  2. Deploy: node scripts/deploy.js");
console.log("");
console.log("═".repeat(60));

// Save to gitignored file
const envPath = path.join(__dirname, "..", ".env.testnet");
fs.writeFileSync(envPath, [
  `DEPLOYER_PRIVATE_KEY=${wallet.privateKey}`,
  `DEPLOYER_ADDRESS=${wallet.address}`,
  "",
].join("\n"));
console.log(`\nSaved to .env.testnet (gitignored)`);
