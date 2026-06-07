import { type Locator, type Page } from "playwright"
import { BasePage } from "./base.page";

export type SearchFormInputs = {
    carManufacturer: string;
    carModel: string;
    optionalAttributes?: string[];
    yearFromInput: number;
    yearToInput: number;               
    mileageFrom?: number;          
    mileageTo?: number;            
    priceFrom?: number;            
    priceTo?: number;              
    pscCode?: string;              
    kmRangeFromPSC?: number;       
};

export class CreateSearchPage extends BasePage {

    public carManufacturerSelect: Locator;
    public carModelSelect: Locator;
    public optionalAtributes: Locator;
    public optionalAtributeBtns: Locator;
    public yearFromInput: Locator;
    public yearToInput: Locator;
    public milegeFromInput: Locator;
    public milegeToInput: Locator;
    public priceFromInput: Locator;
    public priceToInput: Locator;
    public PSCinput: Locator;
    public kmRangeFromPSCinput: Locator;
    public submitBtn: Locator;

    constructor(protected page: Page) {
        super(page);
        this.carManufacturerSelect = page.getByTestId("select-manufacturer-input");
        this.carModelSelect = page.getByTestId("select-model-input");
        this.optionalAtributes = page.locator('[id^="id-attribute-"]');
        this.optionalAtributeBtns = page.locator('[id^="id-attributes-submit-btn-"]');
        this.yearFromInput = page.locator('#id-input-year-range-from');
        this.yearToInput = page.locator('#id-input-year-range-to');
        this.milegeFromInput = page.locator('#id-input-mileage-range-from');
        this.milegeToInput = page.locator('#id-input-mileage-range-to');
        this.priceFromInput = page.locator('#id-input-price-range-from');
        this.priceToInput = page.locator('#id-input-price-range-to');
        this.PSCinput = page.locator('#id-psc-code');
        this.kmRangeFromPSCinput = page.locator('#id-psc-km-range');
        this.submitBtn = page.getByTestId("submit-btn");
    }

    async createNewSearch(data: SearchFormInputs) {
        await this.carManufacturerSelect.selectOption(data.carManufacturer);
        await this.carManufacturerSelect.dispatchEvent('change');
        await this.page.waitForTimeout(1000);
        await this.carModelSelect.selectOption(data.carModel);
        if (data.optionalAttributes && data.optionalAttributes.length > 0) {
            for (let i = 0; i < data.optionalAttributes.length; i++) {
                const attrValue = data.optionalAttributes[i];
                const textarea = this.optionalAtributes.nth(i);
                const button = this.optionalAtributeBtns.nth(i);
                if (attrValue) {
                    await textarea.fill(attrValue);
                    await button.click();
                }
            }
        }
        await this.yearFromInput.fill(data.yearFromInput.toString());
        await this.yearToInput.fill(data.yearToInput.toString());
        if (data.mileageFrom !== undefined) {
            await this.milegeFromInput.fill(data.mileageFrom.toString());
        }
        if (data.mileageTo !== undefined) {
            await this.milegeToInput.fill(data.mileageTo.toString());
        }
        if (data.priceFrom !== undefined) {
            await this.priceFromInput.fill(data.priceFrom.toString());
        }
        if (data.priceTo !== undefined) {
            await this.priceToInput.fill(data.priceTo.toString());
        }
        if (data.pscCode !== undefined) {
            await this.PSCinput.fill(data.pscCode);
        }
        if (data.kmRangeFromPSC !== undefined) {
            await this.kmRangeFromPSCinput.fill(data.kmRangeFromPSC.toString());
        }
        await this.submitBtn.click();
    }
}
