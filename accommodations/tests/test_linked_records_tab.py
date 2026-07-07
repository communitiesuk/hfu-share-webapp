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
from user_management.tests.base import get_admin_user, get_da_user, get_la_user


class AccommodationLinkedRecordsTestCase(TestSessionTokenMixin, TestCase):
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

    def test_linked_records_should_display_related_accommodation_requests(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-linked-records",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Accommodation requests")
        self.assertContains(response, self.ar.title)
        self.assertContains(response, self.ar_other_la.title)

    def test_should_display_only_related_accommodation_requests_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-linked-records",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Accommodation requests")
        self.assertContains(response, self.ar.title)
        self.assertNotContains(response, self.ar_other_la.title)

    def test_linked_records_should_display_related_guests(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-linked-records",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Guests")
        self.assertContains(response, self.guest.first_name)
        self.assertContains(response, self.guest_other_la.first_name)

    def test_should_display_only_related_guests_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-linked-records",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Guests")
        self.assertContains(response, self.guest.first_name)
        self.assertNotContains(response, self.guest_other_la.first_name)

    def test_linked_records_should_display_related_hosts(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-linked-records",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Host")
        self.assertContains(response, self.sponsor.first_name)
        self.assertContains(response, self.host.first_name)

    def test_should_display_only_related_hosts_within_users_la(self):
        # Host LA is determined via their accommodations, so for an accommodation
        # the user will always be able to see all linked hosts and sponsors
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-linked-records",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Host")
        self.assertContains(response, self.sponsor.first_name)
        self.assertContains(response, self.host.first_name)

    def test_linked_records_should_display_related_visa_applications(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-linked-records",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Visa applications")
        self.assertContains(response, self.uan.title)
        self.assertContains(response, self.uan_other_la.title)

    def test_should_display_only_related_visa_applications_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-linked-records",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Visa applications")
        self.assertContains(response, self.uan.title)
        self.assertNotContains(response, self.uan_other_la.title)

    def test_la_user_is_allowed_access(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "accommodations:detail-linked-records",
                kwargs={"pk": self.accommodation.id},
            )
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_denied_access_to_other_la_accom(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "accommodations:detail-linked-records",
                kwargs={"pk": self.ar_other_la.id},
            )
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_da_user_is_allowed_access(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "accommodations:detail-linked-records",
                kwargs={"pk": self.da_accommodation.id},
            )
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_denied_access_to_other_da_accom(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "accommodations:detail-linked-records",
                kwargs={"pk": self.accommodation.id},
            )
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)
