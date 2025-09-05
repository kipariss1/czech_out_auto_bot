import { type Page } from "playwright";

export abstract class BasePage {

    constructor(
        protected page: Page,
    ) {}

    async waitForPageToLoad() {
        
    }

}