import { test, expect } from 'playwright/test'
import { sqliteDBhandler, cipherHandler } from './index';
import { LandingPage, CreateSearchPage, type SearchFormInputs } from './poms';
import { assertTextPresent, assertAlertPresent } from './assertions';

const testUser = {
        id: '111111111',
        language: 'en'
}

const enc_user_id = cipherHandler.encode(testUser.id);

const baseUrl = 'http://localhost:8000/';

const inputData: SearchFormInputs = {
        carManufacturer: 'Audi',
        carModel: 'A3',
        optionalAttributes: ['Sline', '2.0 TDI'],
        mileageFrom: 150_000,
        mileageTo: 250_000,
        priceFrom: 150_000,
        priceTo: 200_000,
        yearFromInput: 2010,
        yearToInput: 2012,
        pscCode: '11000',
        kmRangeFromPSC: 25
    }

test.beforeEach(async ({}) => {
    sqliteDBhandler.insertUser(testUser);
});

test.afterEach(async ({}) => {
    sqliteDBhandler.cleanDB();
});

test('Happy path test', async ({ page }) => {
    const landingPage = new LandingPage(page);
    const createSearchPage = new CreateSearchPage(page);

    await page.goto(`${baseUrl}?enc_user_id=${enc_user_id}`);
    await landingPage.waitForPageToLoad();
    await landingPage.createSearchBtn.click();
    await createSearchPage.createNewSearch(inputData);
    await landingPage.waitForPageToLoad();
    await assertAlertPresent(page, 'New search successfully created!');
    await assertTextPresent(page, `Year range: ${inputData.yearFromInput} - ${inputData.yearToInput}`);
    await assertTextPresent(page, `Mileage range: ${inputData.mileageFrom} - ${inputData.mileageTo}`);
    await assertTextPresent(page, `Price range (Kč): ${inputData.priceFrom} - ${inputData.priceTo}`);
    await assertTextPresent(page, `Unique trait #1: ${inputData.optionalAttributes![0]}`);
    await assertTextPresent(page, `Unique trait #2: ${inputData.optionalAttributes![1]}`);
});

test('Assert user can\'t create the same search two times', async ({ page }) => {
    const landingPage = new LandingPage(page);
    const createSearchPage = new CreateSearchPage(page);

    await page.goto(`${baseUrl}?enc_user_id=${enc_user_id}`);
    await landingPage.waitForPageToLoad();
    await landingPage.createSearchBtn.click();
    await createSearchPage.createNewSearch(inputData);
    await landingPage.waitForPageToLoad();
    await landingPage.createSearchBtn.click();
    await createSearchPage.createNewSearch(inputData);
    await landingPage.waitForPageToLoad();
    await assertAlertPresent(page, 'Attempted search alreay exists ¯\\_(ツ)_/¯')
});

test('Assert form validation works', async ({ page }) => {
    const landingPage = new LandingPage(page);
    const createSearchPage = new CreateSearchPage(page);
    await page.goto(`${baseUrl}?enc_user_id=${enc_user_id}`);
    await test.step('Assert form requires selection of model', async () => {
        await landingPage.createSearchBtn.click();
        await createSearchPage.waitForPageToLoad();
        await createSearchPage.carManufacturerSelect.selectOption(inputData.carManufacturer);
        await createSearchPage.submitBtn.click();
        await assertAlertPresent(page, 'You must select car and model to continue!')
    });
    await test.step('Assert form requires PSC', async () => {
        await createSearchPage.carModelSelect.selectOption(inputData.carModel);
        await createSearchPage.submitBtn.click();
        await assertAlertPresent(page, 'You should enter PSC to continue!')
    });
    await test.step('Assert form requires PSC in correct format', async () => {
        await createSearchPage.PSCinput.fill('1');
        await createSearchPage.submitBtn.click();
        await assertAlertPresent(page, 'PSC should be only numbers with optional space and needs to be at least 5 characters!');
        await createSearchPage.PSCinput.fill('11111111');
        await createSearchPage.submitBtn.click();
        await assertAlertPresent(page, 'PSC should be only numbers with optional space and needs to be at least 5 characters!');
        await createSearchPage.PSCinput.fill('111aa');
        await createSearchPage.submitBtn.click();
        await assertAlertPresent(page, 'PSC should be only numbers with optional space and needs to be at least 5 characters!');
        await createSearchPage.PSCinput.fill('11 000');
        await createSearchPage.submitBtn.click();
        await landingPage.waitForPageToLoad();
    });
});
