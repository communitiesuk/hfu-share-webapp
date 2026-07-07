import http.client

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from accounts.tests.factories import GroupFactory
from user_management.tests.base import get_admin_user, get_la_user


class UserListViewTestCase(TestSessionTokenMixin, TestCase):
    def test_access_denied_to_non_admin_users(self):
        url = reverse("user_management:users")
        self.client.force_login(get_la_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_access_allowed_to_admin_users(self):
        url = reverse("user_management:users")
        self.client.force_login(get_admin_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.OK)


class UserDetailViewTestCase(TestSessionTokenMixin, TestCase):
    def test_access_denied_to_non_admin_users(self):
        user_to_view = get_la_user()
        url = reverse("user_management:user-details", kwargs={"pk": user_to_view.pk})
        self.client.force_login(get_la_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_access_allowed_to_admin_users(self):
        user_to_view = get_la_user()
        url = reverse("user_management:user-details", kwargs={"pk": user_to_view.pk})
        self.client.force_login(get_admin_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.OK)


class UserRemoveGroupViewTestCase(TestSessionTokenMixin, TestCase):
    def test_access_denied_to_non_admin_users(self):
        user_to_view = get_la_user()
        group_to_remove = GroupFactory(name="test_group")
        url = reverse(
            "user_management:user-remove-from-group",
            kwargs={"user_pk": user_to_view.pk, "group_pk": group_to_remove.pk},
        )
        self.client.force_login(get_la_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_access_allowed_to_admin_users(self):
        user_to_view = get_la_user()
        group_to_remove = GroupFactory(name="test_group")
        url = reverse(
            "user_management:user-remove-from-group",
            kwargs={"user_pk": user_to_view.pk, "group_pk": group_to_remove.pk},
        )
        self.client.force_login(get_admin_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.OK)
