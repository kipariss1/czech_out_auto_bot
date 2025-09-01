import { test, expect } from 'playwright/test'
import { sqliteDBhandler, cipherHandler } from './index.js';
import { LandingPage, CreateSearchPage, type SearchFormInputs } from './poms';

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
    sqliteDBhandler.removeUser();
});

test('Happy path test', async ({ page }) => {
    const inputData: SearchFormInputs = {
        carManufacturer: 'Audi',
        carModel: 'A3',
        optionalAttributes: ['Sline'],
        mileageFrom: 150_000,
        mileageTo: 250_000,
        priceFrom: 150_000,
        priceTo: 200_000,
        yearFromInput: 2010,
        yearToInput: 2012,
        pscCode: '11000',
        kmRangeFromPSC: 25
    }
    const landingPage = new LandingPage(page);
    const createSearchPage = new CreateSearchPage(page);

    await page.goto(`${baseUrl}?enc_user_id=${enc_user_id}`);
    await landingPage.createSearchBtn.click();
    await createSearchPage.createNewSearch(inputData);
    // TODO: make the expectations here
    await page.waitForTimeout(5000);
})
