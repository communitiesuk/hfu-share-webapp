from typing import cast

from django.contrib.auth.models import Group
from django.test import TestCase
from django.views.generic import TemplateView

from accounts.mixins import AdminAccessRequiredMixin, GroupRequiredMixin
from accounts.models import User
from accounts.tests.factories import GroupFactory, UserFactory


class GroupRequiredMixinBaseTestCase(TestCase):
    ADMIN_GROUP_NAME = "dev"
    ALLOW = "allow"
    DENY = "deny"

    def get_user_with_groups(self, group_names: list[str]):
        user = cast(User, UserFactory())
        for group_name in group_names:
            group = cast(Group, GroupFactory(name=group_name))
            user.groups.add(group)
        return user

    def get_view_that_requires_groups(
        self, group_names: list[str], mode: str = "allow"
    ):
        class TestGroupRequiredMixinView(GroupRequiredMixin, TemplateView):
            group_name = group_names
            group_access_mode = mode
            template_name = "base.html"

        return TestGroupRequiredMixinView

    def get_view_that_requires_admin_access(self):
        class TestAdminAccessRequiredMixinView(AdminAccessRequiredMixin, TemplateView):
            template_name = "base.html"

        return TestAdminAccessRequiredMixinView

    def get_incorrectly_configured_view(self):
        class TestGroupRequiredMixinView(GroupRequiredMixin, TemplateView):
            template_name = "base.html"

        return TestGroupRequiredMixinView

    def get_user_with_group_types(self, group_types: list):
        user = cast(User, UserFactory())
        for group_type in group_types:
            group = cast(Group, GroupFactory())
            groupinfo = getattr(group, "groupinfo", None)
            if groupinfo:
                groupinfo.group_type = group_type
                groupinfo.save()
            else:
                group = cast(Group, GroupFactory(group_type=group_type))
            user.groups.add(group)
        return user

    def get_view_that_requires_group_types(self, group_types: list):
        class TestGroupTypeRequiredView(GroupRequiredMixin, TemplateView):
            group_type = group_types
            template_name = "base.html"

        return TestGroupTypeRequiredView

    def get_view_that_requires_groups_and_types(
        self, group_names: list, group_types: list
    ):
        class TestGroupAndTypeRequiredView(GroupRequiredMixin, TemplateView):
            group_name = group_names
            group_type = group_types
            template_name = "base.html"

        return TestGroupAndTypeRequiredView

    def get_view_with_no_group_config(self):
        class TestNoGroupConfigView(GroupRequiredMixin, TemplateView):
            template_name = "base.html"

        return TestNoGroupConfigView


class TestSessionTokenMixin:
    def setUp(self):
        super().setUp()
        session = self.client.session
        session["id_token_claims"] = {"exp": 32514183503}
        session.save()
