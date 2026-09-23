import os
import subprocess
import sys
from pathlib import Path
from typing import Type

import pytest
from dotenv import load_dotenv
from playwright.sync_api import Page

from browser_tests.pages import CookiesPage, HomePage, SafeguardingPage, SharePage
from test_utils.helpers import browser_test_url_is_local

from .test_users import UserType, create_browser_test_user

MANAGE_PY = Path(__file__).resolve().parent.parent / "manage.py"


def _verify_config():
    if not os.getenv("BROWSER_TEST_URL"):
        pytest.exit(
            "Missing environment variables: BROWSER_TEST_URL",
            returncode=1,
        )


def _run_seed_browser_test_la(*args: str) -> None:
    if not os.getenv("SKIP_BROWSER_TEST_SEED"):
        subprocess.run(
            [sys.executable, str(MANAGE_PY), "seed_browser_test_la", *args],
            check=True,
        )


def pytest_sessionstart(session):
    load_dotenv()
    _verify_config()

    if browser_test_url_is_local():
        _run_seed_browser_test_la("--seed")


@pytest.fixture
def page_factory(page: Page):
    def create(share_page_class: Type[SharePage], user_type: UserType):
        share_page = share_page_class(page, create_browser_test_user(user_type))
        return share_page

    return create


def create_page_fixture(share_page_class: Type[SharePage], user_type: UserType):
    @pytest.fixture
    def fixture(page_factory):
        return page_factory(share_page_class, user_type)

    return fixture


for user_type in UserType:
    fixture_param = (
        f"_with_{user_type.value.lower()}user"
        if user_type is not UserType.DEFAULT
        else ""
    )

    globals()[f"home_page{fixture_param}"] = create_page_fixture(HomePage, user_type)
    globals()[f"safeguarding_page{fixture_param}"] = create_page_fixture(
        SafeguardingPage, user_type
    )
    globals()[f"cookies_page{fixture_param}"] = create_page_fixture(
        CookiesPage, user_type
    )
