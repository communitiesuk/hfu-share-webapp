import http.client

from bs4 import BeautifulSoup
from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import HiddenUnassignedAccommodationRequest
from ontology.tests.factories import MvAccommodationRequestFactory as AccReqFactory
from user_management.tests.base import (
    get_admin_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_user_with_no_access,
)

LIST_URL_NAME = "unassigned-accommodation-requests:unassigned-accommodation-requests"
HIDE_URL_NAME = "unassigned-accommodation-requests:hide"


class HideUnassignedAccommodationRequestTests(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.ar = AccReqFactory(
            title="John Brown and 1 other to 10 Gordon Street",
            ltla_name=None,
            utla_name=None,
        )

    def test_list_renders_hide_link_for_each_row(self):
        self.client.force_login(get_admin_user())

        response = self.client.get(reverse(LIST_URL_NAME))

        soup = BeautifulSoup(response.content.decode("utf-8"), "html.parser")
        table = soup.find("table", class_="govuk-table")
        hide_url = reverse(HIDE_URL_NAME, args=[self.ar.id])
        hide_link = table.find("a", href=hide_url)
        self.assertIsNotNone(hide_link)
        self.assertIn("Hide", hide_link.get_text())

    def test_get_confirm_page_shows_hide_prompt(self):
        self.client.force_login(get_admin_user())

        response = self.client.get(reverse(HIDE_URL_NAME, args=[self.ar.id]))

        self.assertEqual(response.status_code, http.client.OK)
        html = response.content.decode("utf-8")
        self.assertIn("Hide the accommodation request record for", html)
        self.assertIn(self.ar.title, html)
        self.assertIn("Hide this record?", html)
        self.assertIn("Yes, hide", html)

    def test_post_hides_record(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(HIDE_URL_NAME, args=[self.ar.id]),
            follow=True,
        )

        self.assertRedirects(response, reverse(LIST_URL_NAME))
        hidden_ar = HiddenUnassignedAccommodationRequest.objects.get(
            accommodation_request=self.ar
        )
        self.assertEqual(hidden_ar.hidden_by, user)
        self.assertContains(response, "The accommodation request has been hidden.")
        self.assertContains(response, "Success")

    def test_hidden_record_excluded_from_list(self):
        user = get_admin_user()
        self.client.force_login(user)

        HiddenUnassignedAccommodationRequest.objects.create(
            accommodation_request=self.ar, hidden_by=user
        )

        response = self.client.get(reverse(LIST_URL_NAME))

        self.assertNotContains(response, self.ar.title)

    def test_post_on_already_hidden_record_shows_error(self):
        user = get_admin_user()
        self.client.force_login(user)

        HiddenUnassignedAccommodationRequest.objects.create(
            accommodation_request=self.ar, hidden_by=user
        )

        response = self.client.post(
            reverse(HIDE_URL_NAME, args=[self.ar.id]),
            follow=True,
        )

        self.assertRedirects(response, reverse(LIST_URL_NAME))
        self.assertContains(response, "There is a problem")
        self.assertContains(response, "The record has not been hidden.")
        self.assertEqual(
            HiddenUnassignedAccommodationRequest.objects.filter(
                accommodation_request=self.ar
            ).count(),
            1,
        )

    def test_admin_user_can_access(self):
        self.client.force_login(get_admin_user())

        response = self.client.get(reverse(HIDE_URL_NAME, args=[self.ar.id]))

        self.assertEqual(response.status_code, http.client.OK)

    def test_mhclg_user_can_access(self):
        self.client.force_login(get_mhclg_user())

        response = self.client.get(reverse(HIDE_URL_NAME, args=[self.ar.id]))

        self.assertEqual(response.status_code, http.client.OK)

    def test_service_support_user_cannot_access(self):
        self.client.force_login(get_service_support_user())

        response = self.client.get(reverse(HIDE_URL_NAME, args=[self.ar.id]))

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_la_user_cannot_access(self):
        self.client.force_login(get_la_user())

        get_response = self.client.get(reverse(HIDE_URL_NAME, args=[self.ar.id]))
        post_response = self.client.post(reverse(HIDE_URL_NAME, args=[self.ar.id]))

        self.assertEqual(get_response.status_code, http.client.NOT_FOUND)
        self.assertEqual(post_response.status_code, http.client.NOT_FOUND)
        self.assertFalse(
            HiddenUnassignedAccommodationRequest.objects.filter(
                accommodation_request=self.ar
            ).exists()
        )

    def test_user_with_no_access_cannot_access(self):
        self.client.force_login(get_user_with_no_access())

        get_response = self.client.get(reverse(HIDE_URL_NAME, args=[self.ar.id]))
        post_response = self.client.post(reverse(HIDE_URL_NAME, args=[self.ar.id]))

        self.assertEqual(get_response.status_code, http.client.NOT_FOUND)
        self.assertEqual(post_response.status_code, http.client.NOT_FOUND)
        self.assertFalse(
            HiddenUnassignedAccommodationRequest.objects.filter(
                accommodation_request=self.ar
            ).exists()
        )
