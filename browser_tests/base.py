import os
from typing import ClassVar

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from dotenv import load_dotenv
from playwright.sync_api import Browser, Page, Playwright, sync_playwright


@tag("browser")
class BrowserTestCase(StaticLiveServerTestCase):
    playwright: ClassVar[Playwright]
    browser: ClassVar[Browser]
    page: Page

    @classmethod
    def setUpClass(cls) -> None:
        load_dotenv(override=False)
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            headless=os.environ.get("HEADLESS", "1") == "1"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        self.page = self.browser.new_page()
        self.addCleanup(self.page.close)
