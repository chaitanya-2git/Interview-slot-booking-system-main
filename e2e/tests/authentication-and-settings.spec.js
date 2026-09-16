const { test, expect } = require('@playwright/test');

test.describe('Authentication and settings', () => {
  test('homepage redirects to the sign-in page and rejects invalid credentials', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/');
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByText('Welcome back', { exact: true })).toBeVisible();

    await page.getByLabel('Email address').fill('unknown@example.test');
    await page.getByLabel('Password').fill('not-a-valid-password');
    await page.getByRole('button', { name: 'Sign in to portal' }).click();
    await expect(page.getByText(/Invalid email or password or account is inactive/)).toBeVisible();
  });

  test('HR can use navigation, receive password validation, and save preferences', async ({ page }) => {
    await page.goto('/hr-dashboard');
    await expect(page.getByText('Good morning, E2E HR')).toBeVisible();

    await page.getByRole('link', { name: 'Settings' }).click();
    await expect(page.getByRole('heading', { name: 'Account Settings' })).toBeVisible();

    await page.getByLabel('Current password', { exact: true }).fill('E2eHrPassword!');
    await page.getByLabel('New password', { exact: true }).fill('DifferentPassword!');
    await page.getByLabel('Confirm new password', { exact: true }).fill('MismatchPassword!');
    await page.getByRole('button', { name: 'Update password' }).click();
    await expect(page.getByText('The new passwords do not match.')).toBeVisible();

    await page.getByLabel('Larger text').check();
    await page.getByLabel('Reduce motion').check();
    await page.getByRole('button', { name: 'Save preferences' }).click();
    await expect(page.getByText('Settings saved successfully.')).toBeVisible();
    await expect(page.locator('body')).toHaveClass(/pref-larger-text/);
    await expect(page.locator('body')).toHaveClass(/pref-reduce-motion/);
  });

  test('logout clears the authenticated session', async ({ page }) => {
    await page.goto('/hr-dashboard');
    await page.getByTitle('Sign out').click();
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByText('You have been logged out.')).toBeVisible();
  });
});
