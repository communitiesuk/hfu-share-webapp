import pytest

from ..pages import CookiesPage
from .base import BrowserTest


@pytest.fixture(autouse=True)
def navigate_to_landing_pag(cookies_page: CookiesPage):
    cookies_page.sign_in()


def _setup_cookies_and_check_banner_is_visible(cookies_page: CookiesPage):
    cookies_page.set_ga_cookies()

    cookies_page.assert_cookie_banner_visibility(True)
    cookies_page.assert_cookies_on_share_visibility(True)
    cookies_page.assert_cookies_confirmation_visibility(False)

    cookies_page.assert_cookie_is_not_set("cookie_consent")
    cookies_page.assert_cookie_is_set(cookies_page.ga_cookie_name)
    cookies_page.assert_cookie_is_set(cookies_page.ga_id_cookie_name)


def _setup_cookies_and_navifate_to_cookies_page(cookies_page: CookiesPage):
    cookies_page.set_ga_cookies()

    cookies_page.assert_cookie_banner_visibility(True)
    cookies_page.assert_cookies_on_share_visibility(True)
    cookies_page.assert_cookies_confirmation_visibility(False)

    cookies_page.click_cookie_link("How we use cookies")
    cookies_page.assert_has_heading("Cookies")

    cookies_page.assert_cookie_banner_visibility(False)
    cookies_page.assert_cookie_is_not_set("cookie_consent")
    cookies_page.assert_cookie_is_set(cookies_page.ga_cookie_name)
    cookies_page.assert_cookie_is_set(cookies_page.ga_id_cookie_name)

    cookies_page.assert_cookie_settings_choices_visibility(True)
    cookies_page.assert_cookie_setting_confirmation_visibility(False)

    cookies_page.assert_cookie_option_check_status("Yes", False)
    cookies_page.assert_cookie_option_check_status("No", False)


class TestCookies(BrowserTest):
    def test_can_accept_cookies_via_banner(self, cookies_page: CookiesPage):
        _setup_cookies_and_check_banner_is_visible(cookies_page)

        cookies_page.click_cookie_button("Accept analytics cookies")

        cookies_page.assert_cookie_banner_visibility(True)
        cookies_page.assert_cookies_on_share_visibility(False)
        cookies_page.assert_cookies_confirmation_visibility(True)
        cookies_page.assert_cookies_confirmation_accepted_visibility(True)
        cookies_page.assert_cookies_confirmation_rejected_visibility(False)

        cookies_page.assert_cookie_is_set_with_value("cookie_consent", "true")
        cookies_page.assert_cookie_is_set(cookies_page.ga_cookie_name)
        cookies_page.assert_cookie_is_set(cookies_page.ga_id_cookie_name)

        cookies_page.click_cookie_button("Hide cookie message")

        cookies_page.assert_cookie_banner_visibility(False)

        # Check cookie banner hidden on other pages
        cookies_page.click_link("Accommodation requests")
        cookies_page.assert_has_heading("Accommodation requests")

        cookies_page.assert_cookie_banner_visibility(False)

        # And that the GA cookies are still there
        cookies_page.assert_cookie_is_set_with_value("cookie_consent", "true")
        cookies_page.assert_cookie_is_set(cookies_page.ga_cookie_name)
        cookies_page.assert_cookie_is_set(cookies_page.ga_id_cookie_name)

    def test_can_reject_cookies_via_banner(self, cookies_page: CookiesPage):
        _setup_cookies_and_check_banner_is_visible(cookies_page)

        cookies_page.click_cookie_button("Reject analytics cookies")

        cookies_page.assert_cookie_banner_visibility(True)
        cookies_page.assert_cookies_on_share_visibility(False)
        cookies_page.assert_cookies_confirmation_visibility(True)
        cookies_page.assert_cookies_confirmation_accepted_visibility(False)
        cookies_page.assert_cookies_confirmation_rejected_visibility(True)

        cookies_page.assert_cookie_is_set_with_value("cookie_consent", "false")
        cookies_page.assert_cookie_is_not_set(cookies_page.ga_cookie_name)
        cookies_page.assert_cookie_is_not_set(cookies_page.ga_id_cookie_name)

        cookies_page.click_cookie_button("Hide cookie message")

        cookies_page.assert_cookie_banner_visibility(False)

        # Check cookie banner hidden on other pages
        cookies_page.click_link("Accommodation requests")
        cookies_page.assert_has_heading("Accommodation requests")

        cookies_page.assert_cookie_banner_visibility(False)

        # And that the GA cookies are still there
        cookies_page.assert_cookie_is_set_with_value("cookie_consent", "false")
        cookies_page.assert_cookie_is_not_set(cookies_page.ga_cookie_name)
        cookies_page.assert_cookie_is_not_set(cookies_page.ga_id_cookie_name)

    def test_can_accept_cookies_via_settings(self, cookies_page: CookiesPage):
        _setup_cookies_and_navifate_to_cookies_page(cookies_page)

        cookies_page.check_field("Yes")
        cookies_page.click_button("Save cookie settings")

        cookies_page.assert_cookie_settings_choices_visibility(False)
        cookies_page.assert_cookie_setting_confirmation_visibility(True)

        cookies_page.assert_cookie_is_set_with_value("cookie_consent", "true")
        cookies_page.assert_cookie_is_set(cookies_page.ga_cookie_name)
        cookies_page.assert_cookie_is_set(cookies_page.ga_id_cookie_name)

        # Check settings are saved
        cookies_page.page.reload()

        cookies_page.assert_cookie_banner_visibility(False)
        cookies_page.assert_cookie_settings_choices_visibility(True)
        cookies_page.assert_cookie_setting_confirmation_visibility(False)

        cookies_page.assert_cookie_option_check_status("Yes", True)
        cookies_page.assert_cookie_option_check_status("No", False)

        cookies_page.assert_cookie_is_set_with_value("cookie_consent", "true")
        cookies_page.assert_cookie_is_set(cookies_page.ga_cookie_name)
        cookies_page.assert_cookie_is_set(cookies_page.ga_id_cookie_name)

        # Check cookie banner now hidden on other pages
        cookies_page.click_navigation_link("Accommodation requests")
        cookies_page.assert_has_heading("Accommodation requests")

        cookies_page.assert_cookie_banner_visibility(False)

        # And that the GA cookies are still there
        cookies_page.assert_cookie_is_set_with_value("cookie_consent", "true")
        cookies_page.assert_cookie_is_set(cookies_page.ga_cookie_name)
        cookies_page.assert_cookie_is_set(cookies_page.ga_id_cookie_name)

    def test_can_reject_cookies_via_settings(self, cookies_page: CookiesPage):
        _setup_cookies_and_navifate_to_cookies_page(cookies_page)

        cookies_page.check_field("No")
        cookies_page.click_button("Save cookie settings")

        cookies_page.assert_cookie_settings_choices_visibility(False)
        cookies_page.assert_cookie_setting_confirmation_visibility(True)

        cookies_page.assert_cookie_is_set_with_value("cookie_consent", "false")
        cookies_page.assert_cookie_is_not_set(cookies_page.ga_cookie_name)
        cookies_page.assert_cookie_is_not_set(cookies_page.ga_id_cookie_name)

        # Check settings are saved
        cookies_page.page.reload()

        cookies_page.assert_cookie_banner_visibility(False)
        cookies_page.assert_cookie_settings_choices_visibility(True)
        cookies_page.assert_cookie_setting_confirmation_visibility(False)

        cookies_page.assert_cookie_option_check_status("Yes", False)
        cookies_page.assert_cookie_option_check_status("No", True)

        cookies_page.assert_cookie_is_set_with_value("cookie_consent", "false")
        cookies_page.assert_cookie_is_not_set(cookies_page.ga_cookie_name)
        cookies_page.assert_cookie_is_not_set(cookies_page.ga_id_cookie_name)

        # Check cookie banner now hidden on other pages
        cookies_page.click_navigation_link("Accommodation requests")
        cookies_page.assert_has_heading("Accommodation requests")

        cookies_page.assert_cookie_banner_visibility(False)

        # And that the GA cookies are still there
        cookies_page.assert_cookie_is_set_with_value("cookie_consent", "false")
        cookies_page.assert_cookie_is_not_set(cookies_page.ga_cookie_name)
        cookies_page.assert_cookie_is_not_set(cookies_page.ga_id_cookie_name)

    def test_can_reject_cookies_via_settings_by_only_submitting(
        self, cookies_page: CookiesPage
    ):
        _setup_cookies_and_navifate_to_cookies_page(cookies_page)

        cookies_page.click_button("Save cookie settings")

        cookies_page.assert_cookie_settings_choices_visibility(False)
        cookies_page.assert_cookie_setting_confirmation_visibility(True)

        cookies_page.assert_cookie_is_set_with_value("cookie_consent", "false")
        cookies_page.assert_cookie_is_not_set(cookies_page.ga_cookie_name)
        cookies_page.assert_cookie_is_not_set(cookies_page.ga_id_cookie_name)

        # Check settings are saved
        cookies_page.page.reload()

        cookies_page.assert_cookie_banner_visibility(False)
        cookies_page.assert_cookie_settings_choices_visibility(True)
        cookies_page.assert_cookie_setting_confirmation_visibility(False)

        cookies_page.assert_cookie_option_check_status("Yes", False)
        cookies_page.assert_cookie_option_check_status("No", True)

        cookies_page.assert_cookie_is_set_with_value("cookie_consent", "false")
        cookies_page.assert_cookie_is_not_set(cookies_page.ga_cookie_name)
        cookies_page.assert_cookie_is_not_set(cookies_page.ga_id_cookie_name)

        # Check cookie banner now hidden on other pages
        cookies_page.click_navigation_link("Accommodation requests")
        cookies_page.assert_has_heading("Accommodation requests")

        cookies_page.assert_cookie_banner_visibility(False)

        # And that the GA cookies are still there
        cookies_page.assert_cookie_is_set_with_value("cookie_consent", "false")
        cookies_page.assert_cookie_is_not_set(cookies_page.ga_cookie_name)
        cookies_page.assert_cookie_is_not_set(cookies_page.ga_id_cookie_name)
