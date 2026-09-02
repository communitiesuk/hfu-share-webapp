import os

import pytest
from dotenv import load_dotenv
from playwright.sync_api import Page

from browser_tests.pages.home_page import HomePage
from browser_tests.pages.safeguarding_page import SafeguardingPage

from .test_users import USER_TYPES, BrowserTestUserFactory


def _verify_config():
    if not os.getenv("BROWSER_TEST_URL"):
        pytest.exit(
            "Missing environment variables: BROWSER_TEST_URL",
            returncode=1,
        )


def pytest_sessionstart(session):
    load_dotenv()
    _verify_config()


@pytest.fixture
def home_page_factory(page: Page):
    def create(user_type):
        home_page = HomePage(page, BrowserTestUserFactory.create(user_type))
        return home_page

    return create


@pytest.fixture
def safeguarding_page_factory(page: Page):
    def create(user_type):
        safeguarding_page = SafeguardingPage(
            page, BrowserTestUserFactory.create(user_type)
        )
        return safeguarding_page

    return create


def create_home_page_fixture(user_type: str):
    @pytest.fixture
    def fixture(home_page_factory):
        return home_page_factory(user_type)

    return fixture


def create_safeguarding_page_fixture(user_type: str):
    @pytest.fixture
    def fixture(safeguarding_page_factory):
        return safeguarding_page_factory(user_type)

    return fixture


for user_type in USER_TYPES:
    fixture_param = f"_with_{user_type}_user" if user_type != "default" else ""

    globals()[f"home_page{fixture_param}"] = create_home_page_fixture(user_type)
    globals()[f"safeguarding_page{fixture_param}"] = create_safeguarding_page_fixture(
        user_type
    )
