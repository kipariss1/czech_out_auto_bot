import { test, expect } from "@playwright/test"


test('Basic example', async ({ page }) => {
    await page.goto('https://google.com');
    await expect(page).toHaveTitle('Google');
})
