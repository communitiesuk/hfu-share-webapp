import re

import astroid
from pylint.checkers import BaseChecker

# Link or button text that says nothing about what it acts on. A screen
# reader user browsing a list of links hears only this word, so it must be
# accompanied by visually hidden text naming the target, e.g.
#   Remove<span class="govuk-visually-hidden"> John Smith</span>
GENERIC_WORDS = [
    "change",
    "select",
    "remove",
    "edit",
    "view",
    "start",
    "hide",
    "unhide",
    "delete",
    "update",
    "add",
    "download",
    "download file",
    "show more",
    "show less",
    "re-open",
    "reopen",
    "more",
    "here",
    "click here",
    "read more",
    "learn more",
]

# Matches markup like ">Remove</a>" or "> Change </button>": a link or
# button whose entire text is one of the generic words above.
GENERIC_LINK_RE = re.compile(
    r">\s*(?:"
    + "|".join(re.escape(word) for word in GENERIC_WORDS)
    + r")\s*</(?:a|button)>",
    re.IGNORECASE,
)


class GenericLinkTextChecker(BaseChecker):
    name = "generic-link-text"
    msgs = {
        "W1353": (
            "Link or button text is a bare generic word, add a "
            "govuk-visually-hidden span describing the target",
            "generic-link-text-in-format-html",
            "Screen reader users browse links out of context, so generic text "
            "like 'Change' or 'Remove' needs visually hidden text saying what "
            "it acts on",
        )
    }

    def visit_call(self, node):
        if self._called_function_name(node) not in ("format_html", "format_html_join"):
            return
        if not node.args:
            return

        html = self._literal_string(node.args[0])
        if html is None:
            return
        if "govuk-visually-hidden" in html:
            return

        if GENERIC_LINK_RE.search(html):
            self.add_message("generic-link-text-in-format-html", node=node)

    def _called_function_name(self, node):
        if isinstance(node.func, astroid.Name):
            return node.func.name
        if isinstance(node.func, astroid.Attribute):
            return node.func.attrname
        return None

    def _literal_string(self, node):
        # A plain string literal. Adjacent literals ('...' '...') are already
        # one string by the time pylint sees them.
        if isinstance(node, astroid.Const) and isinstance(node.value, str):
            return node.value
        # String literals joined with +.
        if isinstance(node, astroid.BinOp) and node.op == "+":
            left = self._literal_string(node.left)
            right = self._literal_string(node.right)
            if left is not None and right is not None:
                return left + right
        return None


def register(linter):
    linter.register_checker(GenericLinkTextChecker(linter))
