const { test, expect } = require('@playwright/test');

test.use({ storageState: 'playwright/.auth/hr.json' });

test('HR can search the candidate directory by skill and minimum experience', async ({ page }) => {
  await page.goto('/talent-search');

  await expect(page.getByRole('heading', { name: 'Talent Search' })).toBeVisible();
  await page.getByLabel('Skill and experience').fill('Python 2+ years');
  await page.getByRole('button', { name: 'Search Talent' }).click();

  await expect(page.getByText('1 candidate(s) found')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'E2E Candidate' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'View profile' })).toBeVisible();
});
