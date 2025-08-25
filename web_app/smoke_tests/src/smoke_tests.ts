import { test, expect } from 'playwright/test'

test.beforeEach(async ({}) => {
    // TODO: write incertion of the test user before each test
})

test('Happy path test', async ({ page }) => {
    await page.goto(`http://localhost:8000?enc_user_id=${123/*TODO: insert actually an encrypted id*/}`);
})
