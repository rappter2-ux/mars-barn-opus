// @ts-check
const { test, expect } = require('@playwright/test');

// ══════════════════════════════════════════════════════════════
// SIMHUB — Leaderboard page loads and functions
// ══════════════════════════════════════════════════════════════

test.describe('SimHub', () => {
  test('page loads with tabs', async ({ page }) => {
    await page.goto('/simhub.html');
    await page.waitForSelector('.tabs');
    const tabs = await page.locator('.tab').count();
    expect(tabs).toBe(5);
  });

  test('frame feed tab shows timeline', async ({ page }) => {
    await page.goto('/simhub.html');
    await page.locator('.tab', { hasText: 'FRAME FEED' }).click();
    const timeline = page.locator('#frame-timeline');
    await expect(timeline).toBeVisible();
  });

  test('upload tab has drop zone', async ({ page }) => {
    await page.goto('/simhub.html');
    await page.locator('.tab', { hasText: 'UPLOAD' }).click();
    const dropZone = page.locator('#upload-drop');
    await expect(dropZone).toBeVisible();
  });
});

// ══════════════════════════════════════════════════════════════
// CONTROL — Mission control loads
// ══════════════════════════════════════════════════════════════

test.describe('Mission Control', () => {
  test('page loads with grid layout', async ({ page }) => {
    await page.goto('/control.html');
    await page.waitForSelector('.mc-grid');
    const header = await page.locator('.mc-header h1').textContent();
    expect(header).toContain('MISSION CONTROL');
  });

  test('protocol buttons exist', async ({ page }) => {
    await page.goto('/control.html');
    const getState = page.locator('button', { hasText: 'GET STATE' });
    await expect(getState).toBeVisible();
  });

  test('wallet section exists', async ({ page }) => {
    await page.goto('/control.html');
    const walletBtn = page.locator('button', { hasText: 'GET WALLETS' });
    await expect(walletBtn).toBeVisible();
  });
});

// ══════════════════════════════════════════════════════════════
// PATTERNS — Pattern library loads
// ══════════════════════════════════════════════════════════════

test.describe('Pattern Library', () => {
  test('page loads with 13 patterns', async ({ page }) => {
    await page.goto('/patterns.html');
    const patterns = await page.locator('.pattern').count();
    expect(patterns).toBe(13);
  });

  test('TOC nav links exist', async ({ page }) => {
    await page.goto('/patterns.html');
    const navLinks = await page.locator('#toc a').count();
    expect(navLinks).toBe(13);
  });
});

// ══════════════════════════════════════════════════════════════
// BLOG — Blog index and posts load
// ══════════════════════════════════════════════════════════════

test.describe('Blog', () => {
  test('index loads with posts', async ({ page }) => {
    await page.goto('/blog/');
    const posts = await page.locator('.post-card').count();
    expect(posts).toBeGreaterThanOrEqual(7);
  });

  const blogPosts = [
    '/blog/the-1to1-thesis.html',
    '/blog/portal-pattern.html',
    '/blog/emergent-tooling.html',
    '/blog/echo-frames.html',
    '/blog/nervous-system.html',
    '/blog/sim-cartridges.html',
    '/blog/competitive-frames.html',
  ];

  for (const post of blogPosts) {
    test(`blog post loads: ${post}`, async ({ page }) => {
      await page.goto(post);
      const h1 = await page.locator('h1').textContent();
      expect(h1.length).toBeGreaterThan(5);
    });
  }
});
