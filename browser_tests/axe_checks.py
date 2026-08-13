from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Page

WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]


def collect_axe_violations(page: Page, page_name: str) -> str | None:
    results = Axe().run(
        page,
        options={"runOnly": {"type": "tag", "values": WCAG_TAGS}},
    )

    if results.violations_count == 0:
        return None

    return (
        f"axe found {results.violations_count} accessibility "
        f"violation(s) on {page_name}:\n{results.generate_report()}"
    )


def assert_no_axe_violations(page: Page, page_name: str) -> None:
    report = collect_axe_violations(page, page_name)
    assert report is None, report
