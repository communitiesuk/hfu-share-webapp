import os
import re

from playwright.sync_api import expect

from browser_tests.base import BrowserTestCase


class BrowserTests(BrowserTestCase):
    def test_landing_page_redirects_to_login(self):
        self.page.goto(self.dev_url)
        expect(self.page).to_have_url(re.compile("/accounts/login/"))
        expect(
            self.page.get_by_role("heading", name="Sign In - EntraID disabled")
        ).to_be_visible()

    def test_login(self):
        self.login()
        expect(self.page).to_have_url(re.compile("/landing-page"))
        expect(self.page.get_by_role("heading", name="Welcome")).to_be_visible()
