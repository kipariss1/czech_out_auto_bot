import { test, expect } from 'playwright/test'
import { sqliteDBhandler, cipherHandler } from './index.js';


const testUser = {
        id: '111111111',
        language: 'en'
}

const enc_user_id = cipherHandler.encode(testUser.id);

const baseUrl = 'http://localhost:8000/';

test.beforeAll(async ({}) => {
    sqliteDBhandler.insertUser(testUser);
});

test.afterAll(async ({}) => {
    sqliteDBhandler.removeDb();
});

test('Happy path test', async ({ page }) => {
    await page.goto(`${baseUrl}?enc_user_id=${enc_user_id}`);
    await page.waitForTimeout(5000);
})
