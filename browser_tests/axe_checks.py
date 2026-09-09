from axe_playwright_python.sync_playwright import Axe

from .pages.share_page import SharePage

WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]

KNOWN_ISSUES = [
    # govuk-frontend deliberately sets aria-expanded on radios with
    # conditional reveals, see https://github.com/alphagov/govuk-frontend/issues/979
    {
        "rule": "aria-allowed-attr",
        "html_contains": ("govuk-radios__input", "aria-expanded"),
    },
    # A known false positive as the skip link does not need to apear in a landmark (see https://design-system.service.gov.uk/components/skip-link/#when-to-use-this-component)
    {
        "rule": "region",
        "html_contains": ("govuk-skip-link",),
    },
]


def _is_known_issue(violation_id: str, node: dict) -> bool:
    return any(
        violation_id == issue["rule"]
        and all(marker in node["html"] for marker in issue["html_contains"])
        for issue in KNOWN_ISSUES
    )


def _filter_known_issues(response: dict) -> None:
    remaining = []
    for violation in response["violations"]:
        nodes = [
            node
            for node in violation["nodes"]
            if not _is_known_issue(violation["id"], node)
        ]
        if nodes:
            remaining.append({**violation, "nodes": nodes})
    response["violations"] = remaining


def collect_axe_violations(page: SharePage, page_name: str) -> str | None:
    results = Axe().run(
        page.page,
        options={
            "runOnly": {"type": "tag", "values": WCAG_TAGS},
            "exclude": [
                # Django debug toolbar which only apears on dev so should be exluded
                ["#djDebug"],
            ],
        },
    )

    _filter_known_issues(results.response)

    if results.violations_count == 0:
        return None

    return (
        f"axe found {results.violations_count} accessibility "
        f"violation(s) on {page_name}:\n{results.generate_report()}"
    )


def assert_no_axe_violations(page: SharePage, page_name: str) -> None:
    report = collect_axe_violations(page, page_name)
    assert report is None, report
