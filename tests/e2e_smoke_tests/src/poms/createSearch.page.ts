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
    public mileageFilterSwitch: Locator;
    public priceFromInput: Locator;
    public priceToInput: Locator;
    public priceFilterSwitch: Locator;
    public PSCinput: Locator;
    public PSCFilterSwitch: Locator;
    public kmRangeFromPSCinput: Locator;
    public kmRangeFromPSCFilterSwitch: Locator;
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
        this.mileageFilterSwitch = page.locator('#id-enable-mileage-filter');
        this.priceFromInput = page.locator('#id-input-price-range-from');
        this.priceToInput = page.locator('#id-input-price-range-to');
        this.priceFilterSwitch = page.locator('#id-enable-price-filter');
        this.PSCinput = page.locator('#id-psc-code');
        this.PSCFilterSwitch = page.locator('#id-enable-psc-filter');
        this.kmRangeFromPSCinput = page.locator('#id-psc-km-range');
        this.kmRangeFromPSCFilterSwitch = page.locator('#id-enable-psc-km-filter');
        this.submitBtn = page.getByTestId("submit-btn");
    }

    private async enableOptionalFilter(filterSwitch: Locator) {
        if (!(await filterSwitch.isChecked())) {
            await filterSwitch.check();
        }
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
        if (data.mileageFrom !== undefined || data.mileageTo !== undefined) {
            await this.enableOptionalFilter(this.mileageFilterSwitch);
        }
        if (data.mileageFrom !== undefined) {
            await this.milegeFromInput.fill(data.mileageFrom.toString());
        }
        if (data.mileageTo !== undefined) {
            await this.milegeToInput.fill(data.mileageTo.toString());
        }
        if (data.priceFrom !== undefined || data.priceTo !== undefined) {
            await this.enableOptionalFilter(this.priceFilterSwitch);
        }
        if (data.priceFrom !== undefined) {
            await this.priceFromInput.fill(data.priceFrom.toString());
        }
        if (data.priceTo !== undefined) {
            await this.priceToInput.fill(data.priceTo.toString());
        }
        if (data.pscCode !== undefined) {
            await this.enableOptionalFilter(this.PSCFilterSwitch);
            await this.PSCinput.fill(data.pscCode);
        }
        if (data.kmRangeFromPSC !== undefined) {
            await this.enableOptionalFilter(this.kmRangeFromPSCFilterSwitch);
            await this.kmRangeFromPSCinput.fill(data.kmRangeFromPSC.toString());
        }
        await this.submitBtn.click();
    }
}
