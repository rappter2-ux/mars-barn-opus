// @ts-check
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests/browser',
  timeout: 30000,
  use: {
    baseURL: 'http://localhost:8787',
    headless: true,
  },
  webServer: {
    command: 'python3 -m http.server 8787 --directory docs',
    port: 8787,
    reuseExistingServer: true,
  },
});
