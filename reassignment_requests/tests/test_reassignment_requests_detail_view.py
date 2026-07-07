import http.client

from django.template.defaultfilters import cut
from django.template.defaultfilters import date as django_date
from django.urls import reverse
from django.utils import timezone

from accounts.enums import GroupType
from accounts.models import User
from ontology.models import ReassignmentRequest
from ontology.tests.factories import ReassignmentRequestFactory
from reassignment_requests.tests.base import ReassignmentRequestsBaseTestCase
from user_management.tests.base import (
    UserGroup,
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_user_with_groups,
    get_user_with_no_access,
)


class ReassignmentRequestsDetailViewTestCase(ReassignmentRequestsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.reassignment_request = self.pending_request_somerset_source_multiple_guests

    def get_detail_page_response(
        self,
        user: User | None = None,
        reassignment_request: ReassignmentRequest | None = None,
        url_name: str = "detail-made",
    ):
        if not reassignment_request:
            reassignment_request = self.reassignment_request

        if not user:
            user = get_user_with_groups(
                [
                    UserGroup(
                        name=ltla_name,
                        type=GroupType.LOCAL_AUTHORITY,
                    )
                    for ltla_name in reassignment_request.source_ltla_name
                ]
            )

        self.client.force_login(user)

        url = reverse(
            f"reassignment-requests:{url_name}", kwargs={"pk": reassignment_request.pk}
        )

        return self.client.get(url)

    def test_access_granted_for_admin_user(self):
        user = get_admin_user()
        response = self.get_detail_page_response(user=user)
        self.assertEqual(response.status_code, http.client.OK)

    def test_access_granted_for_la_user(self):
        user = get_la_user()
        response = self.get_detail_page_response(user=user)
        self.assertEqual(response.status_code, http.client.OK)

    def test_access_granted_for_da_user(self):
        user = get_da_user()
        request = self.da_request
        response = self.get_detail_page_response(
            user=user, reassignment_request=request
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_access_granted_for_mhclg_user(self):
        user = get_mhclg_user()
        response = self.get_detail_page_response(user=user)
        self.assertEqual(response.status_code, http.client.OK)

    def test_access_granted_for_support_user(self):
        user = get_service_support_user()
        response = self.get_detail_page_response(user=user)
        self.assertEqual(response.status_code, http.client.OK)

    def test_access_not_granted_for_ukvi_user(self):
        user = get_user_with_groups(
            [
                UserGroup(name="ukvi", type=GroupType.HOME_OFFICE),
            ]
        )
        response = self.get_detail_page_response(user=user)
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_page_has_correct_heading(self):
        response = self.get_detail_page_response()
        self.assertContains(
            response, "Request to move guests to a different local authority"
        )

    def test_request_date_is_shown(self):
        response = self.get_detail_page_response()
        self.assertContains(response, "Request date")
        local_time = timezone.localtime(self.reassignment_request.created_at)
        formatted_date = django_date(local_time, r"j F Y \a\t g:ia")
        expected_string = cut(formatted_date, ".")

        self.assertContains(response, expected_string)

    def test_guest_list_is_shown(self):
        response = self.get_detail_page_response()
        self.assertContains(response, "Guests")
        for guest in self.reassignment_request.guests.all():
            self.assertContains(response, guest.full_name)

    def test_destination_la_is_shown(self):
        response = self.get_detail_page_response()
        self.assertContains(response, "Moving to")
        self.assertNotContains(response, "Moving from")
        self.assertContains(response, self.reassignment_request.destination_ltla_name)

    def test_source_la_is_shown(self):
        response = self.get_detail_page_response(
            url_name="detail-received",
        )

        self.assertNotContains(response, "Moving to")
        self.assertContains(response, "Moving from")
        self.assertContains(response, self.reassignment_request.source_ltla_name[0])

    def test_source_multi_la_is_shown(self):
        response = self.get_detail_page_response(
            reassignment_request=self.pending_request_multi_la_source,
            url_name="detail-received",
        )

        self.assertContains(response, "Moving from")
        self.assertNotContains(response, "Moving to")
        self.assertContains(
            response, "|".join(self.pending_request_multi_la_source.source_ltla_name)
        )

    def test_reason_is_shown(self):
        response = self.get_detail_page_response()
        self.assertContains(response, "Reason")
        self.assertContains(response, self.reassignment_request.reason)

    def test_return_to_list_button_is_shown(self):
        response = self.get_detail_page_response()
        self.assertContains(response, "Return to list of requests")

    def test_cancel_request_button_is_shown_when_request_is_pending_and_la_made_it(
        self,
    ):
        response = self.get_detail_page_response(
            reassignment_request=self.pending_request_somerset_source_multiple_guests
        )
        self.assertContains(response, "Cancel request")

    def test_cancel_button_is_not_shown_if_request_is_pending_and_other_la_made_it(
        self,
    ):
        response = self.get_detail_page_response(
            reassignment_request=self.request_to_somerset,
            user=get_user_with_groups(
                [
                    UserGroup(
                        name=self.request_to_somerset.destination_ltla_name,
                        type=GroupType.LOCAL_AUTHORITY,
                    )
                ]
            ),
        )
        self.assertNotContains(response, "Cancel request")

    def test_cancel_request_button_is_not_shown_when_request_is_accepted(self):
        response = self.get_detail_page_response(
            reassignment_request=self.accepted_request_somerset_source
        )
        self.assertNotContains(response, "Cancel request")

    def test_cancel_request_button_is_not_shown_when_request_is_rejected(self):
        response = self.get_detail_page_response(
            reassignment_request=self.rejected_request_somerset_source
        )
        self.assertNotContains(response, "Cancel request")

    def test_cancel_request_button_is_not_shown_when_request_needs_ar(self):
        response = self.get_detail_page_response(
            reassignment_request=self.needs_ar_request_somerset_source
        )
        self.assertNotContains(response, "Cancel request")

    def test_user_cannot_see_reassignment_request_not_from_their_la(self):
        response = self.get_detail_page_response(user=get_user_with_no_access())
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_dev_user_can_see_any_reassignment_request(self):
        response = self.get_detail_page_response(user=get_admin_user())
        self.assertEqual(response.status_code, http.client.OK)

    def test_accept_reject_form_shows_for_destination_la_user_with_pending(self):
        # A user for the destination LA
        response = self.get_detail_page_response(
            user=get_user_with_groups(
                [
                    UserGroup(
                        name=self.request_to_somerset.destination_ltla_name,
                        type=GroupType.LOCAL_AUTHORITY,
                    )
                ]
            ),
            reassignment_request=self.request_to_somerset,
        )

        # Should show the accept/reject form
        self.assertContains(response, "Accept request")
        self.assertContains(response, "Reject request")

    def test_accept_reject_form_does_not_show_for_non_pending_requests(self):
        # A user for the destination LA
        response = self.get_detail_page_response(
            user=get_user_with_groups(
                [
                    UserGroup(
                        name=self.request_to_somerset.destination_ltla_name,
                        type=GroupType.LOCAL_AUTHORITY,
                    )
                ]
            ),
            reassignment_request=self.accepted_request_somerset_source,
        )

        self.assertNotContains(response, "Accept request")
        self.assertNotContains(response, "Reject request")
        self.assertNotContains(response, "Confirm")

    def test_accept_reject_form_wont_show_for_user_that_doesnt_match_destination(self):
        # A user for the destination LA
        response = self.get_detail_page_response(
            reassignment_request=self.request_to_somerset
        )

        # Should not show the accept/reject form
        self.assertNotContains(response, "Accept request")
        self.assertNotContains(response, "Reject request")

    def test_requests_with_none_value_source_ltla_names_do_not_cause_exceptions(self):
        user = get_admin_user()
        self.client.force_login(user)

        pending_request_no_source_ltla_name = ReassignmentRequestFactory(
            source_ltla_name=[None],
            source_utla_name=["utla_somerset"],
            destination_ltla_name="ltla_destination",
            destination_utla_name="utla_destination",
            outcome=ReassignmentRequest.Outcome.PENDING,
            reason="Example reason",
        )

        url = reverse(
            "reassignment-requests:detail-received",
            kwargs={"pk": pending_request_no_source_ltla_name.pk},
        )

        self.client.get(url)
