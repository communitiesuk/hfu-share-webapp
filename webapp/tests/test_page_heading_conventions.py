import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

# Templates that still hardcode a page heading literal. This list is a
# ratchet: entries may be removed as templates move to view-declared
# headings (PageTitleMixin), never added. New templates take their heading
# from the view via page_heading in context.
HARDCODED_HEADING_ALLOWLIST = {
    "accommodation_requests/templates/accommodation_requests/accommodation_requests_list_page_base.html",
    "accommodations/templates/accommodations/accommodations_list_page_base.html",
    "accounts/templates/accounts/login.html",
    "deduplication/templates/select_duplicate_record_type.html",
    "downloads/templates/downloads/download.html",
    "guests/templates/guests/guests_list_page_base.html",
    "reassignment_requests/templates/reassignment_requests/cancel_request_view.html",
    "reassignment_requests/templates/reassignment_requests/detail_view.html",
    "reassignment_requests/templates/reassignment_requests/reassignment_requests_tabs_view_base.html",
    "safeguarding/templates/safeguarding/detail_view/central_safeguarding/check_detail.html",
    "safeguarding/templates/safeguarding/escalated_checks_list.html",
    "sponsors/templates/sponsors/sponsors_list_page_base.html",
    "templates/403.html",
    "templates/404.html",
    "templates/500.html",
    "uams/templates/uams/uams_list_page_base.html",
    "unassigned_accommodation_requests/templates/unassigned_accommodation_requests/unassigned_accommodation_requests_list_page_base.html",
    "user_management/templates/user_management/access_request_form/access_request_form_intro.html",
    "user_management/templates/user_management/access_requests/access_requests_your_request_page.html",
    "user_management/templates/user_management/base.html",
    "visa_applications/templates/visa_applications/detail_view/vir/vir_close_confirm.html",
    "visa_applications/templates/visa_applications/detail_view/vir/vir_reopen_confirm.html",
    "visa_applications/templates/visa_applications/virs.html",
    "visa_applications/templates/visa_applications/visa_applications.html",
    "webapp/templates/webapp/pages/accessibility_statement/accessibility_statement.html",
    "webapp/templates/webapp/pages/cookies/cookies.html",
}

HARDCODED_HEADING_RE = re.compile(r'page_heading="')


class PageHeadingConventionTest(SimpleTestCase):
    def _template_paths(self):
        base = Path(settings.BASE_DIR)
        skip_parts = {".venv", "node_modules", "staticfiles"}

        for path in base.glob("**/templates/**/*.html"):
            if set(path.parts) & skip_parts:
                continue
            yield path

    def test_no_new_hardcoded_page_headings(self):
        offenders = []

        for path in self._template_paths():
            relative_path = str(path.relative_to(settings.BASE_DIR))
            if relative_path in HARDCODED_HEADING_ALLOWLIST:
                continue
            if HARDCODED_HEADING_RE.search(path.read_text()):
                offenders.append(relative_path)

        self.assertEqual(
            sorted(offenders),
            [],
            "\n\nThese templates hardcode a page heading literal. Declare the "
            "heading on the view instead (PageTitleMixin / page_heading in "
            "context) so the browser title and the heading share one source. "
            "See webapp/mixins.py:\n" + "\n".join(sorted(offenders)),
        )

    def test_allowlist_contains_no_migrated_templates(self):
        base = Path(settings.BASE_DIR)
        stale = [
            relative_path
            for relative_path in sorted(HARDCODED_HEADING_ALLOWLIST)
            if not (base / relative_path).exists()
            or not HARDCODED_HEADING_RE.search((base / relative_path).read_text())
        ]

        self.assertEqual(
            stale,
            [],
            "\n\nThese templates no longer hardcode a page heading (or no "
            "longer exist). Remove them from HARDCODED_HEADING_ALLOWLIST so "
            "the ratchet only tightens:\n" + "\n".join(stale),
        )
