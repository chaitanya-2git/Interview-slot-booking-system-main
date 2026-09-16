const { test: setup, expect } = require('@playwright/test');
const fs = require('fs');

const authDirectory = 'playwright/.auth';
const credentials = {
  hr: {
    email: process.env.E2E_HR_EMAIL || 'e2e-hr@example.test',
    password: process.env.E2E_HR_PASSWORD || 'E2eHrPassword!'
  },
  candidate: {
    email: process.env.E2E_CANDIDATE_EMAIL || 'e2e-candidate@example.test',
    password: process.env.E2E_CANDIDATE_PASSWORD || 'E2eCandidatePassword!'
  }
};

async function signIn(page, account) {
  await page.goto('/login');
  await page.getByLabel('Email address').fill(account.email);
  await page.getByLabel('Password').fill(account.password);
  await page.getByRole('button', { name: 'Sign in to portal' }).click();
}

setup.beforeAll(() => fs.mkdirSync(authDirectory, { recursive: true }));

setup('sign in HR and save session state', async ({ page }) => {
  await signIn(page, credentials.hr);
  await expect(page).toHaveURL(/\/hr-dashboard$/);
  await expect(page.getByText('Good morning, E2E HR')).toBeVisible();
  await page.context().storageState({ path: `${authDirectory}/hr.json` });
});

setup('sign in candidate and save session state', async ({ browser }) => {
  const context = await browser.newContext();
  const page = await context.newPage();
  await signIn(page, credentials.candidate);
  await expect(page).toHaveURL(/\/candidate-dashboard$/);
  await expect(page.getByText('Welcome back, E2E Candidate')).toBeVisible();
  await context.storageState({ path: `${authDirectory}/candidate.json` });
  await context.close();
});
