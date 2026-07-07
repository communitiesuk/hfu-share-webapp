from pylint.checkers import BaseChecker


class ViewAccessControlChecker(BaseChecker):
    name = "check-view-access-control"
    msgs = {
        "W1351": (
            "View class lacks explicit access control mixin",
            "view-missing-access-control",
            "View classes should inherit from PermissionsMixin or "
            "GroupRequiredMixin to enforce access restrictions and "
            "prevent unauthorised access",
        )
    }

    def visit_classdef(self, node):
        parent_classes = set(base.name for base in node.ancestors(recurs=True))
        if "View" in parent_classes and "GroupRequiredMixin" not in parent_classes:
            self.add_message("view-missing-access-control", node=node)


class LocalAuthorityAccessChecker(BaseChecker):
    name = "check-local-authority-access"
    msgs = {
        "W1352": (
            "View class inheriting from SingleObjectMixin or "
            "MultipleObjectMixin lacks LocalAuthorityAccessMixin",
            "view-missing-local-authority-access",
            "Views that inherit from SingleObjectMixin or "
            "MultipleObjectMixin should also "
            "inherit from LocalAuthorityAccessMixin or "
            "PermissionsMixin to ensure proper "
            "queryset filtering and prevent unauthorized object "
            "access",
        )
    }

    def visit_classdef(self, node):
        parent_classes = set(base.name for base in node.ancestors(recurs=True))

        object_mixins = {"SingleObjectMixin", "MultipleObjectMixin"}
        has_object_mixin = bool(object_mixins & parent_classes)

        access_control_mixins = {"LocalAuthorityAccessMixin", "PermissionsMixin"}
        has_access_control = bool(access_control_mixins & parent_classes)

        if has_object_mixin and not has_access_control:
            self.add_message("view-missing-local-authority-access", node=node)


def register(linter):
    linter.register_checker(ViewAccessControlChecker(linter))
    linter.register_checker(LocalAuthorityAccessChecker(linter))
