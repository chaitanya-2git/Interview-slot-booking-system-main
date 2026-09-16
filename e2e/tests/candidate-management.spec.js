const { test, expect } = require('@playwright/test');

test('HR can create, search for, and permanently delete a candidate', async ({ page }, testInfo) => {
  const email = `playwright-candidate-${testInfo.parallelIndex}@example.test`;

  await page.goto('/hr-dashboard');
  await page.getByRole('link', { name: 'Candidates' }).click();
  await expect(page.getByRole('heading', { name: 'Manage Candidates' })).toBeVisible();

  await page.getByRole('link', { name: 'Add Candidate' }).click();
  await expect(page.getByText('Create Candidate')).toBeVisible();
  await page.getByLabel('Full Name').fill('Playwright Candidate');
  await page.getByLabel('Email Address').fill(email);
  await page.getByLabel('Password', { exact: false }).fill('CandidatePassword!');
  await page.getByRole('button', { name: 'Create Account' }).click();
  await expect(page.getByText(/Candidate created successfully/)).toBeVisible();

  await page.getByRole('searchbox', { name: 'Search candidates by name, email, or skills' }).fill(email);
  await expect(page.getByText(email)).toBeVisible();
  const candidateCard = page.locator('article').filter({ has: page.getByRole('heading', { name: 'Playwright Candidate', exact: true }) });
  await candidateCard.getByRole('link', { name: 'View details' }).click();
  await expect(page.getByRole('heading', { name: 'Playwright Candidate' })).toBeVisible();
  await expect(page.getByText('Professional overview')).toBeVisible();
  await expect(page.getByText('No resume uploaded')).toBeVisible();
  await page.getByRole('link', { name: 'Candidates' }).click();
  await page.getByRole('searchbox', { name: 'Search candidates by name, email, or skills' }).fill(email);
  await candidateCard.getByRole('link', { name: 'Delete candidate' }).click();
  await expect(page.getByText('Delete candidate?', { exact: true })).toBeVisible();
  await page.getByLabel("Type the candidate's email to confirm").fill(email);
  await page.getByRole('button', { name: 'Delete permanently' }).click();
  await expect(page.getByText(/Candidate and related records deleted successfully/)).toBeVisible();
  await expect(page.getByText(email)).not.toBeVisible();
});
