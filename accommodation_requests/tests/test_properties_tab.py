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


class AccommodationRequestPropertiesTestCase(
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

    def test_properties_should_render_for_admin(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-properties",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Properties")
        self.assertContains(response, "Accommodation request record for")
        self.assertContains(response, self.ar.id)
        self.assertContains(response, self.ar.ltla_name[0])
        self.assertContains(response, self.ar.utla_name[0])
        self.assertContains(response, self.guest.id)
        self.assertContains(response, self.guest_other_la.id)

    def test_properties_should_render_for_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-properties",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Properties")
        self.assertContains(response, "Accommodation request record for")
        self.assertContains(response, self.ar.id)
        self.assertContains(response, self.ar.ltla_name[0])
        self.assertContains(response, self.ar.utla_name[0])
        self.assertContains(response, self.guest.id)
