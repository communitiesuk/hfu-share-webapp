import http.client

from django.urls import reverse

from accommodation_requests.tests.base import AccommodationRequestsBaseTestCase
from accounts.tests.base import TestSessionTokenMixin
from ontology.models import MvAccommodationRequest
from ontology.tests.factories import MvAccommodationRequestFactory as AccReqFactory
from user_management.tests.base import get_admin_user, get_la_user


class AccommodationRequestDetailOverviewTestCase(
    TestSessionTokenMixin, AccommodationRequestsBaseTestCase
):
    def test_ar_detail_overview_with_no_withdrawn_sponsors_works(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-overview",
                args=[self.null_withdrawn_sponsors_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_ar_detail_overview_with_no_person_id_works(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-overview",
                args=[self.no_guests_acc_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_ar_detail_overview_displays_correct_details(self):
        ar = AccReqFactory(
            title="Test Access Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            active_host=self.sponsor_1,
            sponsor_id=[self.sponsor_2.id, self.sponsor_3.id],
            ltla_name=["LTLA name"],
            utla_name=["UTLA name"],
            person_id=[self.guest.id],
            accommodation_id=[self.accommodation_one.id],
        )

        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-overview",
                args=[ar.id],
            )
        )
        context = response.context
        fields = dict(context["fields"])

        self.assertIn("Status", fields)
        self.assertIn(
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED, fields["Status"]
        )

        self.assertIn("Host", fields)
        self.assertIn(self.sponsor_1.get_full_name(), fields["Host"])

        self.assertIn("Sponsors", fields)
        self.assertIn(self.sponsor_2.get_full_name(), fields["Sponsors"])
        self.assertIn(self.sponsor_3.get_full_name(), fields["Sponsors"])

        self.assertIn("Lower tier Local Authority", fields)
        self.assertIn("LTLA name", fields["Lower tier Local Authority"])

        self.assertIn("Upper tier Local Authority", fields)
        self.assertIn("UTLA name", fields["Upper tier Local Authority"])

        self.assertIn("Guests", fields)
        self.assertIn(self.guest.get_full_name(), fields["Guests"])

        self.assertIn("Address", fields)
        self.assertIn(self.accommodation_one.full_address, fields["Address"])

    def test_ar_detail_overview_displays_correct_multi_la_details(self):
        ar = AccReqFactory(
            title="Test Access Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            active_host=self.sponsor_1,
            sponsor_id=[self.sponsor_2.id, self.sponsor_3.id],
            ltla_name=["Bridgend", "Kent"],
            utla_name=["Bridgend", "Kent"],
            person_id=[self.guest.id],
            accommodation_id=[self.accommodation_one.id],
        )
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-overview",
                args=[ar.id],
            )
        )
        context = response.context
        fields = dict(context["fields"])

        self.assertIn("Lower tier Local Authority", fields)
        self.assertIn("Bridgend", fields["Lower tier Local Authority"])
        self.assertIn("Kent", fields["Lower tier Local Authority"])

        self.assertIn("Upper tier Local Authority", fields)
        self.assertIn("Bridgend", fields["Upper tier Local Authority"])
        self.assertIn("Kent", fields["Upper tier Local Authority"])

    def test_ar_detail_overview_hides_details_outside_of_users_la(self):
        ar = AccReqFactory(
            title="Test Access Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            active_host=self.sponsor_1,
            sponsor_id=[self.sponsor_2.id, self.sponsor_3.id],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            person_id=[self.guest.id],
            accommodation_id=[self.accommodation_one.id],
        )

        self.client.force_login(get_la_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-overview",
                args=[ar.id],
            )
        )
        context = response.context
        fields = dict(context["fields"])

        self.assertIn("Status", fields)
        self.assertIn(
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED, fields["Status"]
        )

        self.assertIn("Host", fields)
        self.assertEqual(None, fields["Host"])

        self.assertIn("Sponsor", fields)
        self.assertInHTML("Sponsor is not in your LA", fields["Sponsor"])

        self.assertIn("Lower tier Local Authority", fields)
        self.assertIn("ltla_somerset", fields["Lower tier Local Authority"])

        self.assertIn("Upper tier Local Authority", fields)
        self.assertIn("utla_somerset", fields["Upper tier Local Authority"])

        self.assertIn("Guests", fields)
        self.assertEqual([], fields["Guests"])

        self.assertIn("Address", fields)
        self.assertEqual([], fields["Address"])

    def test_overview_displays_active_host_as_host(self):
        ar = AccReqFactory(
            title="Test Access Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            active_host=self.sponsor_1,
            primary_sponsor=self.sponsor_2,
        )

        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-overview",
                args=[ar.id],
            )
        )
        context = response.context
        fields = dict(context["fields"])

        self.assertIn("Host", fields)
        self.assertIn(self.sponsor_1.get_full_name(), fields["Host"])

    def test_overview_displays_primary_sponsor_as_host_if_no_active_host(self):
        ar = AccReqFactory(
            title="Test Access Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            primary_sponsor=self.sponsor_2,
        )

        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-overview",
                args=[ar.id],
            )
        )
        context = response.context
        fields = dict(context["fields"])

        self.assertIn("Host", fields)
        self.assertIn(self.sponsor_2.get_full_name(), fields["Host"])
