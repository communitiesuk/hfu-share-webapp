import os
from typing import ClassVar

from django.test import SimpleTestCase, tag
from dotenv import load_dotenv
from playwright.sync_api import Browser, Page, Playwright, sync_playwright


@tag("browser")
class BrowserTestCase(SimpleTestCase):
    playwright: ClassVar[Playwright]
    browser: ClassVar[Browser]
    base_url: ClassVar[str]
    test_user_email: ClassVar[str]
    test_user_password: ClassVar[str]
    page: Page

    @classmethod
    def setUpClass(cls) -> None:
        load_dotenv(override=False)
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            headless=os.environ.get("HEADLESS", "1") == "1"
        )
        cls.base_url = os.environ["BROWSER_TEST_URL"]
        cls.test_user_email = os.environ["BROWSER_TEST_USER_EMAIL"]
        cls.test_user_password = os.environ["BROWSER_TEST_USER_PASSWORD"]

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
        self.page.goto(self.base_url)
        self.page.get_by_label("Email address").fill(self.test_user_email)
        self.page.get_by_label("Password").fill(self.test_user_password)
        self.page.get_by_role("button", name="Sign in").click()
