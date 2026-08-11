import re

from playwright.sync_api import expect

from browser_tests.base import BrowserTestCase


class BrowserTests(BrowserTestCase):
    def test_has_title(self) -> None:
        self.page.goto("https://example.com/")

        expect(self.page).to_have_title(re.compile("Example Domain"))

    def test_get_started_link(self) -> None:
        self.page.goto("https://example.com/")

        self.page.get_by_role("link", name="Learn more").click()

        expect(self.page.get_by_role("heading", name="Example Domain")).to_be_visible()
