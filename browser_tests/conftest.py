import os

import pytest
from dotenv import load_dotenv
from playwright.sync_api import Page

from browser_tests.pages.home_page import HomePage


def _verify_config():
    required_browser_test_params = [
        "BROWSER_TEST_URL",
        "BROWSER_TEST_USER_EMAIL",
        "BROWSER_TEST_USER_PASSWORD",
    ]

    missing_browser_test_params = [
        param for param in required_browser_test_params if not os.getenv(param)
    ]

    if missing_browser_test_params:
        pytest.exit(
            f"Missing environment variables: {', '.join(missing_browser_test_params)}",
            returncode=1,
        )


def pytest_sessionstart(session):
    load_dotenv()
    _verify_config()


@pytest.fixture
def sign_in_page(page: Page):
    home_page = HomePage(page)
    home_page.open()
    return home_page


@pytest.fixture
def home_page(page: Page):
    home_page = HomePage(page)
    home_page.sign_in()
    return home_page
