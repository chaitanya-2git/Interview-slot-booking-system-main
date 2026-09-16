const { test, expect } = require('@playwright/test');

test.use({ storageState: 'playwright/.auth/candidate.json' });

test('candidate can save professional onboarding details', async ({ page }) => {
  await page.goto('/candidate-profile');

  await expect(page.getByRole('heading', { name: 'Upload and parse your resume' })).toBeVisible();
  await page.getByLabel('Resume (PDF, DOC, or DOCX)').setInputFiles('e2e/fixtures/sample-candidate-resume.docx');
  await page.getByRole('button', { name: 'Parse resume' }).click();
  await expect(page.getByRole('heading', { name: 'Complete the essentials' })).toBeVisible();
  await expect(page.getByLabel('Phone number')).toHaveValue('+91 9000000000');
  await page.getByLabel('Phone number').fill('+91 9000000000');
  await page.getByLabel('Current location').fill('Hyderabad');
  await page.getByLabel('Profile photo Optional').setInputFiles('e2e/fixtures/sample-profile-photo.png');
  await page.getByLabel('LinkedIn URL').fill('https://www.linkedin.com/in/e2e-candidate');
  await page.getByRole('button', { name: 'Continue' }).click();

  await expect(page.getByRole('heading', { name: 'Review your experience' })).toBeVisible();
  await page.getByLabel('Current company').fill('BluJay Technologies');
  await page.getByLabel('Designation').fill('Software Engineer');
  await page.getByLabel('Experience (years)').fill('2');
  await page.getByLabel('Notice period').fill('30 days');
  await page.getByLabel('Skills').fill('Python, Flask, SQL');
  await page.getByLabel('Education').fill('B.Tech Computer Science');
  await page.getByRole('button', { name: 'Save Profile' }).click();

  await expect(page).toHaveURL(/\/candidate-dashboard$/);
  await expect(page.getByText('Profile saved successfully. Your candidate profile is ready for review.')).toBeVisible();
  await expect(page.getByAltText('E2E Candidate profile photo')).toBeVisible();
});

