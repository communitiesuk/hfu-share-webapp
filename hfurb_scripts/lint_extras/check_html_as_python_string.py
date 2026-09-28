import re
from pathlib import Path

from pylint.checkers import BaseChecker

HTML_TAG_PATTERN = re.compile(
    r"</?(?:div|span|a|p|ul|li|table|tr|td|th|strong|em|button|input)\b",
    re.IGNORECASE,
)
IGNORED_DIRS = {
    "tests",
    "venv",
    ".venv",
}


class HTMLAsPythonStringChecker(BaseChecker):
    name = "html-in-python-string"
    msgs = {
        "W1354": (
            "HTML detected in Python string",
            "html-in-python-string",
            "Move HTML into a template and use render_to_string.",
        )
    }

    def _should_ignore(self, node) -> bool:
        path = Path(node.root().file)

        return bool(set(path.parts) & IGNORED_DIRS)

    def visit_const(self, node):
        if self._should_ignore(node) or not isinstance(node.value, str):
            return

        if HTML_TAG_PATTERN.search(node.value):
            self.add_message(
                "html-in-python-string",
                node=node,
            )

    def visit_joinedstr(self, node):
        if self._should_ignore(node):
            return

        text_parts = []

        for value in node.values:
            if hasattr(value, "value"):
                text_parts.append(str(value.value))

        text = "".join(text_parts)

        if HTML_TAG_PATTERN.search(text):
            self.add_message(
                "html-in-python-string",
                node=node,
            )


def register(linter):
    linter.register_checker(HTMLAsPythonStringChecker(linter))
