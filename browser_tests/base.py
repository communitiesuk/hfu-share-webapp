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
        cls.dev_url = os.environ["HFU_DEV_URL"]
        cls.dev_email = os.environ["HFU_DEV_EMAIL"]
        cls.dev_password = os.environ["HFU_DEV_PASSWORD"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        self.page = self.browser.new_page()
        self.addCleanup(self.page.close)

    def login(self) -> None:
        self.page.goto(self.dev_url)
        self.page.get_by_label("Email address").fill(self.dev_email)
        self.page.get_by_label("Password").fill(self.dev_password)
        self.page.get_by_role("button", name="Sign in").click()
