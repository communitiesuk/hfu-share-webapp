from .base import BrowserTest


class TestHomePage(BrowserTest):
    def test_can_log_into_home_page(self, sign_in_page):
        sign_in_page.sign_in()

        sign_in_page.assert_has_heading("Welcome")
        sign_in_page.assert_has_secondary_heading("Manage records")

    def test_can_view_accessibility_statement(self, home_page):
        home_page.click_footer_link("Accessibility statement")

        home_page.assert_has_heading(
            "Accessibility statement for Share Homes for Ukraine data (Share)"
        )

        home_page.click_breadcrumb_link("Home")

        home_page.assert_has_heading("Welcome")
        home_page.assert_has_secondary_heading("Manage records")

    def test_can_view_cookies(self, home_page):
        home_page.click_footer_link("Cookies")

        home_page.assert_has_heading("Cookies")

        home_page.click_breadcrumb_link("Home")

        home_page.assert_has_heading("Welcome")
        home_page.assert_has_secondary_heading("Manage records")
