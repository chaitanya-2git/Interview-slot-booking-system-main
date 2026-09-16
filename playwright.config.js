const { defineConfig, devices } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const localTestPython = path.join(
  process.cwd(),
  '.playwright-python',
  'Scripts',
  'python.exe'
);
const python = process.env.PYTHON || (fs.existsSync(localTestPython) ? localTestPython : 'python');
const installedChrome = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

module.exports = defineConfig({
  testDir: './e2e/tests',
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: [['html', { open: 'never' }], ['list']],
  use: {
    baseURL: 'http://127.0.0.1:5000',
    // Prefer the locally installed Chrome when available. Playwright falls back
    // to its bundled Chromium in CI and on other developer machines.
    ...(fs.existsSync(installedChrome)
      ? { launchOptions: { executablePath: installedChrome } }
      : {}),
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure'
  },
  projects: [
    {
      name: 'setup',
      testMatch: /.*\.setup\.js/
    },
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/hr.json'
      },
      dependencies: ['setup'],
      testIgnore: /.*\.setup\.js/
    }
  ],
  webServer: {
    command: `"${python}" e2e/server.py`,
    url: 'http://127.0.0.1:5000/login',
    reuseExistingServer: false,
    timeout: 60_000
  }
});
