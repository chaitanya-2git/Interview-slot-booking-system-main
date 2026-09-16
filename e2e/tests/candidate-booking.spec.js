const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

test.use({ storageState: 'playwright/.auth/candidate.json' });

test('candidate can load slots, book an interview, and cancel the booking', async ({ page }) => {
  // The production template loads this exact Bootstrap bundle from jsDelivr.
  // Load its official local package before the page so the real modal remains
  // reliable when CI or a local network blocks the public CDN.
  await page.addInitScript({
    content: fs.readFileSync(
      path.join(path.dirname(require.resolve('bootstrap')), 'bootstrap.bundle.min.js'),
      'utf8'
    )
  });

  await page.goto('/candidate-dashboard');
  await expect(page.getByText('Welcome back, E2E Candidate')).toBeVisible();

  await page.getByRole('button', { name: 'Book Interview' }).first().click();
  await page.locator('#interviewDateSelector').fill('2030-01-15');
  await expect(page.getByRole('button', { name: 'Book' }).first()).toBeVisible();
  await page.getByRole('button', { name: 'Book' }).first().click();

  const bookingModal = page.locator('#bookingModal');
  await page.evaluate(() => {
    const modal = document.getElementById('bookingModal');
    const trigger = document.querySelector('.book-slot-btn');
    window.bootstrap.Modal.getOrCreateInstance(modal).show(trigger);
  });
  await expect(bookingModal).toBeVisible();
  await bookingModal.getByLabel(/Company Name/).fill('Playwright Systems');
  await bookingModal.getByLabel(/Technology/).fill('Python');
  await bookingModal.getByLabel(/Interview Round/).selectOption('L1');
  await page.getByRole('button', { name: 'Next: HR Details', exact: true }).click();
  await expect(page.locator('#bookingFooter2')).toBeVisible();
  await bookingModal.getByLabel(/HR Name/).fill('E2E HR');
  await bookingModal.getByLabel(/HR Number/).fill('+91 9000000000');
  await page.locator('#bookingFooter2 button[type="submit"]').click();

  await expect(page.getByText('Interview slot booked successfully!')).toBeVisible();
  await page.getByRole('button', { name: 'My Interviews' }).first().click();
  await expect(page.getByRole('cell', { name: 'Playwright Systems' })).toBeVisible();

  page.once('dialog', dialog => dialog.accept());
  await page.getByTitle('Cancel').first().click();
  await expect(page.getByText('Booking cancelled successfully!')).toBeVisible();
});
