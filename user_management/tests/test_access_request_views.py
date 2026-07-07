import http.client

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from accounts.tests.factories import AccessRequestFactory
from user_management.tests.base import (
    get_admin_user,
    get_la_user,
    get_user_with_no_access,
)


class AccessRequestsListViewTestCase(TestSessionTokenMixin, TestCase):
    def test_access_denied_to_non_admin_users(self):
        url = reverse("user_management:access-requests")
        self.client.force_login(get_la_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_access_allowed_to_admin_users(self):
        url = reverse("user_management:access-requests")
        self.client.force_login(get_admin_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.OK)


class AccessRequestsDetailPageTestCase(TestSessionTokenMixin, TestCase):
    def test_access_denied_to_non_admin_users(self):
        access_request = AccessRequestFactory()
        url = reverse(
            "user_management:access-request-details", kwargs={"pk": access_request.pk}
        )
        self.client.force_login(get_la_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_access_allowed_to_admin_users(self):
        access_request = AccessRequestFactory()
        url = reverse(
            "user_management:access-request-details", kwargs={"pk": access_request.pk}
        )
        self.client.force_login(get_admin_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.OK)


class AccessRequestsFormTestCase(TestSessionTokenMixin, TestCase):
    def test_access_allowed_to_non_admin_users(self):
        url = reverse("user-management:access-request-form")
        self.client.force_login(get_la_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.OK)

    def test_access_allowed_to_user_with_no_groups(self):
        url = reverse("user-management:access-request-form")
        self.client.force_login(get_user_with_no_access())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.OK)

    def test_confirmation_page_access_allowed_to_non_admin_users(self):
        url = reverse("user-management:access-request-confirmation")
        self.client.force_login(get_la_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.OK)


class AccessRequestIntroViewTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("user-management:access-request-intro")

    def test_notification_shows_when_user_has_groups(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(
            response, "You already have access to Homes for Ukraine data"
        )

    def test_no_notification_when_user_has_no_groups(self):
        user = get_user_with_no_access()
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertNotContains(
            response, "You already have access to Homes for Ukraine data"
        )
