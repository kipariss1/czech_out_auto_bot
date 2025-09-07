import { type Locator, type Page } from "playwright";
import { BasePage } from "./base.page.js";

export class LandingPage extends BasePage {
    public createSearchBtn: Locator;

    constructor (protected page: Page) {
        super(page);
        this.createSearchBtn = page.getByTestId("create-car-search-btn");
    }
}