import { test, expect } from 'playwright/test'
import { sqliteDBhandler, cipherHandler } from './index.js';
import { LandingPage, CreateSearchPage, type SearchFormInputs } from './poms';
import { assertTextPresent } from './assertions';

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
    await landingPage.waitForPageToLoad();
    await landingPage.createSearchBtn.click();
    await createSearchPage.createNewSearch(inputData);
    await landingPage.waitForPageToLoad();
    await assertTextPresent(page, 'Year range:');
    await assertTextPresent(page, `${inputData.yearFromInput} - ${inputData.yearToInput}`);
    await assertTextPresent(page, 'Mileage range:');
    await assertTextPresent(page, `${inputData.mileageFrom} - ${inputData.mileageTo}`);
    await assertTextPresent(page, 'Price range:');
    await assertTextPresent(page, `${inputData.priceFrom} - ${inputData.priceTo}`);
    await assertTextPresent(page, 'Unique trait #1:');
    await assertTextPresent(page, 'Year range:');
    await assertTextPresent(page, `${inputData.optionalAttributes![0]}`);
})
