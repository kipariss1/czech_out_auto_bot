import { expect, type Locator, type Page } from "playwright/test";

export async function assertTextPresent(page: Page, text: string | RegExp): Promise<void> {
    const textElement = page.getByText(text);
    await expect(textElement.first(), `Element with text "${text}" is not visible`).toBeVisible();
}

export async function assertAlertPresent(page: Page, errorMsg: string | RegExp) {
    const alert = page.getByRole('alert');
    await expect(alert.filter({ hasText: errorMsg }), `Error with text "${errorMsg}" is not visible`).toBeVisible();
}
