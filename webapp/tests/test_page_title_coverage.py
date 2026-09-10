from types import SimpleNamespace
from typing import cast

from django.test import SimpleTestCase
from django.urls import ResolverMatch, get_resolver

from case_management.page_title import get_tab_title
from webapp.mixins import PageTitleMixin

SKIPPED_ROUTE_PREFIXES = ("admin/", "__debug__", "assets/")

# Views whose pages are identified by their section title alone, or which do
# not render a page at all (file downloads, redirects, endpoints). This list
# is a ratchet: entries may be removed as views gain a declared page
# identity (PageTitleMixin, get_step_heading, or a TAB_MAP tab), never
# added. A new view must declare its identity or be consciously added here
# in review.
SECTION_TITLE_ONLY_ALLOWLIST = {
    "accommodation_requests.views.AccommodationRequestCloseForGuests",
    "accommodation_requests.views.AccommodationRequestCommentsDownloadAttachmentView",
    "accommodation_requests.views.AccommodationRequestInteractionsDownloadAttachmentView",
    "accommodation_requests.views.AccommodationRequestReopenRequestView",
    "accommodation_requests.views.AccommodationRequestWithdrawSponsorView",
    "accommodations.views.AccommodationEditView",
    "accommodations.views.PostcodeSearchView",
    "deduplication.views.SelectRecordTypeView",
    "django.views.generic.base.TemplateView",
    "downloads.views.DownloadsPage",
    "guests.views.GuestEditView",
    "reassignment_requests.views.CancelReassignmentRequestView",
    "reassignment_requests.views.ReassignmentRequestDetailView",
    "safeguarding.views.DownloadEscalatedChecksCSVView",
    "safeguarding.views.EscalatedChecksView",
    "sponsors.views.SponsorEditView",
    "uams.views.UamsDownloadAttachmentView",
    "uams.views.UamsDownloadGOVUKFormsAttachmentView",
    "unassigned_accommodation_requests.views.HideUnassignedAccommodationRequestView",
    "unassigned_accommodation_requests.views.UnhideUnassignedAccommodationRequestView",
    "user_management.views.access_requests_views.AccessRequestHideRequest",
    "user_management.views.access_requests_views.AccessRequestYourRequestView",
    "user_management.views.access_requests_views.AccessRequestsDetailsPage",
    "user_management.views.form_wizard_views.AccessRequestFormConfirmationPageView",
    "user_management.views.form_wizard_views.AccessRequestFormWizard",
    "user_management.views.groups_views.GroupDetailsView",
    "user_management.views.groups_views.GroupRemoveUserView",
    "user_management.views.intro_views.AccessRequestIntroView",
    "user_management.views.users_views.UserDetailsView",
    "user_management.views.users_views.UserRemoveGroupView",
    "visa_applications.views.VIRCloseConfirmView",
    "visa_applications.views.VIRReopenConfirmView",
    "webapp.views.AccessibilityStatementView",
    "webapp.views.CSPReportView",
    "webapp.views.CookiesView",
    "webapp.views.LandingPageView",
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
        if route.startswith(SKIPPED_ROUTE_PREFIXES):
            continue
        view_class = getattr(callback, "view_class", None)
        if view_class is None or view_class in seen:
            continue
        seen.add(view_class)
        yield view_class


def has_page_identity(view_class) -> bool:
    if issubclass(view_class, PageTitleMixin):
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
            and dotted_path(view_class) not in SECTION_TITLE_ONLY_ALLOWLIST
        )

        self.assertEqual(
            missing,
            [],
            "\n\nThese views declare no page identity for the browser title. "
            "Give each a PageTitleMixin page_heading (or WizardPageTitleMixin "
            "step_headings for wizards), or add it to "
            "SECTION_TITLE_ONLY_ALLOWLIST if the "
            "section title alone identifies the page:\n" + "\n".join(missing),
        )

    def test_allowlist_contains_no_compliant_views(self):
        known = {dotted_path(view_class) for view_class in class_based_views()}
        compliant = {
            dotted_path(view_class)
            for view_class in class_based_views()
            if has_page_identity(view_class)
        }
        stale = sorted(
            path
            for path in SECTION_TITLE_ONLY_ALLOWLIST
            if path not in known or path in compliant
        )

        self.assertEqual(
            stale,
            [],
            "\n\nThese allowlist entries are no longer needed (view removed "
            "or now declares a page identity). Remove them so the ratchet "
            "only tightens:\n" + "\n".join(stale),
        )
