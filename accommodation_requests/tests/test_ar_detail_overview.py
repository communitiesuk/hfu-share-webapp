import http.client

from django.urls import reverse

from accommodation_requests.tests.base import AccommodationRequestsBaseTestCase
from accounts.tests.base import TestSessionTokenMixin
from ontology.models import MvAccommodationRequest
from ontology.tests.factories import MvAccommodationRequestFactory as AccReqFactory
from user_management.tests.base import (
    get_admin_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
)


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

    def test_overview_shows_current_host_tag_against_host(self):
        ar = AccReqFactory(
            title="Test Access Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            active_host=self.sponsor_1,
        )

        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-overview",
                args=[ar.id],
            )
        )
        fields = dict(response.context["fields"])

        self.assertIn(self.sponsor_1.get_full_name(), fields["Host"])
        self.assertIn("Current host", fields["Host"])
        self.assertIn("govuk-tag--green", fields["Host"])

    def test_overview_shows_current_host_tag_against_primary_sponsor_fallback(self):
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
        fields = dict(response.context["fields"])

        self.assertIn(self.sponsor_2.get_full_name(), fields["Host"])
        self.assertIn("Current host", fields["Host"])

    def test_overview_shows_no_current_host_tag_when_no_host_shown(self):
        ar = AccReqFactory(
            title="Test Access Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            sponsor_id=[self.sponsor_2.id, self.sponsor_3.id],
        )

        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-overview",
                args=[ar.id],
            )
        )
        fields = dict(response.context["fields"])

        self.assertIsNone(fields["Host"])
        self.assertNotContains(response, "Current host")

    def test_overview_shows_current_accommodation_tag_against_primary_only(self):
        ar = AccReqFactory(
            title="Test Access Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one.id, self.accomodation_three.id],
            primary_accommodation=self.accomodation_three,
        )

        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-overview",
                args=[ar.id],
            )
        )
        fields = dict(response.context["fields"])

        addresses = fields["Address"]
        tagged_addresses = [
            address for address in addresses if "Current accommodation" in address
        ]
        untagged_addresses = [
            address for address in addresses if "Current accommodation" not in address
        ]

        self.assertEqual(1, len(tagged_addresses))
        self.assertIn(self.accomodation_three.full_address, tagged_addresses[0])
        self.assertIn("govuk-tag--green", tagged_addresses[0])
        self.assertEqual([self.accommodation_one.full_address], untagged_addresses)

    def test_overview_shows_no_current_accommodation_tag_without_primary(self):
        ar = AccReqFactory(
            title="Test Access Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one.id],
        )

        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-overview",
                args=[ar.id],
            )
        )
        fields = dict(response.context["fields"])

        self.assertEqual([self.accommodation_one.full_address], fields["Address"])
        self.assertNotContains(response, "Current accommodation")

    def get_lower_tier_local_authority_value(self, ar):
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-overview",
                args=[ar.id],
            )
        )
        return dict(response.context["fields"])["Lower tier Local Authority"]

    def test_overview_links_to_the_assign_to_la_form_when_there_is_no_ltla(self):
        ar = AccReqFactory(
            title="Test Access Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            ltla_name=None,
        )

        self.client.force_login(get_mhclg_user())

        self.assertInHTML(
            '<a class="govuk-link govuk-link--no-visited-state" href="{}">'
            "Assign local authority</a>".format(
                reverse(
                    "unassigned-accommodation-requests:assign-local-authority",
                    args=[ar.id],
                )
                + "?reset=true"
            ),
            self.get_lower_tier_local_authority_value(ar),
        )

    def test_overview_has_no_assign_to_la_link_when_the_ltla_is_set(self):
        ar = AccReqFactory(
            title="Test Access Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            ltla_name=["ltla_somerset"],
        )

        self.client.force_login(get_mhclg_user())

        self.assertEqual(
            ["ltla_somerset"], self.get_lower_tier_local_authority_value(ar)
        )

    def test_overview_has_no_assign_to_la_link_for_users_who_cannot_assign(self):
        ar = AccReqFactory(
            title="Test Access Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            ltla_name=None,
        )

        self.client.force_login(get_service_support_user())

        self.assertIsNone(self.get_lower_tier_local_authority_value(ar))

    def test_overview_shows_the_default_back_button_by_default(self):
        ar = AccReqFactory(
            title="Test Access Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

        self.client.force_login(get_mhclg_user())

        response = self.client.get(
            reverse("accommodation-requests:detail-overview", args=[ar.id])
        )

        self.assertContains(response, "Back to list of accommodation requests")
        self.assertNotContains(response, "Back to unassigned accommodation requests")

    def test_overview_shows_the_back_to_unassigned_list_button_when_requested(self):
        ar = AccReqFactory(
            title="Test Access Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

        self.client.force_login(get_mhclg_user())

        response = self.client.get(
            reverse("accommodation-requests:detail-overview", args=[ar.id])
            + "?from=unassigned-accommodation-requests"
        )

        self.assertNotContains(response, "Back to list of accommodation requests")
        self.assertInHTML(
            '<a href="{}" class="govuk-button govuk-button--secondary">'
            "Back to unassigned accommodation requests</a>".format(
                reverse(
                    "unassigned-accommodation-requests:"
                    "unassigned-accommodation-requests"
                )
            ),
            response.content.decode(),
        )
