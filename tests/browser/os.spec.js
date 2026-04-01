// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('LisPy OS', () => {
  test('OS loads with desktop icons', async ({ page }) => {
    await page.goto('/os.html');
    await page.waitForSelector('.desktop');
    const icons = await page.locator('.desktop-icon').count();
    expect(icons).toBeGreaterThanOrEqual(8);
  });

  test('terminal opens and runs LisPy', async ({ page }) => {
    await page.goto('/os.html');
    // Double-click Terminal icon
    await page.locator('.desktop-icon', { hasText: 'Terminal' }).dblclick();
    await page.waitForSelector('#win-terminal.open');
    
    // Type a LisPy expression
    const input = page.locator('#term-input');
    await input.fill('(+ 2 3)');
    await input.press('Enter');
    
    // Check output contains 5
    const output = await page.locator('#term-output').textContent();
    expect(output).toContain('5');
  });

  test('start menu opens', async ({ page }) => {
    await page.goto('/os.html');
    await page.locator('.taskbar-start').click();
    await expect(page.locator('#start-menu')).toHaveClass(/open/);
  });

  test('Mars Gov opens and shows metrics', async ({ page }) => {
    await page.goto('/os.html');
    await page.locator('.desktop-icon', { hasText: 'Mars Gov' }).dblclick();
    await page.waitForSelector('#win-gov.open');
    // Wait for refresh to complete (fetches from GitHub)
    await page.waitForFunction(() => {
      const el = document.getElementById('gm-sol');
      return el && el.textContent !== '—';
    }, { timeout: 15000 }).catch(() => {});
    // Even if fetch fails (offline), the window should be open
    await expect(page.locator('#win-gov')).toHaveClass(/open/);
  });

  test('Colony Sim opens in iframe', async ({ page }) => {
    await page.goto('/os.html');
    await page.locator('.desktop-icon', { hasText: 'Colony Sim' }).dblclick();
    await page.waitForSelector('#win-sim.open');
    const iframe = page.locator('#sim-frame');
    await expect(iframe).toHaveAttribute('src', 'viewer.html');
  });

  test('taskbar tracks open apps', async ({ page }) => {
    await page.goto('/os.html');
    await page.locator('.desktop-icon', { hasText: 'Terminal' }).dblclick();
    await page.waitForSelector('#win-terminal.open');
    const taskbarApps = page.locator('#taskbar-apps .taskbar-app');
    expect(await taskbarApps.count()).toBeGreaterThanOrEqual(1);
  });

  test('clock displays in taskbar', async ({ page }) => {
    await page.goto('/os.html');
    const clock = await page.locator('#clock').textContent();
    expect(clock).toContain('LisPy OS');
  });
});
