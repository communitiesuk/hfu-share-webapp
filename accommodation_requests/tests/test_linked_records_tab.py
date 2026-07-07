from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
    SponsorshipCertificationFormFactory,
    VisaApplicationFactory,
)
from user_management.tests.base import get_admin_user, get_la_user
from webapp.mixins import SummaryListTestCaseMixin


class AccommodationRequestLinkedRecordsTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()
        self.sponsor = MvVolunteerFactory(first_name="LA Sponsor", last_name="Spon")
        self.sponsor_other_la = MvVolunteerFactory(
            first_name="Other LA Sponsor", last_name="Spon"
        )
        self.host = MvVolunteerFactory(first_name="Host", last_name="Host")
        self.host_other_la = MvVolunteerFactory(first_name="Host", last_name="Host")
        self.guest = MvPersonFactory(first_name="LA Guest", last_name="Guest")
        self.guest_other_la = MvPersonFactory(
            first_name="Other LA Guest", last_name="Guest"
        )
        self.accommodation = MvAccommodationFactory(
            ltla_name="ltla_somerset", full_address="Somerset accommodation"
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
        self.uam = SponsorshipCertificationFormFactory(
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            reference="UAM-111-222",
            given_name="John",
            family_name="Doe",
            cohabitant_id=["UAM-111-222"],
        )
        self.uam_other_la = SponsorshipCertificationFormFactory(
            ltla_name=["Other LTLA"],
            utla_name=["Other UTLA"],
            reference="UAM-123-123",
            given_name="Jane",
            family_name="Doe",
        )
        self.ar = MvAccommodationRequestFactory(
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            accommodation_id=[self.accommodation.id, self.accommodation_other_la.id],
            person_id=[self.guest.id, self.guest_other_la.id],
            number_of_people=1,
            primary_sponsor=self.sponsor,
            sponsor_id=[self.sponsor.id, self.sponsor_other_la.id],
            active_host=self.host,
            unique_application_number=[
                self.uan.application_unique_application_number,
                self.uan_other_la.application_unique_application_number,
            ],
            sponsorship_certification_number_id=[
                self.uam.pk,
                self.uam_other_la.pk,
            ],
        )
        self.ar_with_active_host_and_primary_sponsor = MvAccommodationRequestFactory(
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            accommodation_id=[self.accommodation.id, self.accommodation_other_la.id],
            person_id=[self.guest.id, self.guest_other_la.id],
            number_of_people=1,
            primary_sponsor=self.sponsor,
            sponsor_id=[self.sponsor.id, self.sponsor_other_la.id],
            active_host=self.host,
            unique_application_number=[
                self.uan.application_unique_application_number,
                self.uan_other_la.application_unique_application_number,
            ],
        )
        self.ar_with_primary_sponsor_with_no_active_host = (
            MvAccommodationRequestFactory(
                ltla_name=["ltla_somerset"],
                utla_name=["utla_somerset"],
                accommodation_id=[
                    self.accommodation.id,
                    self.accommodation_other_la.id,
                ],
                person_id=[self.guest.id, self.guest_other_la.id],
                number_of_people=1,
                primary_sponsor=self.sponsor,
                sponsor_id=[self.sponsor.id, self.sponsor_other_la.id],
                unique_application_number=[
                    self.uan.application_unique_application_number,
                    self.uan_other_la.application_unique_application_number,
                ],
            )
        )

        self.guest.accommodation_request = self.ar
        self.guest.save()

        self.guest_other_la.accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["Other LTLA"], utla_name=["Other UTLA"]
        )
        self.guest_other_la.save()

    def test_linked_records_should_display_related_accommodations(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(
            response, "Accommodation", self.accommodation.full_address
        )
        self.assertSummaryListContainsRow(
            response, "Accommodation", self.accommodation_other_la.full_address
        )

    def test_should_display_only_related_accommodations_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(
            response, "Accommodation", self.accommodation.full_address
        )
        self.assertSummaryListNotContainsRow(
            response, "Accommodation", self.accommodation_other_la.full_address
        )

    def test_linked_records_should_display_related_guests(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(response, "Guests", self.guest.first_name)
        self.assertSummaryListContainsRow(
            response, "Guests", self.guest_other_la.first_name
        )

    def test_should_display_only_related_guests_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(response, "Guests", self.guest.first_name)
        self.assertSummaryListNotContainsRow(
            response, "Guests", self.guest_other_la.first_name
        )

    def test_linked_records_should_display_related_primary_sponsor_if_no_active_host(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar_with_primary_sponsor_with_no_active_host.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(
            response,
            "Host",
            self.ar_with_primary_sponsor_with_no_active_host.primary_sponsor.full_name,
        )
        self.assertNotContains(response, "Primary sponsor")

    def test_should_display_only_related_primary_sponsor_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar_with_primary_sponsor_with_no_active_host.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(response, "Host", self.sponsor.full_name)

        self.ar_with_primary_sponsor_with_no_active_host.primary_sponsor = (
            self.sponsor_other_la
        )
        self.ar_with_primary_sponsor_with_no_active_host.save()

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar_with_primary_sponsor_with_no_active_host.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertNotContains(response, "Host")
        self.assertNotContains(response, self.sponsor_other_la.full_name)

    def test_linked_records_should_display_related_sponsors(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(response, "Sponsors", self.sponsor.full_name)
        self.assertSummaryListContainsRow(
            response, "Sponsors", self.sponsor_other_la.first_name
        )

    def test_should_display_only_related_sponsors_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(response, "Sponsors", self.sponsor.full_name)
        self.assertSummaryListNotContainsRow(
            response, "Sponsors", self.sponsor_other_la.first_name
        )

    def test_linked_records_displays_withdrawn_tag_next_to_withdrawn_sponsor(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.ar.sponsor_withdrawn = [self.sponsor.id]
        self.ar.save()

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRowWithStatusTag(
            response, "Sponsors", self.sponsor.full_name, "Withdrawn"
        )

    def test_linked_records_should_display_related_active_host_if_present(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar_with_active_host_and_primary_sponsor.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(
            response,
            "Host",
            self.ar_with_active_host_and_primary_sponsor.active_host.full_name,
        )

    def test_should_display_only_related_active_host_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(response, "Host", self.host.full_name)

        self.ar.active_host = self.host_other_la
        self.ar.save()

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertNotContains(response, "Host")
        self.assertNotContains(response, self.host_other_la.full_name)

    def test_linked_records_does_not_display_withdrawn_tag_next_to_active_host(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Set the active host as a withdrawn sponsor. Individuals can withdraw
        # from being a sponsor, but they remain the active host. They cannot
        # withdraw from being a host until a rematch/reassignment occurs
        self.ar.sponsor_withdrawn = [self.sponsor.id]
        self.ar.active_host = self.sponsor
        self.ar.save()

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(response, "Host", self.sponsor.full_name)
        self.assertSummaryListNotContainsRowWithStatusTag(
            response, "Host", self.sponsor.full_name, "Withdrawn"
        )

    def test_linked_records_should_display_related_visa_applications(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(response, "Visa applications", self.uan.title)
        self.assertSummaryListContainsRow(
            response, "Visa applications", self.uan_other_la.title
        )

    def test_should_display_only_related_visa_applications_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(response, "Visa applications", self.uan.title)
        self.assertSummaryListNotContainsRow(
            response, "Visa applications", self.uan_other_la.title
        )

    def test_linked_records_should_display_related_uams(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(
            response, "Sponsorship certification number", self.uam.pk
        )
        self.assertSummaryListContainsRow(
            response, "Sponsorship certification number", self.uam_other_la.pk
        )

    def test_should_display_only_related_uams_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-linked-records",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(
            response, "Sponsorship certification number", self.uam.pk
        )
        self.assertSummaryListNotContainsRow(
            response, "Sponsorship certification number", self.uam_other_la.pk
        )
