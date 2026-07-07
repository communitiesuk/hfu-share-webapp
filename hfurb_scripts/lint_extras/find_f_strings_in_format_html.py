import astroid
from pylint.checkers import BaseChecker


class FormatHTMLFStringChecker(BaseChecker):
    name = "no-f-string-in-format-html"
    msgs = {
        "W1350": (
            "Uses f string in call to format_html, use placeholders instead",
            "f-string-in-format-html",
            "This is an XSS vulnerability, use placeholders and arguments instead",
        )
    }

    def visit_call(self, node):
        func = node.func

        if (isinstance(func, astroid.Name) and func.name == "format_html") or (
            isinstance(func, astroid.Attribute) and func.attrname == "format_html"
        ):
            if node.args and isinstance(node.args[0], astroid.JoinedStr):
                self.add_message("f-string-in-format-html", node=node)


def register(linter):
    linter.register_checker(FormatHTMLFStringChecker(linter))
