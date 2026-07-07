from typing import Protocol

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest

from accounts.enums import GroupType


class GroupRequiredMixinProtocol(Protocol):
    request: HttpRequest
    group_name: str | list[str] | None


def user_in_all_group_names(user, group_names):
    if not group_names:
        return True
    user_group_names = set(user.groups.values_list("name", flat=True))
    return all(name in user_group_names for name in group_names)


def user_in_any_group_names(user, group_names):
    if not group_names:
        return True
    return user.groups.filter(name__in=group_names).exists()


def user_in_all_group_types(user, group_types):
    if not group_types:
        return True
    user_group_types = set(user.groups.values_list("groupinfo__group_type", flat=True))
    return all(gt in user_group_types for gt in group_types)


def user_in_any_group_types(user, group_types):
    if not group_types:
        return True
    if hasattr(user, "is_in_group_types"):
        return user.is_in_group_types(group_types)
    return user.groups.filter(groupinfo__group_type__in=group_types).exists()


def user_has_group_with_type(user, group_type):
    if hasattr(user, "is_in_group_types"):
        return user.is_in_group_types([group_type])
    return user.groups.filter(groupinfo__group_type=group_type).exists()


class GroupRequiredMixin(UserPassesTestMixin):
    """
    Add to class based view to only allow access to users with the specified
    group(s) or group type(s).

    Usage:
    - `group_name` (str or list): allow/deny access for specific groups.
    - `group_type` (GroupType or list): allow/deny access for group types.
    - `group_access_mode`: "ALLOW" (default) or "DENY".
    - `all_groups_required`: if True, user must belong to all specified.
    - If admin-only views unauthorized users get 403.
    - In all other views unauthorized users get 404.
    """

    ADMIN_GROUP_NAMES = ["dev"]
    ADMIN_GROUP_TYPES = [GroupType.DEV]
    ALLOW = "allow"
    DENY = "deny"

    group_type: str | GroupType | list[GroupType] | None = None
    group_name: str | list[str] | None = None
    group_access_mode: str = ALLOW  # can be 'ALLOW' or 'DENY'
    all_groups_required: bool = False

    def get_group_type(self):
        if hasattr(self, "group_type") and self.group_type is not None:
            return (
                self.group_type
                if isinstance(self.group_type, (list, tuple, set))
                else [self.group_type]
            )
        return []

    @property
    def normalized_group_names(self):
        if self.group_name is None:
            return []
        return (
            self.group_name
            if isinstance(self.group_name, (list, tuple, set))
            else [self.group_name]
        )

    def test_func(self, *args, **kwargs):
        user = self.request.user
        group_names = self.normalized_group_names
        group_types = self.get_group_type()
        mode = getattr(self, "group_access_mode", self.ALLOW)
        all_required = getattr(self, "all_groups_required", False)
        if not group_names and not group_types:
            raise RuntimeError(
                "No group name or group type configured for GroupRequiredMixin"
            )

        if all_required:
            in_names = user_in_all_group_names(user, group_names)
            in_types = user_in_all_group_types(user, group_types)
        else:
            in_names = user_in_any_group_names(user, group_names)
            in_types = user_in_any_group_types(user, group_types)

        if mode == self.DENY:
            if group_names and in_names:
                return False
            if group_types and in_types:
                return False
            return True

        if group_names and in_names:
            return True
        if group_types and in_types:
            return True
        return False

    def handle_no_permission(self):
        group_names = self.normalized_group_names
        group_types = self.get_group_type()
        is_admin_view = (
            (group_names == self.ADMIN_GROUP_NAMES and not group_types)
            or (group_types == self.ADMIN_GROUP_TYPES and not group_names)
            or (
                group_names == self.ADMIN_GROUP_NAMES
                and group_types == self.ADMIN_GROUP_TYPES
            )
        )
        if is_admin_view:
            raise PermissionDenied("You do not have permission to access this page.")
        raise Http404("Page not found")


class AdminAccessRequiredMixin(GroupRequiredMixin):
    """
    Add to class based views to only allow access to user's with the `dev` group
    """

    group_name = "dev"
