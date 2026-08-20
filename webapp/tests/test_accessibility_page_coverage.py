from django.test import SimpleTestCase
from django.urls import get_resolver

from browser_tests.accessibility_pages import (
    ELEVATED_ACCESS_PAGES,
    NOT_SCANNABLE,
    STATIC_PAGES,
)

SKIPPED_PREFIXES = ("/admin/", "/__debug__/", "/assets/")


def parameterless_paths():
    def walk(resolver, prefix=""):
        for entry in resolver.url_patterns:
            pattern = str(entry.pattern)
            if hasattr(entry, "url_patterns"):
                yield from walk(entry, prefix + pattern)
            else:
                yield prefix + pattern

    for path in sorted(set(walk(get_resolver()))):
        path = "/" + path
        if "<" in path or "(" in path:
            continue
        if path.startswith(SKIPPED_PREFIXES):
            continue
        yield path


class AccessibilityPageCoverageTest(SimpleTestCase):
    def test_every_parameterless_page_is_axe_scanned_or_excluded(self):
        covered = (
            {path for path, _ in STATIC_PAGES}
            | {path for path, _ in ELEVATED_ACCESS_PAGES}
            | NOT_SCANNABLE
        )
        missing = [path for path in parameterless_paths() if path not in covered]

        self.assertEqual(
            missing,
            [],
            "\n\nThese pages are not covered by the axe accessibility browser "
            "tests. Add each one to STATIC_PAGES in "
            "browser_tests/accessibility_pages.py so it gets scanned, to "
            "NOT_SCANNABLE if it is not a real page (an API endpoint, "
            "redirect or file download), or to ELEVATED_ACCESS_PAGES "
            "if only an admin user can access it:\n" + "\n".join(missing),
        )

    def test_page_lists_contain_no_stale_paths(self):
        known = set(parameterless_paths())
        listed = (
            {path for path, _ in STATIC_PAGES}
            | {path for path, _ in ELEVATED_ACCESS_PAGES}
            | NOT_SCANNABLE
        )
        stale = sorted(listed - known)

        self.assertEqual(
            stale,
            [],
            "\n\nThese paths are listed in browser_tests/accessibility_pages.py "
            "but no longer exist in any urls.py, remove them:\n" + "\n".join(stale),
        )
