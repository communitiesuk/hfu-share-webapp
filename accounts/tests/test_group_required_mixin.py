import http.client

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from accounts.enums import GroupType
from accounts.tests.base import GroupRequiredMixinBaseTestCase


class GroupRequiredMixinTest(GroupRequiredMixinBaseTestCase):
    def test_exception_raised_when_view_incorrectly_configured(self):
        view = self.get_incorrectly_configured_view()
        request = RequestFactory().get("/")
        request.user = self.get_user_with_groups(group_names=["any_group"])

        with self.assertRaises(Exception) as context:
            view.as_view()(request)

        self.assertIn(
            "No group name or group type configured for GroupRequiredMixin",
            str(context.exception),
        )

    def test_access_denied_to_user_without_group(self):
        request = RequestFactory().get("/")
        request.user = self.get_user_with_groups(group_names=["not_the_test_group"])
        view = self.get_view_that_requires_groups(["test_group"])

        with self.assertRaises(Exception) as exc:
            view.as_view()(request)
        self.assertIn("not found", str(exc.exception).lower())

    def test_access_allowed_to_user_with_group(self):
        request = RequestFactory().get("/")
        request.user = self.get_user_with_groups(group_names=["test_group"])
        view = self.get_view_that_requires_groups(["test_group"])

        response = view.as_view()(request)
        self.assertEqual(response.status_code, http.client.OK)

    def test_access_denied_to_user_without_all_groups(self):
        request = RequestFactory().get("/")
        request.user = self.get_user_with_groups(group_names=["test_group"])
        view = self.get_view_that_requires_groups(
            ["test_group", "the_other_test_group"]
        )
        view.all_groups_required = True

        with self.assertRaises(Exception) as exc:
            view.as_view()(request)
        self.assertIn("not found", str(exc.exception).lower())

    def test_access_allowed_to_user_with_all_groups(self):
        request = RequestFactory().get("/")
        request.user = self.get_user_with_groups(
            group_names=["test_group", "the_other_test_group", "irrelevant_group"]
        )
        view = self.get_view_that_requires_groups(
            ["test_group", "the_other_test_group"]
        )
        view.all_groups_required = True

        response = view.as_view()(request)
        self.assertEqual(response.status_code, http.client.OK)

    def test_access_allowed_to_user_with_group_type(self):
        request = RequestFactory().get("/")
        user = self.get_user_with_group_types([GroupType.DEV])
        request.user = user
        view = self.get_view_that_requires_group_types([GroupType.DEV])
        response = view.as_view()(request)
        self.assertEqual(response.status_code, http.client.OK)

    def test_access_denied_to_user_without_group_type(self):
        request = RequestFactory().get("/")
        user = self.get_user_with_group_types([GroupType.MHCLG])
        request.user = user
        view = self.get_view_that_requires_group_types([GroupType.DEV])
        with self.assertRaises(PermissionDenied):
            view.as_view()(request)

    def test_access_denied_with_deny_mode(self):
        request = RequestFactory().get("/")
        request.user = self.get_user_with_groups(group_names=["test_group"])
        view = self.get_view_that_requires_groups(["test_group"], mode=self.DENY)
        with self.assertRaises(Exception) as exc:
            view.as_view()(request)
        self.assertIn("not found", str(exc.exception).lower())

    def test_access_allowed_with_deny_mode(self):
        request = RequestFactory().get("/")
        request.user = self.get_user_with_groups(group_names=["some_unrelated_group"])
        view = self.get_view_that_requires_groups(["test_group"], mode=self.DENY)
        response = view.as_view()(request)
        self.assertEqual(response.status_code, http.client.OK)

    def test_access_allowed_with_deny_mode_user_in_no_groups(self):
        request = RequestFactory().get("/")
        request.user = self.get_user_with_groups(group_names=[])
        view = self.get_view_that_requires_groups(["test_group"], mode=self.DENY)
        response = view.as_view()(request)
        self.assertEqual(response.status_code, http.client.OK)

    def test_access_allowed_with_both_group_name_and_type(self):
        request = RequestFactory().get("/")
        user = self.get_user_with_groups(group_names=["test_group"])
        request.user = user
        view = self.get_view_that_requires_groups_and_types(
            ["test_group"], [GroupType.DEV]
        )
        response = view.as_view()(request)
        self.assertEqual(response.status_code, http.client.OK)

    def test_admin_group_returns_403(self):
        request = RequestFactory().get("/")
        request.user = self.get_user_with_groups(group_names=["not_dev"])
        view = self.get_view_that_requires_groups(["dev"])
        with self.assertRaises(PermissionDenied):
            view.as_view()(request)

    def test_view_with_admin_and_nonadmin_group_names_is_not_admin_only(self):
        request = RequestFactory().get("/")
        request.user = self.get_user_with_groups(group_names=["not_dev"])
        view = self.get_view_that_requires_groups(["dev", "other"])

        with self.assertRaises(Exception) as exc:
            view.as_view()(request)
        self.assertIn("not found", str(exc.exception).lower())

    def test_view_with_admin_group_name_and_type_is_admin_only(self):
        request = RequestFactory().get("/")
        request.user = self.get_user_with_groups(group_names=["not_dev"])
        view = self.get_view_that_requires_groups_and_types(["dev"], [GroupType.DEV])

        with self.assertRaises(PermissionDenied):
            view.as_view()(request)

    def test_view_with_only_admin_group_type_is_admin_only(self):
        request = RequestFactory().get("/")
        user = self.get_user_with_group_types([GroupType.HOME_OFFICE])
        request.user = user
        view = self.get_view_that_requires_groups_and_types([], [GroupType.DEV])

        with self.assertRaises(PermissionDenied):
            view.as_view()(request)

    def test_view_with_only_admin_group_name_is_admin_only(self):
        request = RequestFactory().get("/")
        request.user = self.get_user_with_groups(group_names=["not_dev"])
        view = self.get_view_that_requires_groups_and_types(["dev"], [])

        with self.assertRaises(PermissionDenied):
            view.as_view()(request)
