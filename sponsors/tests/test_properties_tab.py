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
from user_management.tests.base import get_admin_user, get_da_user
from webapp.mixins import SummaryListTestCaseMixin


class SponsorsPropertiesTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()
        self.uan = VisaApplicationFactory(
            ltla_name="ltla_somerset",
            application_unique_application_number="123456",
            title="Visa Application for Guest",
        )
        self.scottish_uan = VisaApplicationFactory(
            ltla_name="City of Edinburgh",
            application_unique_application_number="987654",
            title="Scottish Visa Application",
        )
        self.uan_other_la = VisaApplicationFactory(
            ltla_name="Other LTLA",
            utla_name="Other UTLA",
            application_unique_application_number="789101",
            title="Other LA Visa Application",
        )
        self.sponsor = MvVolunteerFactory(
            first_name="LA Sponsor",
            last_name="Spon",
            application_unique_application_number=[
                self.uan.application_unique_application_number,
                self.uan_other_la.application_unique_application_number,
            ],
        )

        self.scottish_sponsor = MvVolunteerFactory(
            first_name="Scottish Sponsor",
            last_name="Spon",
            application_unique_application_number=[
                self.scottish_uan.application_unique_application_number,
            ],
        )
        self.accommodation = MvAccommodationFactory(
            ltla_name="ltla_somerset",
            full_address="Somerset accommodation",
        )
        self.scottish_accommodation = MvAccommodationFactory(
            ltla_name="City of Edinburgh",
            full_address="Edinburgh accommodation",
        )
        self.scottish_accommodation.hosts.set([self.scottish_sponsor.id])
        self.accommodation.hosts.set([self.sponsor.id])
        self.accommodation_other_la = MvAccommodationFactory(
            ltla_name="Other LTLA",
            utla_name="Other UTLA",
            full_address="Other accommodation",
        )
        self.accommodation_other_la.hosts.set([self.sponsor.id])
        self.accommodation_on_ar_not_belonging_to_sponsor = MvAccommodationFactory(
            full_address="AR accommodation",
        )
        self.guest = MvPersonFactory(
            first_name="Guest",
            last_name="Person",
        )
        self.guest_other_la = MvPersonFactory(
            first_name="Other LA Guest",
            last_name="Person",
        )
        self.ar = MvAccommodationRequestFactory(
            title="Guest Person to Somerset accom",
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            primary_accommodation=self.accommodation,
            accommodation_id=[
                self.accommodation.id,
                self.accommodation_on_ar_not_belonging_to_sponsor.id,
            ],
            person_id=[self.guest.id],
            number_of_people=1,
            primary_sponsor=self.sponsor,
            sponsor_id=[self.sponsor.id],
            active_host=self.sponsor,
        )

        self.ar_other_la = MvAccommodationRequestFactory(
            title="Other LA Guest Person to Other accommod",
            ltla_name=["Other LA"],
            utla_name=["Other LA"],
            primary_accommodation=self.accommodation_other_la,
            accommodation_id=[self.accommodation_other_la.id],
            person_id=[self.guest_other_la.id],
            number_of_people=1,
            primary_sponsor=self.sponsor,
            sponsor_id=[self.sponsor.id],
            active_host=self.sponsor,
        )

        self.scottish_ar = MvAccommodationRequestFactory(
            title="Guest Person to Scottish accom",
            ltla_name=["City of Edinburgh"],
            primary_accommodation=self.scottish_accommodation,
            accommodation_id=[
                self.scottish_accommodation.id,
            ],
            person_id=[self.guest.id],
            number_of_people=1,
            primary_sponsor=self.scottish_sponsor,
            sponsor_id=[self.scottish_sponsor.id],
            active_host=self.scottish_sponsor,
        )
        self.active_host_ar = MvAccommodationRequestFactory(
            title="AR with sponsor as active host only",
            primary_sponsor=None,
            sponsor_id=[],
            active_host=self.sponsor,
        )
        self.primary_sponsor_ar = MvAccommodationRequestFactory(
            title="AR with sponsor as active host only",
            primary_sponsor=self.sponsor,
            sponsor_id=[],
            active_host=None,
        )
        self.sponsor_ar = MvAccommodationRequestFactory(
            title="AR with sponsor as active host only",
            primary_sponsor=None,
            sponsor_id=[self.sponsor.id],
            active_host=None,
        )

        self.guest.accommodation_request = self.ar
        self.guest.save()

        self.guest_other_la.accommodation_request = self.ar_other_la
        self.guest.save()

    def test_properties_should_render_for_admin_user(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-properties",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Properties")
        self.assertContains(response, self.sponsor.id)
        self.assertContains(response, self.sponsor.first_name)
        self.assertContains(response, self.sponsor.last_name)

    def test_properties_should_render_for_da_user(
        self,
    ):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-properties",
                args=[self.scottish_sponsor.pk],
            )
        )

        self.assertContains(response, "Properties")
        self.assertContains(response, self.scottish_sponsor.id)
        self.assertContains(response, self.scottish_sponsor.first_name)
        self.assertContains(response, self.scottish_sponsor.last_name)

    def test_excluded_fields_are_not_shown(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-properties",
                args=[self.sponsor.pk],
            )
        )

        self.assertNotContains(response, "Archived at")
        self.assertNotContains(response, "Is archived")
        self.assertNotContains(response, "Viewer group names")
