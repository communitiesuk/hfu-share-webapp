import pytest

from browser_tests.accessibility_pages import RECORD_LIST_PAGES, STATIC_PAGES
from browser_tests.axe_checks import assert_no_axe_violations, collect_axe_violations

from ..pages.share_page import SharePage
from .base import BrowserTest


def open_page(page: SharePage, path, page_name):
    response = page.goto(path)

    assert response is not None and response.ok, (
        f"{page_name} ({path}) returned HTTP "
        f"{response.status if response else 'no response'} for the browser "
        "test user, fix the user's access or move the path to NOT_SCANNABLE"
    )

    heading = page.page_heading.inner_text()
    assert heading not in ("Page not found", "Sign in"), (
        f"{page_name} ({path}) rendered '{heading}' instead of the real page "
        "for the browser test user, fix the user's access or move the path "
        "to NOT_SCANNABLE"
    )


@pytest.mark.accessibility
class TestAccessibility(BrowserTest):
    def test_sign_in_page_has_no_axe_violations(self, sign_in_page):
        assert_no_axe_violations(sign_in_page, "sign in page")

    @pytest.mark.parametrize(("path", "page_name"), STATIC_PAGES)
    def test_page_has_no_axe_violations(self, home_page, path, page_name):
        open_page(home_page, path, page_name)
        assert_no_axe_violations(home_page, page_name)

    @pytest.mark.parametrize(("list_path", "record_name"), RECORD_LIST_PAGES)
    def test_record_tabs_have_no_axe_violations(
        self, home_page, list_path, record_name
    ):
        open_page(home_page, list_path, f"{record_name} list")

        record_links = home_page.page.locator("main table a")
        if record_links.count() == 0:
            pytest.skip(f"no {record_name} records visible to the browser test user")

        record_links.first.click()
        home_page.page.wait_for_load_state()

        reports = [collect_axe_violations(home_page, f"{record_name} record")]

        tab_hrefs = [
            tab.get_attribute("href")
            for tab in home_page.page.locator("a.govuk-tabs__tab").all()
        ]
        for href in tab_hrefs:
            home_page.goto(href)
            reports.append(
                collect_axe_violations(home_page, f"{record_name} record tab {href}")
            )

        failures = [report for report in reports if report]
        assert not failures, "\n\n".join(failures)
