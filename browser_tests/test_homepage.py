import re

from playwright.sync_api import expect

from browser_tests.base import BrowserTestCase


class BrowserTests(BrowserTestCase):
    def test_landing_page_redirects_to_login(self):
        self.page.goto("<dev_url_here>")

        expect(self.page).to_have_url(re.compile("landing-page"))
        expect(self.page.get_by_role("heading", name="Sign In - EntraID disabled")).to_be_visible()
