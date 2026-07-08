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
from webapp.mixins import SummaryListTestCaseMixin


class GuestPropertiesTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()
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
        self.sponsor = MvVolunteerFactory(first_name="LA Sponsor", last_name="Spon")
        self.sponsor_other_la = MvVolunteerFactory(
            first_name="Other LA Sponsor", last_name="Spon"
        )
        self.host = MvVolunteerFactory(first_name="Host", last_name="Host")
        self.host_other_la = MvVolunteerFactory(first_name="Host", last_name="Host")
        self.accommodation = MvAccommodationFactory(
            ltla_name="ltla_somerset",
            full_address="Somerset accommodation",
        )
        self.accommodation.hosts.set([self.sponsor.id, self.host.id])
        self.accommodation_other_la = MvAccommodationFactory(
            ltla_name="Other LTLA",
            utla_name="Other UTLA",
            full_address="Other accommodation",
        )
        self.accommodation_other_la.hosts.set(
            [self.sponsor_other_la.id, self.host_other_la.id]
        )
        self.guest = MvPersonFactory(
            first_name="Guest",
            last_name="Person",
            application_number=[
                self.uan.application_unique_application_number,
                self.uan_other_la.application_unique_application_number,
            ],
        )
        self.ar = MvAccommodationRequestFactory(
            title="Guest Person to Somerset accom",
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            primary_accommodation=self.accommodation,
            accommodation_id=[self.accommodation.id, self.accommodation_other_la.id],
            person_id=[self.guest.id],
            number_of_people=1,
            primary_sponsor=self.sponsor,
            sponsor_id=[self.sponsor.id, self.sponsor_other_la.id],
            active_host=self.host,
        )
        self.guest.accommodation_request = self.ar
        self.guest.save()

        self.da_guest = MvPersonFactory(
            first_name="DA",
            last_name="Guest",
        )
        self.da_ar = MvAccommodationRequestFactory(
            title="Guest Person to Aberdeenshire",
            ltla_name=["Aberdeenshire"],
            utla_name=["Aberdeenshire"],
            primary_accommodation=self.accommodation,
            accommodation_id=[self.accommodation.id, self.accommodation_other_la.id],
            person_id=[self.guest.id],
            number_of_people=1,
            primary_sponsor=self.sponsor,
            sponsor_id=[self.sponsor.id, self.sponsor_other_la.id],
            active_host=self.host,
        )
        self.da_guest.accommodation_request = self.da_ar
        self.da_guest.save()

    def test_la_user_is_allowed_access(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("guests:detail-properties", args=[self.guest.pk])
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_denied_access_to_other_la_guest(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("guests:detail-properties", args=[self.da_guest.pk])
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_da_user_is_allowed_access(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("guests:detail-properties", args=[self.da_guest.pk])
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_denied_access_to_other_da_guest(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("guests:detail-properties", args=[self.guest.pk])
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_excluded_fields_are_not_shown(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("guests:detail-properties", args=[self.guest.pk])
        )
        self.assertNotContains(response, "Archived at")
        self.assertNotContains(response, "Is archived")
