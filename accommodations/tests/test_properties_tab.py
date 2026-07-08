import http.client

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
    VisaApplicationFactory,
)
from user_management.tests.base import get_da_user, get_la_user


class AccommodationPropertiesTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sponsor = MvVolunteerFactory(first_name="LA Sponsor", last_name="Spon")
        self.host = MvVolunteerFactory(first_name="LA Host", last_name="Host")
        self.guest = MvPersonFactory(first_name="LA Guest", last_name="Guest")
        self.guest_other_la = MvPersonFactory(
            first_name="Other LA Guest", last_name="Guest"
        )
        self.uan = VisaApplicationFactory(
            ltla_name="ltla_somerset",
            application_unique_application_number="123456",
            title="Visa Application for Guest",
        )
        self.uan_other_la = VisaApplicationFactory(
            ltla_name="Other LTLA",
            utla_name="Other UTLA",
            application_unique_application_number="789101",
            title="Other LA Visa Application",
        )
        self.accommodation = MvAccommodationFactory(
            ltla_name="ltla_somerset",
            full_address="Somerset accommodation",
            application_unique_application_number=[
                self.uan.application_unique_application_number,
                self.uan_other_la.application_unique_application_number,
            ],
        )
        self.accommodation.hosts.set([self.sponsor.id, self.host.id])
        self.ar = MvAccommodationRequestFactory(
            title="LA Guest Guest to Somerset accom",
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            primary_accommodation=self.accommodation,
            accommodation_id=[self.accommodation.id],
        )
        self.ar_other_la = MvAccommodationRequestFactory(
            title="Other LA Guest Guest to Somerset accom",
            ltla_name=["Other LTLA"],
            utla_name=["Other UTLA"],
            primary_accommodation=self.accommodation,
            accommodation_id=[self.accommodation.id],
        )
        self.da_accommodation = MvAccommodationFactory(
            full_address="Scotland DA address",
            ltla_name="Aberdeenshire",
            utla_name="Aberdeenshire",
        )

        self.guest.accommodation_request = self.ar
        self.guest.save()

        self.guest_other_la.accommodation_request = self.ar_other_la
        self.guest_other_la.save()

    def test_la_user_is_allowed_access(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "accommodations:detail-properties", kwargs={"pk": self.accommodation.id}
            )
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_denied_access_to_other_la_accom(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "accommodations:detail-properties",
                kwargs={"pk": self.ar_other_la.id},
            )
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_da_user_is_allowed_access(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "accommodations:detail-properties",
                kwargs={"pk": self.da_accommodation.id},
            )
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_denied_access_to_other_da_accom(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "accommodations:detail-properties", kwargs={"pk": self.accommodation.id}
            )
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_excluded_fields_are_not_shown(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "accommodations:detail-properties", kwargs={"pk": self.accommodation.id}
            )
        )
        self.assertNotContains(response, "Archived at")
        self.assertNotContains(response, "Is archived")
