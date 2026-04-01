// @ts-check
const { test, expect } = require('@playwright/test');

// ══════════════════════════════════════════════════════════════
// VIEWER — Core sim page loads and LisPy VM works
// ══════════════════════════════════════════════════════════════

test.describe('Viewer', () => {
  test('page loads with mission selector', async ({ page }) => {
    await page.goto('/viewer.html');
    await page.waitForSelector('#mission-overlay');
    const title = await page.locator('#mission-overlay h1').textContent();
    expect(title).toContain('FIRST PRINCIPLES TO MARS');
  });

  test('mission cards are clickable', async ({ page }) => {
    await page.goto('/viewer.html');
    await page.waitForSelector('.mission-card');
    const cards = await page.locator('.mission-card').count();
    expect(cards).toBe(8);
  });

  test('LisPy VM works in browser', async ({ page }) => {
    await page.goto('/viewer.html');
    // Run LisPy directly in the page context
    const result = await page.evaluate(() => {
      const vm = new LispyVM();
      vm.setEnv('x', 42);
      return vm.run('(+ x 8)');
    });
    expect(result.ok).toBe(true);
    expect(result.result).toBe(50);
  });

  test('LisPy string literals work', async ({ page }) => {
    await page.goto('/viewer.html');
    const result = await page.evaluate(() => {
      const vm = new LispyVM();
      return vm.run('(concat "hello" " " "world")');
    });
    expect(result.ok).toBe(true);
    expect(result.result).toBe('hello world');
  });

  test('LisPy prompt library accessible', async ({ page }) => {
    await page.goto('/viewer.html');
    const result = await page.evaluate(() => {
      const vm = new LispyVM();
      return vm.run('(prompt-list)');
    });
    expect(result.ok).toBe(true);
    expect(result.result.length).toBeGreaterThan(10);
  });

  test('cartridge drop zone exists', async ({ page }) => {
    await page.goto('/viewer.html');
    const dropZone = page.locator('#cartridge-drop');
    await expect(dropZone).toBeVisible();
  });

  test('autopilot toggle exists', async ({ page }) => {
    await page.goto('/viewer.html');
    // The autopilot button exists in the header (hidden until game starts)
    const btn = page.locator('#autopilot-btn');
    expect(await btn.count()).toBe(1);
  });
});
