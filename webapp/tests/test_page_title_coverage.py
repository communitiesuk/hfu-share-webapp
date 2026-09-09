from types import SimpleNamespace
from typing import cast

from django.test import SimpleTestCase
from django.urls import ResolverMatch, get_resolver

from case_management.page_title import get_tab_title
from webapp.mixins import PageTitleMixin

SKIPPED_ROUTE_PREFIXES = ("admin/", "__debug__", "assets/")
HOME_ROUTES = ("", "landing-page")

# Endpoints and redirects that render no page, so a page identity would be
# meaningless: file downloads, POST-and-redirect actions and report sinks.
NON_PAGE_VIEWS = {
    "accommodation_requests.views.AccommodationRequestCommentsDownloadAttachmentView",
    "accommodation_requests.views.AccommodationRequestInteractionsDownloadAttachmentView",
    "accommodations.views.PostcodeSearchView",
    "safeguarding.views.DownloadEscalatedChecksCSVView",
    "uams.views.UamsDownloadAttachmentView",
    "uams.views.UamsDownloadGOVUKFormsAttachmentView",
    "unassigned_accommodation_requests.views.HideUnassignedAccommodationRequestView",
    "unassigned_accommodation_requests.views.UnhideUnassignedAccommodationRequestView",
    "user_management.views.access_requests_views.AccessRequestHideRequest",
    "webapp.views.CSPReportView",
}


def class_based_views():
    def walk(resolver, prefix=""):
        for entry in resolver.url_patterns:
            if hasattr(entry, "url_patterns"):
                yield from walk(entry, prefix + str(entry.pattern))
            else:
                yield prefix + str(entry.pattern), entry.callback

    seen = set()
    for route, callback in walk(get_resolver()):
        if route.startswith(SKIPPED_ROUTE_PREFIXES) or route in HOME_ROUTES:
            continue
        view_class = getattr(callback, "view_class", None)
        if view_class is None or view_class in seen:
            continue
        seen.add(view_class)
        yield view_class


def has_page_identity(view_class) -> bool:
    if issubclass(view_class, PageTitleMixin):
        return True
    if hasattr(view_class, "get_step_heading"):
        return True
    stub_match = cast(
        ResolverMatch, SimpleNamespace(_func_path=dotted_path(view_class))
    )
    return bool(get_tab_title(stub_match))


def dotted_path(view_class) -> str:
    return f"{view_class.__module__}.{view_class.__qualname__}"


class PageTitleCoverageTest(SimpleTestCase):
    def test_every_view_declares_a_page_identity_or_is_allowlisted(self):
        missing = sorted(
            dotted_path(view_class)
            for view_class in class_based_views()
            if not has_page_identity(view_class)
            and dotted_path(view_class) not in NON_PAGE_VIEWS
        )

        self.assertEqual(
            missing,
            [],
            "\n\nThese views declare no page identity for the browser title. "
            "Give each a PageTitleMixin page_heading (or get_step_heading for "
            "wizards), or add it to NON_PAGE_VIEWS if the "
            "section title alone identifies the page:\n" + "\n".join(missing),
        )

    def test_non_page_list_contains_no_compliant_views(self):
        known = {dotted_path(view_class) for view_class in class_based_views()}
        compliant = {
            dotted_path(view_class)
            for view_class in class_based_views()
            if has_page_identity(view_class)
        }
        stale = sorted(
            path for path in NON_PAGE_VIEWS if path not in known or path in compliant
        )

        self.assertEqual(
            stale,
            [],
            "\n\nThese allowlist entries are no longer needed (view removed "
            "or now declares a page identity). Remove them so the ratchet "
            "only tightens:\n" + "\n".join(stale),
        )
