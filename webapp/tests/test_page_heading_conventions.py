import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

# Error pages are rendered by Django's error handlers, so there is no view
# class to declare their headings on.
VIEWLESS_ERROR_TEMPLATES = {
    "templates/403.html",
    "templates/404.html",
    "templates/500.html",
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
            if relative_path in VIEWLESS_ERROR_TEMPLATES:
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

    def test_error_template_exceptions_still_apply(self):
        base = Path(settings.BASE_DIR)
        stale = [
            relative_path
            for relative_path in sorted(VIEWLESS_ERROR_TEMPLATES)
            if not (base / relative_path).exists()
            or not HARDCODED_HEADING_RE.search((base / relative_path).read_text())
        ]

        self.assertEqual(
            stale,
            [],
            "\n\nThese error templates no longer hardcode a page heading (or no "
            "longer exist). Remove them from VIEWLESS_ERROR_TEMPLATES:\n"
            + "\n".join(stale),
        )
