import http.client

from django.test import TestCase
from django.urls import reverse

from accounts.models import AccessRequest
from accounts.tests.base import TestSessionTokenMixin
from accounts.tests.factories import AccessRequestFactory
from user_management.tests.base import get_la_user, get_user_with_no_access


class HideAccessRequestsTests(TestSessionTokenMixin, TestCase):
    def test_should_return_404_for_request_not_belonging_to_user(self):
        user = get_la_user()
        other_user = get_user_with_no_access()
        access_request = AccessRequestFactory(requester=other_user)

        self.client.force_login(user)

        response = self.client.post(
            reverse("user_management:hide-access-request", args=[access_request.pk])
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

        access_request.refresh_from_db()
        self.assertEqual(access_request.hidden_by_requester, False)

    def test_should_return_409_for_pending_request_belonging_to_user(self):
        user = get_la_user()
        self.client.force_login(user)
        access_request = AccessRequestFactory(
            requester=user, status=AccessRequest.Status.PENDING
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse("user_management:hide-access-request", args=[access_request.pk])
        )

        self.assertEqual(response.status_code, http.client.CONFLICT)

        access_request.refresh_from_db()
        self.assertEqual(access_request.hidden_by_requester, False)

    def test_should_redirect_and_hide_approved_request_belonging_to_user(self):
        user = get_la_user()
        self.client.force_login(user)
        access_request = AccessRequestFactory(
            requester=user, status=AccessRequest.Status.APPROVED
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse("user_management:hide-access-request", args=[access_request.pk])
        )

        self.assertRedirects(response, reverse("webapp:landing-page"))

        access_request.refresh_from_db()
        self.assertEqual(access_request.hidden_by_requester, True)

    def test_should_redirect_and_hide_rejected_request_belonging_to_user(self):
        user = get_la_user()
        self.client.force_login(user)
        access_request = AccessRequestFactory(
            requester=user, status=AccessRequest.Status.REJECTED
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse("user_management:hide-access-request", args=[access_request.pk])
        )

        self.assertRedirects(response, reverse("webapp:landing-page"))

        access_request.refresh_from_db()
        self.assertEqual(access_request.hidden_by_requester, True)
