from datetime import datetime, timedelta, timezone
from typing import Optional

from playwright._impl._api_structures import SetCookieParam
from playwright.sync_api import BrowserContext, Cookie, Locator, expect

from test_utils.helpers import browser_test_url_is_local

from .share_page import SharePage


class CookiesPage(SharePage):
    ga_cookie_name = "_ga"
    ga_id_cookie_name = ""

    @property
    def context(self) -> BrowserContext:
        return self.page.context

    @property
    def cookie_banner(self) -> Locator:
        return self.page.locator(".govuk-cookie-banner")

    @property
    def cookies_on_share(self) -> Locator:
        return self.cookie_banner.locator("#cookies-on-share")

    @property
    def cookies_confirmation(self) -> Locator:
        return self.cookie_banner.locator("#confirmation")

    @property
    def cookies_confirmation_accepted(self) -> Locator:
        return self.cookies_confirmation.locator("#accepted-confirmation")

    @property
    def cookies_confirmation_rejected(self) -> Locator:
        return self.cookies_confirmation.locator("#rejected-confirmation")

    @property
    def cookie_settings_choices(self) -> Locator:
        return self.main_page.locator(".cookie-settings-form")

    @property
    def cookie_setting_confirmation(self) -> Locator:
        return self.main_page.locator(".cookie-settings__confirmation")

    @property
    def google_analytics_id(self) -> Optional[str]:
        return self.cookie_banner.get_attribute("data-analytics-id")

    def set_ga_cookies(self):
        self.ga_id_cookie_name = f"_ga_{self.google_analytics_id.replace('G-', '')}"

        self.set_cookie(self.ga_cookie_name, "_ga-value")
        self.set_cookie(self.ga_id_cookie_name, "_ga_id-value")

    def click_cookie_button(self, button_text: str):
        self.click_button(button_text, self.cookie_banner)

    def click_cookie_link(self, link_text: str):
        self.click_link(link_text, self.cookie_banner)

    def assert_cookie_banner_visibility(self, isShown: bool):
        self.assert_element_visibility(self.cookie_banner, isShown)

    def assert_cookies_on_share_visibility(self, isShown: bool):
        self.assert_element_visibility(self.cookies_on_share, isShown)

    def assert_cookies_confirmation_visibility(self, isShown: bool):
        self.assert_element_visibility(self.cookies_confirmation, isShown)

    def assert_cookies_confirmation_accepted_visibility(self, isShown: bool):
        self.assert_element_visibility(self.cookies_confirmation_accepted, isShown)

    def assert_cookies_confirmation_rejected_visibility(self, isShown: bool):
        self.assert_element_visibility(self.cookies_confirmation_rejected, isShown)

    def assert_cookie_settings_choices_visibility(self, isShown: bool):
        self.assert_element_visibility(self.cookie_settings_choices, isShown)

    def assert_cookie_setting_confirmation_visibility(self, isShown: bool):
        self.assert_element_visibility(self.cookie_setting_confirmation, isShown)

    def set_cookie(self, cookie_name: str, cookie_value: str):
        cookie_settings: SetCookieParam = {
            "name": cookie_name,
            "value": cookie_value,
            "expires": (datetime.now(tz=timezone.utc) + timedelta(365)).timestamp(),
            "sameSite": "Strict",
        }

        if browser_test_url_is_local():
            cookie_settings["url"] = f"{self.base_url}/"
        else:
            cookie_settings["domain"] = ".communities.gov.uk"
            cookie_settings["path"] = "/"

        self.context.add_cookies([cookie_settings])

    def assert_cookie_is_set(self, cookie_name: str):
        assert self._find_cookie(cookie_name) is not None

    def assert_cookie_is_not_set(self, cookie_name: str):
        assert self._find_cookie(cookie_name) is None

    def assert_cookie_is_set_with_value(self, cookie_name: str, cookie_value: str):
        cookie = self._find_cookie(cookie_name)

        assert cookie is not None and cookie["value"] == cookie_value

    def _find_cookie(self, cookie_name: str) -> Optional[Cookie]:
        for cookie in self.context.cookies():
            if cookie_name == cookie["name"]:
                return cookie

        return None

    def assert_cookie_option_check_status(self, option: str, is_checked: bool):
        radio_button = self.cookie_settings_choices.get_by_label(option)

        if is_checked:
            expect(radio_button).to_be_checked()
        else:
            expect(radio_button).not_to_be_checked()
