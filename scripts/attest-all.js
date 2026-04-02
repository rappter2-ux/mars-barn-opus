/**
 * Attest ALL frames on the local chain. Picks up where deploy-local.js left off.
 * Reads contract address from data/chain/contract.json.
 */
const { ethers } = require("ethers");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80";

function hashFrame(frameData) {
  const content = {};
  for (const [k, v] of Object.entries(frameData)) {
    if (!["_hash", "_signature", "_engineId"].includes(k)) content[k] = v;
  }
  const keys = Object.keys(content).sort();
  const sorted = {};
  for (const k of keys) sorted[k] = content[k];
  return crypto.createHash("sha256").update(JSON.stringify(sorted), "utf8").digest("hex");
}

async function main() {
  const info = JSON.parse(fs.readFileSync("data/chain/contract.json", "utf8"));
  const provider = new ethers.JsonRpcProvider(info.rpc);
  const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
  const artifact = JSON.parse(
    fs.readFileSync("artifacts/contracts/MarsFrameAttestation.sol/MarsFrameAttestation.json", "utf8")
  );
  const contract = new ethers.Contract(info.address, artifact.abi, wallet);

  // Find where we left off
  const latestSol = Number(await contract.latestSol());
  const startSol = latestSol + 1;

  // Find all frames
  const framesDir = path.join("data", "frames");
  const files = fs.readdirSync(framesDir).filter(f => f.match(/^sol-\d+\.json$/)).sort();
  const maxSol = parseInt(files[files.length - 1].match(/\d+/)[0]);

  if (startSol > maxSol) {
    console.log(`All ${latestSol} frames already attested.`);
    return;
  }

  console.log("════════════════════════════════════════════════════════════");
  console.log(`  ATTESTING FRAMES ${startSol}→${maxSol} ON-CHAIN`);
  console.log(`  (${maxSol - startSol + 1} frames remaining)`);
  console.log("════════════════════════════════════════════════════════════");

  // Get previous frame hash for chain linking
  let prevHash;
  if (latestSol > 0) {
    const prev = await contract.getAttestation(BigInt(latestSol));
    prevHash = prev.frameHash;
  } else {
    prevHash = ethers.ZeroHash;
  }

  let nonce = await provider.getTransactionCount(wallet.address);
  const startTime = Date.now();
  let attested = 0;

  for (let sol = startSol; sol <= maxSol; sol++) {
    const framePath = path.join(framesDir, `sol-${String(sol).padStart(4, "0")}.json`);
    if (!fs.existsSync(framePath)) {
      console.log(`  ⚠ Sol ${sol} missing, skipping`);
      continue;
    }

    const frame = JSON.parse(fs.readFileSync(framePath, "utf8"));
    const hash = hashFrame(frame);
    const hashBytes32 = "0x" + hash;

    const engineId = frame._engineId || "rappter-genesis";
    const sig = frame._signature || "";
    const idHex = ethers.hexlify(ethers.toUtf8Bytes(engineId)).slice(0, 34).padEnd(34, "0");
    const sigHex = ethers.hexlify(ethers.toUtf8Bytes(sig)).slice(0, 50).padEnd(50, "0");

    const tx = await contract.attest(
      BigInt(sol), hashBytes32, prevHash, sigHex, idHex,
      { gasLimit: 200000, nonce: nonce++ }
    );
    await tx.wait();
    prevHash = hashBytes32;
    attested++;

    // Progress every 50 frames
    if (sol % 50 === 0 || sol === maxSol) {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      const rate = (attested / (Date.now() - startTime) * 1000).toFixed(1);
      console.log(`  ✓ Sol ${String(sol).padStart(4)}  (${attested} attested, ${elapsed}s, ${rate}/s)`);
    }
  }

  // Verify full chain
  const total = Number(await contract.totalAttestations());
  const latest = Number(await contract.latestSol());

  console.log("");
  console.log("════════════════════════════════════════════════════════════");
  console.log("  FULL CHAIN ATTESTATION COMPLETE");
  console.log("════════════════════════════════════════════════════════════");
  console.log(`  Contract:       ${info.address}`);
  console.log(`  Total attested: ${total}`);
  console.log(`  Latest sol:     ${latest}`);

  // Spot-check integrity at a few segments
  for (const [a, b] of [[1, 100], [100, 300], [300, 500], [500, Math.min(latest, 729)]]) {
    if (b <= latest) {
      const ok = await contract.verifyChainSegment(BigInt(a), BigInt(b));
      console.log(`  Chain ${a}→${b}:   ${ok ? "✓ INTACT" : "✗ BROKEN"}`);
    }
  }

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log(`\n  Completed in ${elapsed}s`);
  console.log("════════════════════════════════════════════════════════════");
}

main().catch((e) => { console.error("Error:", e.shortMessage || e.message); process.exit(1); });
