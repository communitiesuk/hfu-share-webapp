import http.client

from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
    SafeguardingReferralFactory,
    VisaApplicationFactory,
)
from safeguarding.views import SafeguardingDetailOverviewView
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_ukvi_user,
)
from webapp.mixins import SummaryListTestCaseMixin


class SafeguardingOverviewViewTestCase(
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
        )
        self.guest_other = MvPersonFactory(
            first_name="Other Guest",
            last_name="Guest",
        )
        self.ar = MvAccommodationRequestFactory(
            title="Guest Person to Somerset accom",
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            primary_accommodation=self.accommodation,
            person_id=[self.guest.id, self.guest_other.id],
            number_of_people=2,
            primary_sponsor=self.sponsor,
            sponsor_id=[self.sponsor.id, self.sponsor_other_la.id],
            active_host=self.host,
            unique_application_number=[
                self.uan.application_unique_application_number,
                self.uan_other_la.application_unique_application_number,
            ],
        )
        self.referral = SafeguardingReferralFactory(person=self.guest)

        self.guest.accommodation_request = self.ar
        self.guest.save()

        self.guest_other.accommodation_request = self.ar
        self.guest_other.save()

    def test_ukvi_user_can_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "safeguarding:detail-linked-records",
                args=[self.guest.pk, self.referral.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_denied_access(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "safeguarding:detail-overview",
                args=[self.guest.pk, self.referral.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_da_user_is_denied_access(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "safeguarding:detail-overview",
                args=[self.guest.pk, self.referral.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_shows_active_host_if_present(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "safeguarding:detail-overview", args=[self.guest.pk, self.referral.pk]
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(response, "Host", self.host.full_name)

    def test_shows_primary_sponsor_as_active_host_none_present(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.ar.active_host = None
        self.ar.save()

        response = self.client.get(
            reverse(
                "safeguarding:detail-overview", args=[self.guest.pk, self.referral.pk]
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(
            response, "Host", self.ar.primary_sponsor.full_name
        )

    def test_safeguarding_detail_overview_displays_correct_details(self):
        request = RequestFactory().get("/")
        request.user = get_admin_user()

        view = SafeguardingDetailOverviewView(kwargs={"referral_id": self.referral.id})
        view.request = request
        view.object = self.guest

        context = view.get_context_data()
        fields = dict(context["fields"])

        self.assertIn("Host", fields)
        self.assertIn(self.host.get_full_name(), fields["Host"])

        self.assertIn("Sponsor", fields)
        self.assertIn(self.sponsor.get_full_name(), fields["Sponsor"])

        self.assertIn("Lower tier local authority", fields)
        self.assertIn(self.ar.ltla_name[0], fields["Lower tier local authority"])

        self.assertIn("Upper tier local authority", fields)
        self.assertIn(self.ar.utla_name[0], fields["Upper tier local authority"])
