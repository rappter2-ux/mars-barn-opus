// @ts-check
const { test, expect } = require('@playwright/test');

// ══════════════════════════════════════════════════════════════
// HALL OF FAME — Run every LisPy program and verify it succeeds
// ══════════════════════════════════════════════════════════════

test.describe('LisPy Hall of Fame', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/hall-of-fame.html');
    await page.waitForSelector('#programs');
  });

  test('page loads with all 10 programs', async ({ page }) => {
    const programs = await page.locator('.program').count();
    expect(programs).toBe(10);
  });

  // Test each program individually
  const programNames = [
    'The Mandelbrot Set',
    'Self-Rewriting Governor',
    'Fibonacci Spiral Art',
    'Colony Doom Clock',
    'Market Sentiment Engine',
    'Cellular Automaton (Rule 110)',
    'Prime Number Sieve',
    'Colony Orchestra',
    'Recursive Fractal Tree',
    'Monte Carlo Pi Estimator',
  ];

  for (let i = 0; i < programNames.length; i++) {
    test(`Program ${i + 1}: ${programNames[i]} runs without error`, async ({ page }) => {
      // Click the RUN button
      const runBtn = page.locator(`#run-${i}`);
      await runBtn.click();

      // Wait for execution to complete (button text changes back to ▶ RUN)
      await expect(runBtn).toHaveText('▶ RUN', { timeout: 15000 });

      // Check output area doesn't contain ERROR
      const output = await page.locator(`#output-${i}`).textContent();
      expect(output).not.toContain('ERROR');
      expect(output.length).toBeGreaterThan(10);

      // Verify step counter updated
      const steps = await page.locator('#vm-steps').textContent();
      expect(steps).not.toBe('0 steps');
    });
  }

  test('copy button exists for each program', async ({ page }) => {
    // Open first program
    await page.locator('#prog-0 .program-header').click();
    const copyBtn = page.locator('#prog-0 .copy-btn');
    await expect(copyBtn).toBeVisible();
  });
});
