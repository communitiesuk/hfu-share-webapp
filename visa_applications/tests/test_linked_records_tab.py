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
from user_management.tests.base import get_admin_user, get_la_user
from webapp.mixins import SummaryListTestCaseMixin


class VisaApplicationsLinkedRecordsTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()
        self.uan = VisaApplicationFactory(
            ltla_name="ltla_somerset",
            application_unique_application_number="123456",
            title="Visa Application for Guest",
        )
        self.sponsor = MvVolunteerFactory(
            first_name="LA Sponsor",
            last_name="Spon",
            application_unique_application_number=[
                self.uan.application_unique_application_number
            ],
        )
        self.sponsor_other_la = MvVolunteerFactory(
            first_name="Other LA Sponsor",
            last_name="Spon",
            application_unique_application_number=[
                self.uan.application_unique_application_number
            ],
        )
        self.host = MvVolunteerFactory(
            first_name="LA Host",
            last_name="Host",
            application_unique_application_number=[
                self.uan.application_unique_application_number
            ],
        )
        self.host_other_la = MvVolunteerFactory(
            first_name="Other LA Host",
            last_name="Host",
            application_unique_application_number=[
                self.uan.application_unique_application_number
            ],
        )
        self.accommodation = MvAccommodationFactory(
            ltla_name="ltla_somerset",
            full_address="Somerset accommodation",
            application_unique_application_number=[
                self.uan.application_unique_application_number
            ],
        )
        self.accommodation.hosts.set([self.sponsor.id, self.host.id])
        self.accommodation_other_la = MvAccommodationFactory(
            ltla_name="Other LTLA",
            utla_name="Other UTLA",
            full_address="Other accommodation",
            application_unique_application_number=[
                self.uan.application_unique_application_number
            ],
        )
        self.accommodation_other_la.hosts.set(
            [self.sponsor_other_la.id, self.host_other_la.id]
        )
        self.guest = MvPersonFactory(
            first_name="Guest",
            last_name="Person",
            application_number=[
                self.uan.application_unique_application_number,
            ],
        )
        self.guest_other_la = MvPersonFactory(
            first_name="Other LA Guest",
            last_name="Guest",
            application_number=[
                self.uan.application_unique_application_number,
            ],
        )
        self.ar = MvAccommodationRequestFactory(
            title="Guest Person to Somerset accom",
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            primary_accommodation=self.accommodation,
            person_id=[self.guest.id],
            number_of_people=1,
            primary_sponsor=self.sponsor,
            sponsor_id=[self.sponsor.id],
            active_host=self.host,
            unique_application_number=[self.uan.application_unique_application_number],
        )
        self.ar_other_la = MvAccommodationRequestFactory(
            title="Other LA Guest Guest to Somerset accom",
            ltla_name=["Other LTLA"],
            utla_name=["Other UTLA"],
            primary_accommodation=self.accommodation,
            sponsor_id=[self.sponsor_other_la.id],
            active_host=self.host_other_la,
            unique_application_number=[self.uan.application_unique_application_number],
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
                "visa-applications:detail-linked-records",
                args=[self.uan.pk],
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
                "visa-applications:detail-linked-records",
                args=[self.uan.pk],
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
                "visa-applications:detail-linked-records",
                args=[self.uan.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Guest")
        self.assertContains(response, self.guest.first_name)
        self.assertContains(response, self.guest_other_la.first_name)

    def test_should_display_only_related_guests_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:detail-linked-records",
                args=[self.uan.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Guest")
        self.assertContains(response, self.guest.first_name)
        self.assertNotContains(response, self.guest_other_la.first_name)

    def test_linked_records_should_display_related_sponsors(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:detail-linked-records",
                args=[self.uan.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Sponsor")
        self.assertContains(response, self.sponsor.full_name)
        self.assertContains(response, self.host.first_name)
        self.assertContains(response, self.sponsor_other_la.first_name)
        self.assertContains(response, self.host_other_la.first_name)

    def test_should_display_only_related_sponsors_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:detail-linked-records",
                args=[self.uan.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Sponsor")
        self.assertContains(response, self.sponsor.full_name)
        self.assertContains(response, self.host.first_name)
        self.assertNotContains(response, self.sponsor_other_la.first_name)
        self.assertNotContains(response, self.host_other_la.first_name)

    def test_linked_records_should_display_related_active_host(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:detail-linked-records",
                args=[self.uan.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Host")
        self.assertContains(response, self.host.full_name)
        self.assertContains(response, self.host_other_la.first_name)

    def test_should_display_only_related_active_host_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:detail-linked-records",
                args=[self.uan.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Host")
        self.assertContains(response, self.host.full_name)
        self.assertNotContains(response, self.host_other_la.first_name)

    def test_should_display_primary_sponsor_as_active_host_if_none(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.ar.active_host = None
        self.ar.save()

        response = self.client.get(
            reverse(
                "visa-applications:detail-linked-records",
                args=[self.uan.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(response, "Host", self.sponsor.full_name)

    def test_linked_records_should_display_related_accommodations(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:detail-linked-records",
                args=[self.uan.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Accommodation")
        self.assertContains(response, self.accommodation.full_address)
        self.assertContains(response, self.accommodation_other_la.full_address)

    def test_should_display_only_related_accommodations_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:detail-linked-records",
                args=[self.uan.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Accommodation")
        self.assertContains(response, self.accommodation.full_address)
        self.assertNotContains(response, self.accommodation_other_la.full_address)
