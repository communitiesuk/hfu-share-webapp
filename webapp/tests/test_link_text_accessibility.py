import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from hfurb_scripts.lint_extras.check_generic_link_text import GENERIC_WORDS

GENERIC_TEXTS = set(GENERIC_WORDS)

# Template path to link texts that are allowed to stay bare on that page,
# for the rare case where the surrounding page makes the purpose unambiguous,
# e.g.:
# ALLOWED = {
#     "user_management/templates/user_management/access_request_form/"
#     "access_request_form_intro.html": {"start"},
# }
ALLOWED: dict[str, set[str]] = {}

LINK_RE = re.compile(r"<(a|button)\b[^>]*>(.*?)</\1>", re.S | re.I)
TEMPLATE_TAG_RE = re.compile(r"{%.*?%}")
HTML_TAG_RE = re.compile(r"<[^>]+>")


class LinkTextAccessibilityTest(SimpleTestCase):
    def test_no_bare_generic_link_or_button_text_in_templates(self):
        failures = []

        for path in self._template_paths():
            relative_path = str(path.relative_to(settings.BASE_DIR))
            content = path.read_text()

            for match in LINK_RE.finditer(content):
                text = self._link_text(match.group(2))

                if text is None or text not in GENERIC_TEXTS:
                    continue
                if text in ALLOWED.get(relative_path, set()):
                    continue

                line = content[: match.start()].count("\n") + 1
                failures.append(f"{relative_path}:{line}: bare link text {text!r}")

        self.assertEqual(
            failures,
            [],
            "\n\nLinks and buttons with generic text need visually hidden "
            'context, e.g. Change<span class="govuk-visually-hidden"> record '
            "details</span>. Add the span, or add an entry to ALLOWED if the "
            "bare text is unambiguous on its page:\n" + "\n".join(failures),
        )

    def _template_paths(self):
        base = Path(settings.BASE_DIR)
        skip_parts = {".venv", "node_modules", "staticfiles"}

        for path in base.glob("**/templates/**/*.html"):
            parts = set(path.parts)
            if parts & skip_parts:
                continue
            if "admin" in path.relative_to(base).parts:
                continue
            yield path

    def _link_text(self, inner_html):
        if "govuk-visually-hidden" in inner_html:
            return None

        without_template_tags = TEMPLATE_TAG_RE.sub(" ", inner_html)
        if "{{" in without_template_tags:
            return None

        text = HTML_TAG_RE.sub(" ", without_template_tags)
        return re.sub(r"\s+", " ", text).strip().lower()
