import http.client
from unittest.mock import patch

from django.db import DatabaseError
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import HiddenUnassignedAccommodationRequest
from ontology.tests.factories import (
    HiddenUnassignedAccommodationRequestFactory as HiddenUnassignedAccReqFactory,
)
from ontology.tests.factories import MvAccommodationRequestFactory as AccReqFactory
from test_utils.base import BaseTestCase
from user_management.tests.base import (
    get_admin_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_user_with_no_access,
)

LIST_URL_NAME = "unassigned-accommodation-requests:unassigned-accommodation-requests"
HIDE_URL_NAME = "unassigned-accommodation-requests:unhide"


class HideUnassignedAccommodationRequestTests(TestSessionTokenMixin, BaseTestCase):
    def setUp(self):
        super().setUp()
        self.hidden_ar = AccReqFactory(
            title="John Brown and 1 other to 10 Gordon Street",
            ltla_name=None,
            utla_name=None,
        )
        self.unhidden_ar = AccReqFactory(
            title="Jane Brown and 1 other to 11 Gordon Street",
            ltla_name=None,
            utla_name=None,
        )

        self.hidden_unassigned_ar = HiddenUnassignedAccReqFactory(
            accommodation_request=self.hidden_ar
        )

    def test_post_unhides_record(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.assertTrue(
            HiddenUnassignedAccommodationRequest.objects.filter(
                pk=self.hidden_unassigned_ar.pk
            ).exists()
        )

        response = self.client.post(
            reverse(HIDE_URL_NAME, args=[self.hidden_ar.id]),
            follow=True,
        )

        self.assertRedirects(response, reverse(LIST_URL_NAME))
        self.assertFalse(
            HiddenUnassignedAccommodationRequest.objects.filter(
                pk=self.hidden_unassigned_ar.pk
            ).exists()
        )
        self.assertContains(response, "The accommodation request has been unhidden.")
        self.assertContains(response, "Success")

    def test_post_on_already_unhidden_record_shows_error(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(HIDE_URL_NAME, args=[self.unhidden_ar.id]),
            follow=True,
        )

        self.assertRedirects(response, reverse(LIST_URL_NAME))
        self.assertContains(response, "There is a problem")
        self.assertContains(response, "The record is already visible.")

    def test_database_issue_shows_error(self):
        user = get_admin_user()
        self.client.force_login(user)

        with patch(
            "ontology.models.HiddenUnassignedAccommodationRequest.HiddenUnassignedAccommodationRequest.delete",
            side_effect=DatabaseError,
        ):
            response = self.client.post(
                reverse(HIDE_URL_NAME, args=[self.hidden_ar.id]),
                follow=True,
            )

        self.assertRedirects(response, reverse(LIST_URL_NAME))
        self.assertContains(response, "There is a problem")
        self.assertContains(response, "The record has not been unhidden.")

    def test_admin_user_can_access(self):
        self.client.force_login(get_admin_user())

        response = self.client.post(reverse(HIDE_URL_NAME, args=[self.hidden_ar.id]))

        self.assertEqual(response.status_code, http.client.FOUND)

    def test_mhclg_user_can_access(self):
        self.client.force_login(get_mhclg_user())

        response = self.client.post(reverse(HIDE_URL_NAME, args=[self.hidden_ar.id]))

        self.assertEqual(response.status_code, http.client.FOUND)

    def test_service_support_user_cannot_access(self):
        self.client.force_login(get_service_support_user())

        response = self.client.post(reverse(HIDE_URL_NAME, args=[self.hidden_ar.id]))

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_la_user_cannot_access(self):
        self.client.force_login(get_la_user())

        response = self.client.post(reverse(HIDE_URL_NAME, args=[self.hidden_ar.id]))

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_user_with_no_access_cannot_access(self):
        self.client.force_login(get_user_with_no_access())

        response = self.client.post(reverse(HIDE_URL_NAME, args=[self.hidden_ar.id]))

        self.assertEqual(response.status_code, http.client.NOT_FOUND)
