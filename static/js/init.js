import { initCookieBanner } from "./cookie-consent.js";
import { initCookieSettingsForm } from "./cookie-settings.js";
import { initMOJSideNavMobileScroll } from "./moj-side-nav-mobile-scroll.js";
import { initMOJSideNavReload } from "./moj-side-nav-reload.js";
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
    initMOJSideNavMobileScroll();
    initMOJSideNavReload();
};

export { initAll };
