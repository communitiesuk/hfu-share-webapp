import http.client
from datetime import datetime, timezone

from django.db.models import QuerySet
from django.test import RequestFactory
from django.urls import reverse
from django.utils.formats import date_format

from accounts.tests.base import TestSessionTokenMixin
from guests.views import GuestVisaApplicationsListView
from ontology.models import VisaApplication
from ontology.tests.base import LocalAuthorityBaseTestCaseMixin
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvPersonFactory,
    VisaApplicationFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class LinkedVisaApplicationsListTestCase(
    TestSessionTokenMixin,
    LocalAuthorityBaseTestCaseMixin,
):
    def assert_query_set_equal_to_list(
        self, qs: QuerySet, visa_applications: list[VisaApplication]
    ):
        return self.assertQuerySetEqual(
            qs.order_by("pk"),
            sorted(visa_applications, key=lambda a: a.pk),
        )

    def setUp(self):
        super().setUp()

        self.visa_application_within_la = VisaApplicationFactory(
            ltla_name=self.ltla_one_a_name,
            application_unique_application_number="111",
            title="Visa application for guest within la",
            visa_status="Pending",
            application_event_datetime=datetime(
                2025, 3, 24, 14, 30, tzinfo=timezone.utc
            ),
            visa_decision_date=datetime(2025, 3, 25, 9, 15, tzinfo=timezone.utc),
            gwf="1234-5678-9012",
            Q97c_sponsor_name="within la sponsor",
        )
        self.visa_application_outside_la = VisaApplicationFactory(
            ltla_name=self.ltla_two_a_name,
            application_unique_application_number="222",
            title="Visa application for guest outside la",
            visa_status="Rejected",
            application_event_datetime=datetime(
                2022, 7, 24, 14, 30, tzinfo=timezone.utc
            ),
            visa_decision_date=datetime(2022, 1, 25, 9, 15, tzinfo=timezone.utc),
            gwf="1234-2222-1111",
            Q97c_sponsor_name="outside la sponsor",
        )
        self.visa_application_not_linked_to_guest = VisaApplicationFactory(
            ltla_name=self.ltla_one_a_name,
            application_unique_application_number="333",
            title="Visa application not linked to guest",
        )

        self.all_visa_applications_linked_to_guest = [
            self.visa_application_within_la,
            self.visa_application_outside_la,
        ]

        self.ar = MvAccommodationRequestFactory(
            title="guest to another accom",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )

        self.guest = MvPersonFactory(
            first_name="Bob",
            last_name="Smith",
            application_number=[
                self.visa_application_within_la.application_unique_application_number,
                self.visa_application_outside_la.application_unique_application_number,
            ],
        )

        self.guest.accommodation_request = self.ar

        self.guest.save()

        self.user = self.ltla_one_a_user
        self.url = reverse(
            "guests:detail-linked-records-visa-applications",
            kwargs={"pk": self.guest.pk},
        )
        self.request = RequestFactory().get(self.url)

    def test_renders_correctly(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url, follow=True)

        self.assertContains(response, "Visa applications")
        self.assertContains(response, "Guest")
        self.assertContains(response, "Visa status")
        self.assertContains(response, "Application date")
        self.assertContains(response, "Decision date")
        self.assertContains(response, "Sponsor")
        self.assertContains(response, "Local authority")
        self.assertContains(response, "Global Web Form number (GWF)")
        self.assertContains(response, "Unique Application Number (UAN)")

    def test_returns_all_visa_applications_linked_to_guest(self):
        self.request.user = self.user
        view = GuestVisaApplicationsListView(kwargs={"pk": self.guest.pk})
        view.request = self.request

        self.assert_query_set_equal_to_list(
            view.get_queryset(), self.all_visa_applications_linked_to_guest
        )

    def test_shows_all_info_for_visa_application_within_users_la(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url, follow=True)

        self.assertContains(response, self.guest.get_full_name())
        self.assertContains(response, self.visa_application_within_la.visa_status)
        self.assertContains(
            response,
            date_format(self.visa_application_within_la.application_event_datetime),
        )
        self.assertContains(
            response,
            date_format(self.visa_application_within_la.visa_decision_date),
        )
        self.assertContains(response, self.visa_application_within_la.Q97c_sponsor_name)
        self.assertContains(response, self.visa_application_within_la.ltla_name)
        self.assertContains(response, self.visa_application_within_la.gwf)
        self.assertContains(
            response,
            self.visa_application_within_la.application_unique_application_number,
        )

    def test_redacts_info_for_visa_application_outside_users_la(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url, follow=True)

        self.assertContains(response, self.guest.get_full_name())
        self.assertContains(response, self.visa_application_outside_la.visa_status)
        self.assertContains(
            response,
            date_format(self.visa_application_outside_la.application_event_datetime),
        )
        self.assertContains(
            response,
            date_format(self.visa_application_outside_la.visa_decision_date),
        )
        self.assertNotContains(
            response, self.visa_application_outside_la.Q97c_sponsor_name
        )
        self.assertContains(response, self.visa_application_outside_la.ltla_name)
        self.assertNotContains(response, self.visa_application_outside_la.gwf)
        self.assertNotContains(
            response,
            self.visa_application_outside_la.application_unique_application_number,
        )

        self.assertContains(response, "Not available")

    def test_user_without_access_to_guest_is_denied_access(self):
        user = self.ltla_two_a_user
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_dev_user_is_granted_access(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_granted_access(self):
        user = self.ltla_one_a_user
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_granted_access(self):
        user = self.da_main_user
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.client.OK)

    def test_mhclg_user_is_granted_access(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.client.OK)

    def test_ukvi_user_is_granted_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.client.OK)

    def test_service_support_user_is_granted_access(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.client.OK)
