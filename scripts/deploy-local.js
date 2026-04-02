/**
 * Deploy MarsFrameAttestation locally and attest the first 10 frames.
 * Proves the full pipeline: deploy → attest → verify → chain integrity.
 */
const { ethers } = require("ethers");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80";
const RPC = "http://127.0.0.1:8545";

function hashFrame(frameData) {
  const content = {};
  for (const [k, v] of Object.entries(frameData)) {
    if (!["_hash", "_signature", "_engineId"].includes(k)) content[k] = v;
  }
  const keys = Object.keys(content).sort();
  const sorted = {};
  for (const k of keys) sorted[k] = content[k];
  const canonical = JSON.stringify(sorted);
  return crypto.createHash("sha256").update(canonical, "utf8").digest("hex");
}

async function main() {
  const provider = new ethers.JsonRpcProvider(RPC);
  const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
  const artifact = JSON.parse(
    fs.readFileSync("artifacts/contracts/MarsFrameAttestation.sol/MarsFrameAttestation.json", "utf8")
  );

  // ─── Deploy ────────────────────────────────────────────────────────
  console.log("════════════════════════════════════════════════════════════");
  console.log("  DEPLOYING MarsFrameAttestation (local blockchain)");
  console.log("════════════════════════════════════════════════════════════");
  console.log(`  Deployer: ${wallet.address}`);

  const factory = new ethers.ContractFactory(artifact.abi, artifact.bytecode, wallet);
  const deployTx = await factory.deploy();
  await deployTx.waitForDeployment();
  const address = await deployTx.getAddress();
  console.log(`  ✓ Deployed: ${address}\n`);

  // Save contract info
  const info = {
    address,
    network: "localhost",
    chainId: 31337,
    rpc: RPC,
    deployer: wallet.address,
    deployedAt: new Date().toISOString(),
  };
  fs.writeFileSync(
    path.join("data", "chain", "contract.json"),
    JSON.stringify(info, null, 2) + "\n"
  );
  console.log("  ✓ Saved to data/chain/contract.json\n");

  // ─── Attest frames ────────────────────────────────────────────────
  console.log("════════════════════════════════════════════════════════════");
  console.log("  ATTESTING FRAMES 1-10 ON-CHAIN");
  console.log("════════════════════════════════════════════════════════════");

  // Connect to the deployed contract WITH the wallet (for signing)
  // Force nonce refresh after deploy
  const nonce = await provider.getTransactionCount(wallet.address);
  const contract = new ethers.Contract(address, artifact.abi, wallet);
  let prevHash = ethers.ZeroHash; // bytes32 of zeros for genesis
  let txNonce = nonce;

  for (let sol = 1; sol <= 10; sol++) {
    const framePath = path.join("data", "frames", `sol-${String(sol).padStart(4, "0")}.json`);
    const frame = JSON.parse(fs.readFileSync(framePath, "utf8"));
    const hash = hashFrame(frame);
    const hashBytes32 = "0x" + hash;

    // Encode engine ID and signature as fixed-size bytes
    const engineId = frame._engineId || "rappter-genesis";
    const sig = frame._signature || "";
    const idHex = ethers.hexlify(ethers.toUtf8Bytes(engineId)).slice(0, 34).padEnd(34, "0"); // bytes16
    const sigHex = ethers.hexlify(ethers.toUtf8Bytes(sig)).slice(0, 50).padEnd(50, "0"); // bytes24

    // Send attest transaction
    const tx = await contract.attest(
      BigInt(sol),
      hashBytes32,
      prevHash,
      sigHex,
      idHex,
      { gasLimit: 200000, nonce: txNonce++ }
    );
    const receipt = await tx.wait();

    // Verify on-chain
    const [valid, attestedAt] = await contract.verify(BigInt(sol), hashBytes32);
    const blockNum = receipt.blockNumber;
    console.log(
      `  ✓ Sol ${String(sol).padStart(3)}  hash=${hash.slice(0, 16)}  block=${blockNum}  verified=${valid}`
    );

    prevHash = hashBytes32;
  }

  // ─── Verify chain integrity ────────────────────────────────────────
  console.log("");
  console.log("════════════════════════════════════════════════════════════");
  const intact = await contract.verifyChainSegment(1n, 10n);
  const latest = await contract.latestSol();
  const total = await contract.totalAttestations();

  console.log("  🌍 ←→ ⛓️  ←→ 🔴   THE BRIDGE IS LIVE");
  console.log("════════════════════════════════════════════════════════════");
  console.log(`  Contract:       ${address}`);
  console.log(`  Attested sols:  ${total}`);
  console.log(`  Latest sol:     ${latest}`);
  console.log(`  Chain 1→10:     ${intact ? "✓ INTACT" : "✗ BROKEN"}`);
  console.log("");
  console.log("  The virtual colony is cryptographically bound to a ledger.");
  console.log("  The chain witnesses the frames. Trust is math, not servers.");
  console.log("════════════════════════════════════════════════════════════");
}

main().catch((e) => {
  console.error("Error:", e.shortMessage || e.message);
  process.exit(1);
});
