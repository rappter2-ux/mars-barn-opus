/**
 * Deploy MarsFrameAttestation to Base Sepolia (testnet) or Base Mainnet.
 * 
 * Usage:
 *   node scripts/deploy.js                  # Base Sepolia (default)
 *   node scripts/deploy.js --mainnet        # Base Mainnet
 * 
 * Reads DEPLOYER_PRIVATE_KEY from .env.testnet or environment.
 * Writes contract address to data/chain/contract.json after deployment.
 */
const { ethers } = require("ethers");
const fs = require("fs");
const path = require("path");

const NETWORKS = {
  sepolia: {
    name: "Base Sepolia",
    rpc: "https://sepolia.base.org",
    chainId: 84532,
    explorer: "https://sepolia.basescan.org",
  },
  mainnet: {
    name: "Base Mainnet",
    rpc: "https://mainnet.base.org",
    chainId: 8453,
    explorer: "https://basescan.org",
  },
};

async function main() {
  // Pick network
  const isMainnet = process.argv.includes("--mainnet");
  const net = isMainnet ? NETWORKS.mainnet : NETWORKS.sepolia;

  // Load private key
  let privateKey = process.env.DEPLOYER_PRIVATE_KEY;
  if (!privateKey) {
    const envPath = path.join(__dirname, "..", ".env.testnet");
    if (fs.existsSync(envPath)) {
      const content = fs.readFileSync(envPath, "utf8");
      const match = content.match(/DEPLOYER_PRIVATE_KEY=(0x[0-9a-fA-F]+)/);
      if (match) privateKey = match[1];
    }
  }
  if (!privateKey) {
    console.error("No private key. Run: node scripts/generate-wallet.js");
    process.exit(1);
  }

  // Load compiled contract
  const artifactPath = path.join(__dirname, "..", "artifacts", "contracts",
    "MarsFrameAttestation.sol", "MarsFrameAttestation.json");
  if (!fs.existsSync(artifactPath)) {
    console.error("Contract not compiled. Run: npx hardhat compile");
    process.exit(1);
  }
  const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));

  // Connect
  const provider = new ethers.JsonRpcProvider(net.rpc);
  const wallet = new ethers.Wallet(privateKey, provider);

  console.log("═".repeat(60));
  console.log("Mars Frame Attestation — Contract Deployment");
  console.log("═".repeat(60));
  console.log(`Network:  ${net.name} (chain ID ${net.chainId})`);
  console.log(`Deployer: ${wallet.address}`);

  const balance = await provider.getBalance(wallet.address);
  console.log(`Balance:  ${ethers.formatEther(balance)} ETH`);

  if (balance === 0n) {
    console.error("\n✗ No ETH. Get testnet ETH first:");
    console.error(`  Address: ${wallet.address}`);
    console.error("  Faucet:  https://www.alchemy.com/faucets/base-sepolia");
    process.exit(1);
  }

  // Deploy
  console.log("\nDeploying MarsFrameAttestation...");
  const factory = new ethers.ContractFactory(artifact.abi, artifact.bytecode, wallet);
  const contract = await factory.deploy();
  console.log(`Tx sent: ${contract.deploymentTransaction().hash}`);
  console.log("Waiting for confirmation...");
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log(`\n✓ Deployed at: ${address}`);
  console.log(`  Explorer:    ${net.explorer}/address/${address}`);

  // Save contract info
  const contractInfo = {
    address,
    network: net.name,
    chainId: net.chainId,
    deployer: wallet.address,
    txHash: contract.deploymentTransaction().hash,
    deployedAt: new Date().toISOString(),
    explorer: `${net.explorer}/address/${address}`,
  };

  const contractPath = path.join(__dirname, "..", "data", "chain", "contract.json");
  fs.writeFileSync(contractPath, JSON.stringify(contractInfo, null, 2) + "\n");
  console.log("✓ Saved to data/chain/contract.json");

  // Update engine manifest
  const manifestPath = path.join(__dirname, "..", "data", "engine-manifest.json");
  if (fs.existsSync(manifestPath)) {
    const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
    if (manifest.attestation) {
      manifest.attestation.contract_address = address;
      manifest.attestation.chain_id = net.chainId;
      manifest.attestation.deployed_at = new Date().toISOString();
      fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + "\n");
      console.log("✓ Engine manifest updated");
    }
  }

  console.log("\n" + "═".repeat(60));
  console.log("The bridge is live. The chain witnesses the frames.");
  console.log("═".repeat(60));
}

main().catch((e) => { console.error(e); process.exit(1); });

