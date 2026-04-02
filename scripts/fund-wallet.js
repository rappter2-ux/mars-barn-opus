/**
 * Playwright script to guide the user through getting Base Sepolia testnet ETH.
 * Opens a faucet, waits for the user to complete the request,
 * then checks the balance.
 */
const { chromium } = require("playwright");
const { ethers } = require("ethers");
const fs = require("fs");
const path = require("path");

async function main() {
  // Load address
  const envPath = path.join(__dirname, "..", ".env.testnet");
  const content = fs.readFileSync(envPath, "utf8");
  const addressMatch = content.match(/DEPLOYER_ADDRESS=(0x[0-9a-fA-F]+)/);
  if (!addressMatch) {
    console.error("No address found. Run: node scripts/generate-wallet.js");
    process.exit(1);
  }
  const address = addressMatch[1];

  console.log("═".repeat(60));
  console.log("Step 1: Get Base Sepolia Testnet ETH");
  console.log("═".repeat(60));
  console.log(`\nYour deployer address: ${address}`);
  console.log("\nOpening faucet in browser...");
  console.log("Paste your address, complete any captcha, and request ETH.");
  console.log("Close the browser window when done.\n");

  // Open browser to faucet
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // Try multiple faucets — some may be down
  const faucets = [
    "https://www.alchemy.com/faucets/base-sepolia",
    "https://faucet.quicknode.com/base/sepolia",
    "https://bwarelabs.com/faucets/base-sepolia",
  ];

  await page.goto(faucets[0]);
  console.log(`Opened: ${faucets[0]}`);
  console.log(`\nAddress to paste: ${address}`);
  console.log("\nAlternate faucets if this one doesn't work:");
  faucets.slice(1).forEach(f => console.log(`  ${f}`));

  // Copy address to clipboard for convenience
  await page.evaluate((addr) => {
    navigator.clipboard.writeText(addr).catch(() => {});
  }, address);
  console.log("\n(Address copied to clipboard)");

  // Wait for user to close the browser
  await new Promise((resolve) => {
    browser.on("disconnected", resolve);
    page.on("close", async () => {
      await browser.close().catch(() => {});
      resolve();
    });
  });

  console.log("\nBrowser closed. Checking balance...");

  // Check balance
  const provider = new ethers.JsonRpcProvider("https://sepolia.base.org");
  let attempts = 0;
  let balance = 0n;

  while (attempts < 12) {
    balance = await provider.getBalance(address);
    if (balance > 0n) break;
    attempts++;
    if (attempts < 12) {
      process.stdout.write(`  Waiting for funds... (attempt ${attempts}/12)\r`);
      await new Promise(r => setTimeout(r, 5000));
    }
  }

  if (balance > 0n) {
    console.log(`\n✓ Balance: ${ethers.formatEther(balance)} ETH`);
    console.log("\nReady to deploy! Run:");
    console.log("  node scripts/deploy.js");
  } else {
    console.log(`\n✗ No funds yet at ${address}`);
    console.log("  Faucets can take a few minutes. Try again or use a different faucet.");
    console.log("\n  Check manually:");
    console.log(`  https://sepolia.basescan.org/address/${address}`);
  }

  console.log("\n" + "═".repeat(60));
}

main().catch((e) => { console.error(e); process.exit(1); });
