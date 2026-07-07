import http.client

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from accounts.tests.base import GroupRequiredMixinBaseTestCase


class AdminAccessRequiredMixinTestCase(GroupRequiredMixinBaseTestCase):
    def test_access_denied_to_user_without_admin_group(self):
        request = RequestFactory().get("/")
        request.user = self.get_user_with_groups(group_names=["not_the_admin_group"])
        view = self.get_view_that_requires_admin_access()

        with self.assertRaises(PermissionDenied):
            view.as_view()(request)

    def test_access_allowed_to_user_with_admin_group(self):
        request = RequestFactory().get("/")
        request.user = self.get_user_with_groups(group_names=[self.ADMIN_GROUP_NAME])
        view = self.get_view_that_requires_admin_access()

        response = view.as_view()(request)
        self.assertEqual(response.status_code, http.client.OK)
