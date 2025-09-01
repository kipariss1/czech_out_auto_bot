import { type Locator, type Page } from "playwright";

export class LandingPage {
    public createSearchBtn: Locator;

    constructor (page: Page) {
        this.createSearchBtn = page.getByTestId("create-car-search-btn");
    }
}