import pytest

from browser_tests.accessibility_pages import RECORD_LIST_PAGES, STATIC_PAGES
from browser_tests.axe_checks import assert_no_axe_violations, collect_axe_violations

from .base import BrowserTest


def open_page(page, base_url, path, page_name):
    response = page.goto(base_url.rstrip("/") + path)

    assert response is not None and response.ok, (
        f"{page_name} ({path}) returned HTTP "
        f"{response.status if response else 'no response'} for the browser "
        "test user, fix the user's access or move the path to NOT_SCANNABLE"
    )

    heading = page.locator("h1").first.inner_text()
    assert heading not in ("Page not found", "Sign in"), (
        f"{page_name} ({path}) rendered '{heading}' instead of the real page "
        "for the browser test user, fix the user's access or move the path "
        "to NOT_SCANNABLE"
    )


@pytest.mark.accessibility
class TestAccessibility(BrowserTest):
    def test_sign_in_page_has_no_axe_violations(self, sign_in_page):
        assert_no_axe_violations(sign_in_page.page, "sign in page")

    @pytest.mark.parametrize(("path", "page_name"), STATIC_PAGES)
    def test_page_has_no_axe_violations(self, home_page, path, page_name):
        page = home_page.page
        open_page(page, home_page.base_url, path, page_name)
        assert_no_axe_violations(page, page_name)

    @pytest.mark.parametrize(("list_path", "record_name"), RECORD_LIST_PAGES)
    def test_record_tabs_have_no_axe_violations(
        self, home_page, list_path, record_name
    ):
        page = home_page.page
        open_page(page, home_page.base_url, list_path, f"{record_name} list")

        record_links = page.locator("main table a")
        if record_links.count() == 0:
            pytest.skip(f"no {record_name} records visible to the browser test user")

        record_links.first.click()
        page.wait_for_load_state()

        reports = [collect_axe_violations(page, f"{record_name} record")]

        tab_hrefs = [
            tab.get_attribute("href") for tab in page.locator("a.govuk-tabs__tab").all()
        ]
        for href in tab_hrefs:
            page.goto(home_page.base_url.rstrip("/") + href)
            reports.append(
                collect_axe_violations(page, f"{record_name} record tab {href}")
            )

        failures = [report for report in reports if report]
        assert not failures, "\n\n".join(failures)
