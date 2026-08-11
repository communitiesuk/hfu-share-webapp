import os
import re
from unittest import TestCase

from playwright.sync_api import expect, sync_playwright


class BrowserTests(TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def test_has_title(self):
        page = self.browser.new_page()
        page.goto("https://example.com/")

        # Expect a title "to contain" a substring.
        expect(page).to_have_title(re.compile("Example Domain"))
        page.close()

    def test_get_started_link(self):
        page = self.browser.new_page()
        page.goto("https://example.com/")

        # Click the learn more link.
        page.get_by_role("link", name="Learn more").click()

        # Expects page to have a heading with the name of Example Domain.
        expect(page.get_by_role("heading", name="Example Domain")).to_be_visible()
        page.close()
