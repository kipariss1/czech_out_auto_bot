import { expect, test } from 'playwright/test'
import { sqliteDBhandler } from './index';
import { LandingPage, CreateSearchPage, type SearchFormInputs } from './poms';
import { assertTextPresent, assertAlertPresent } from './assertions';

const testUser = {
        id: 111111111,
        telegramId: 420000111
}

const baseUrl = 'http://localhost:8000/';

const inputData: SearchFormInputs = {
        carManufacturer: 'Audi',
        carModel: 'A3',
        mileageFrom: 150_000,
        mileageTo: 250_000,
        priceFrom: 150_000,
        priceTo: 200_000,
        yearFromInput: 2010,
        yearToInput: 2012,
        pscCode: '11000',
        kmRangeFromPSC: 25
    }

test.beforeEach(async ({ page }) => {
    sqliteDBhandler.cleanDB();
    sqliteDBhandler.insertUser(testUser);

    await page.route('**/telegram-web-app.js', async route => {
        await route.fulfill({
            contentType: 'application/javascript',
            body: `
                window.Telegram = {
                    WebApp: {
                        ready() {},
                        expand() {},
                        initDataUnsafe: {
                            user: { id: ${testUser.telegramId} }
                        }
                    }
                };
            `,
        });
    });

    await page.addInitScript((telegramUser) => {
        (window as typeof window & {
            Telegram?: {
                WebApp?: {
                    ready?: () => void,
                    expand?: () => void,
                    initDataUnsafe?: {
                        user?: { id: number }
                    }
                }
            }
        }).Telegram = {
            WebApp: {
                ready() {},
                expand() {},
                initDataUnsafe: {
                    user: {
                        id: telegramUser.id
                    }
                }
            }
        };
    }, { id: testUser.telegramId });
});

test.afterEach(async ({}) => {
    sqliteDBhandler.cleanDB();
});

test('Happy path test', async ({ page }) => {
    const landingPage = new LandingPage(page);
    const createSearchPage = new CreateSearchPage(page);

    await page.goto(baseUrl);
    await landingPage.waitForPageToLoad();
    await landingPage.createSearchBtn.click();
    await createSearchPage.createNewSearch(inputData);
    await landingPage.waitForPageToLoad();
    await assertAlertPresent(page, 'New search successfully created!');
    await assertTextPresent(page, `Year range: ${inputData.yearFromInput} - ${inputData.yearToInput}`);
    await assertTextPresent(page, `Mileage range: ${inputData.mileageFrom} - ${inputData.mileageTo}`);
    await assertTextPresent(page, `Price range (Kč): ${inputData.priceFrom} - ${inputData.priceTo}`);
});

test('Assert user can\'t create the same search two times', async ({ page }) => {
    const landingPage = new LandingPage(page);
    const createSearchPage = new CreateSearchPage(page);

    await page.goto(baseUrl);
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
    await page.goto(baseUrl);
    await test.step('Assert form requires selection of model', async () => {
        await landingPage.createSearchBtn.click();
        await createSearchPage.waitForPageToLoad();
        await createSearchPage.carManufacturerSelect.selectOption(inputData.carManufacturer);
        await createSearchPage.submitBtn.click();
        await assertAlertPresent(page, 'You must select car and model to continue!')
    });
    await test.step('Assert form requires PSC when km range is filled', async () => {
        await createSearchPage.carModelSelect.selectOption(inputData.carModel);
        await createSearchPage.kmRangeFromPSCFilterSwitch.check();
        await createSearchPage.kmRangeFromPSCinput.fill(inputData.kmRangeFromPSC!.toString());
        await createSearchPage.submitBtn.click();
        await assertAlertPresent(page, 'PSC is required when km range is provided!');
        await createSearchPage.kmRangeFromPSCinput.fill('');
    });
    await test.step('Assert form validates PSC in correct format when provided', async () => {
        await createSearchPage.PSCFilterSwitch.check();
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

test('Optional filters stay disabled until switched on', async ({ page }) => {
    const landingPage = new LandingPage(page);
    const createSearchPage = new CreateSearchPage(page);

    await page.goto(baseUrl);
    await landingPage.waitForPageToLoad();
    await landingPage.createSearchBtn.click();
    await createSearchPage.waitForPageToLoad();

    await expect(createSearchPage.mileageFilterSwitch).not.toBeChecked();
    await expect(createSearchPage.milegeFromInput).toBeDisabled();
    await expect(createSearchPage.milegeFromInput).toHaveValue('');

    await createSearchPage.mileageFilterSwitch.check();
    await expect(createSearchPage.milegeFromInput).toBeEnabled();
    await expect(createSearchPage.milegeFromInput).not.toHaveValue('');

    await createSearchPage.mileageFilterSwitch.uncheck();
    await expect(createSearchPage.milegeFromInput).toBeDisabled();
    await expect(createSearchPage.milegeFromInput).toHaveValue('');
});
