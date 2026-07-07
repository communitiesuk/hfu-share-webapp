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
from webapp.mixins import SummaryListTestCaseMixin


class GuestLinkedRecordsTestCase(
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

    def test_linked_records_should_display_related_visa_applications(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-linked-records",
                args=[self.guest.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Visa applications")
        self.assertContains(response, self.uan.title)
        self.assertContains(response, self.uan_other_la.title)

    def test_linked_records_should_display_link_to_see_all_linked_visa_applications(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-linked-records",
                args=[self.guest.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Visa applications")
        self.assertContains(
            response, "View the list of all visa applications for this guest"
        )

    def test_should_display_only_related_visa_applications_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-linked-records",
                args=[self.guest.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Visa applications")
        self.assertContains(response, self.uan.title)
        self.assertNotContains(response, self.uan_other_la.title)

    def test_linked_records_should_display_related_accommodation_requests(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-linked-records",
                args=[self.guest.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Accommodation requests")
        self.assertContains(response, self.ar.title)

    def test_should_display_only_related_accommodation_requests_within_users_la(self):
        # Guest LA is determined via related AR, so if a user can see a guest they
        # should also always be able to see the related AR
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-linked-records",
                args=[self.guest.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Accommodation requests")
        self.assertContains(response, self.ar.title)

    def test_linked_records_should_display_related_primary_sponsor_if_no_active_host(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        self.ar.active_host = None
        self.ar.save()

        response = self.client.get(
            reverse(
                "guests:detail-linked-records",
                args=[self.guest.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(response, "Host", self.sponsor.full_name)
        self.assertNotContains(response, "Primary sponsor")

    def test_should_display_only_related_primary_sponsor_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        self.ar.active_host = None
        self.ar.save()

        response = self.client.get(
            reverse(
                "guests:detail-linked-records",
                args=[self.guest.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(response, "Host", self.sponsor.full_name)

        self.ar.primary_sponsor = self.sponsor_other_la
        self.ar.save()

        response = self.client.get(
            reverse(
                "guests:detail-linked-records",
                args=[self.guest.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertNotContains(response, "Host")
        self.assertNotContains(response, "Primary sponsor")
        self.assertNotContains(response, self.sponsor_other_la.full_name)

    def test_linked_records_should_display_related_sponsors(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-linked-records",
                args=[self.guest.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Sponsors")
        self.assertContains(response, self.sponsor.full_name)
        self.assertContains(response, self.sponsor_other_la.first_name)

    def test_should_display_only_related_sponsors_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-linked-records",
                args=[self.guest.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Sponsors")
        self.assertContains(response, self.sponsor.full_name)
        self.assertNotContains(response, self.sponsor_other_la.first_name)

    def test_linked_records_should_display_related_active_host_if_present(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-linked-records",
                args=[self.guest.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(response, "Host", self.host.full_name)

    def test_should_display_only_related_active_host_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-linked-records",
                args=[self.guest.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Host")
        self.assertContains(response, self.host.full_name)

        self.ar.active_host = self.host_other_la
        self.ar.save()

        response = self.client.get(
            reverse(
                "guests:detail-linked-records",
                args=[self.guest.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertNotContains(response, "Host")
        self.assertNotContains(response, self.host_other_la.full_name)

    def test_linked_records_should_display_related_accommodations(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-linked-records",
                args=[self.guest.pk],
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
                "guests:detail-linked-records",
                args=[self.guest.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Accommodation")
        self.assertContains(response, self.accommodation.full_address)
        self.assertNotContains(response, self.accommodation_other_la.full_address)

    def test_get_accommodation_request_with_broken_ar_id_wont_500(self):
        guest = MvPersonFactory(
            accommodation_request=None,
            accommodation_request_id="nonexistent_id",
        )

        dev_user = get_admin_user()
        self.client.force_login(dev_user)

        response = self.client.get(
            reverse(
                "guests:detail-linked-records",
                args=[guest.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_la_user_is_allowed_access(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("guests:detail-linked-records", args=[self.guest.pk])
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_denied_access_to_other_la_guest(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("guests:detail-linked-records", args=[self.da_guest.pk])
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_da_user_is_allowed_access(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("guests:detail-linked-records", args=[self.da_guest.pk])
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_denied_access_to_other_da_guest(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("guests:detail-linked-records", args=[self.guest.pk])
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)
