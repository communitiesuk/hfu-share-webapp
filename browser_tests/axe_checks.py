from axe_playwright_python.sync_playwright import Axe

from .pages.share_page import SharePage

WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]


def collect_axe_violations(page: SharePage, page_name: str) -> str | None:
    results = Axe().run(
        page.page,
        options={
            "runOnly": {"type": "tag", "values": WCAG_TAGS},
            "exclude": [["#djDebug"]],
        },
    )

    if results.violations_count == 0:
        return None

    return (
        f"axe found {results.violations_count} accessibility "
        f"violation(s) on {page_name}:\n{results.generate_report()}"
    )


def assert_no_axe_violations(page: SharePage, page_name: str) -> None:
    report = collect_axe_violations(page, page_name)
    assert report is None, report
