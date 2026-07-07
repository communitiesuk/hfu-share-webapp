import http.client

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from accounts.tests.factories import GroupFactory
from user_management.tests.base import get_admin_user, get_la_user


class GroupListViewTestCase(TestSessionTokenMixin, TestCase):
    def test_access_denied_to_non_admin_users(self):
        url = reverse("user_management:groups")
        self.client.force_login(get_la_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_access_allowed_to_admin_users(self):
        url = reverse("user_management:groups")
        self.client.force_login(get_admin_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.OK)


class GroupDetailViewTestCase(TestSessionTokenMixin, TestCase):
    def test_access_denied_to_non_admin_users(self):
        group_to_view = GroupFactory(name="test_group")
        url = reverse("user_management:group-details", kwargs={"pk": group_to_view.pk})
        self.client.force_login(get_la_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_access_allowed_to_admin_users(self):
        group_to_view = GroupFactory(name="test_group")
        url = reverse("user_management:group-details", kwargs={"pk": group_to_view.pk})
        self.client.force_login(get_admin_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.OK)


class GroupRemoveUserViewTestCase(TestSessionTokenMixin, TestCase):
    def test_access_denied_to_non_admin_users(self):
        group_to_view = GroupFactory(name="test_group")
        user_to_remove = get_la_user()
        url = reverse(
            "user_management:group-remove-user",
            kwargs={"user_pk": user_to_remove.pk, "group_pk": group_to_view.pk},
        )
        self.client.force_login(get_la_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_access_allowed_to_admin_users(self):
        group_to_view = GroupFactory(name="test_group")
        user_to_remove = get_la_user()
        url = reverse(
            "user_management:group-remove-user",
            kwargs={"user_pk": user_to_remove.pk, "group_pk": group_to_view.pk},
        )
        self.client.force_login(get_admin_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.OK)
