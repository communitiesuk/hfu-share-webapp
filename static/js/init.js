import { initCookieBanner } from "./cookie-consent.js";
import { initCookieSettingsForm } from "./cookie-settings.js";
import { initFilteredSection } from "./filtered-section.js";
import { initMultiValueTextInput } from "./multi-value-text-input.js";
import { initSafeguardingForm } from "./safeguarding-form.js";
import { initSearchableSelect } from "./searchable-select.js";

const initAll = () => {
    initSafeguardingForm();
    initSearchableSelect();
    initFilteredSection();
    initCookieBanner();
    initCookieSettingsForm();
    initMultiValueTextInput();
};

export { initAll };
