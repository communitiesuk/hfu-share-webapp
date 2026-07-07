from django.urls import reverse

from accommodation_requests.tests.base import AccommodationRequestsBaseTestCase
from accounts.tests.base import TestSessionTokenMixin
from ontology.models import MvAccommodationRequest, MvPerson, ReassignmentRequest
from ontology.tests.factories import MvAccommodationRequestFactory as AccReqFactory
from ontology.tests.factories import (
    MvPersonFactory,
    ReassignmentRequestFactory,
)
from user_management.tests.base import get_admin_user, get_la_user


class AccommodationRequestCloseTestCase(
    TestSessionTokenMixin, AccommodationRequestsBaseTestCase
):
    def test_actions_should_include_close_request_for_open_requests(self):
        self.client.force_login(get_admin_user())
        for open_request in self.open_acc_reqs:
            response = self.client.get(
                reverse(
                    "accommodation-requests:detail-actions",
                    args=[open_request.pk],
                )
            )

            self.assertContains(response, "Close accommodation request")
            self.assertNotContains(response, "Reopen accommodation request")

    def test_actions_should_include_reopen_request_for_closed_left_program_requests(
        self,
    ):
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-actions",
                args=[self.closed_left_prog_acc_req.pk],
            )
        )

        self.assertContains(response, "Reopen accommodation request")
        self.assertNotContains(response, "Close accommodation request")

    def test_actions_should_include_reopen_request_for_cancelled_requests(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-actions",
                args=[self.cancelled_acc_req.pk],
            )
        )

        self.assertContains(response, "Reopen accommodation request")
        self.assertNotContains(response, "Close accommodation request")

    def test_actions_should_not_include_close_or_reopen_request_for_closed_empty(
        self,
    ):
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-actions",
                args=[self.closed_empty_acc_req.pk],
            )
        )

        self.assertNotContains(response, "Reopen accommodation request")
        self.assertNotContains(response, "Close accommodation request")

    def test_actions_should_not_include_close_or_reopen_request_for_closed_duplicate(
        self,
    ):
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-actions",
                args=[self.closed_duplicate_acc_req.pk],
            )
        )

        self.assertNotContains(response, "Reopen accommodation request")
        self.assertNotContains(response, "Close accommodation request")


class AccommodationRequestWithdrawSponsorTestCase(
    TestSessionTokenMixin, AccommodationRequestsBaseTestCase
):
    def test_actions_shows_withdraw_sponsor_with_start_for_ar_with_active_sponsors(
        self,
    ):
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-actions",
                args=[self.partial_active_sponsor_req.pk],
            )
        )

        self.assertContains(response, "Withdraw sponsor")
        self.assertNotContains(response, "All sponsors withdrawn")

    def test_actions_hides_withdraw_sponsor_start_for_ar_with_no_active_sponsors(
        self,
    ):
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-actions",
                args=[self.no_active_sponsors_req.pk],
            )
        )

        self.assertContains(response, "Withdraw sponsor")
        self.assertContains(response, "All sponsors withdrawn")

    def test_hides_withdraw_sponsor_start_ar_with_no_active_sponsors_within_users_la(
        self,
    ):
        self.client.force_login(get_la_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-actions",
                args=[self.active_sponsor_from_other_la_req.pk],
            )
        )

        self.assertContains(response, "Withdraw sponsor")
        self.assertContains(response, "Sponsor is not in your LA")


class AccommodationRequestMoveGuestTestCase(
    TestSessionTokenMixin, AccommodationRequestsBaseTestCase
):
    def test_actions_should_include_move_guests_for_open_requests(self):
        self.client.force_login(get_admin_user())
        for open_request in self.open_acc_reqs:
            response = self.client.get(
                reverse(
                    "accommodation-requests:detail-actions",
                    args=[open_request.pk],
                )
            )

            self.assertContains(response, "Move guests")

    def test_actions_should_not_include_move_guests_for_closed_requests(self):
        user = get_admin_user()
        self.client.force_login(user)

        for closed_request in self.cannot_move_guests_acc_reqs:
            response = self.client.get(
                reverse(
                    "accommodation-requests:detail-actions",
                    args=[closed_request.pk],
                )
            )

            self.assertNotContains(response, "Move guests")

    def test_actions_shows_red_tag_when_ar_guest_array_is_empty(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-actions",
                args=[self.no_guests_acc_req.pk],
            )
        )

        self.assertContains(response, "All guests moved")

    def test_shows_red_tag_when_ar_guest_array_contains_only_non_existent_guests(
        self,
    ):
        # Intentionally not using the MvPersonFactory here so that we don't save to
        # the DB. This is testing a scenario we saw in prod where an AR had
        # a FK to a guest, but no guest with that key could be found in the
        # MvPerson table
        guest = MvPerson(id="1234")
        acc_req = AccReqFactory(
            title="Invalid guests acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            person_id=[guest.id],
        )

        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-actions",
                args=[acc_req.pk],
            )
        )

        self.assertContains(response, "All guests moved")

    def test_shows_red_tag_when_ar_guest_array_contains_only_guests_outside_users_la(
        self,
    ):
        # Guest LA is determined via the guest.accommodation_request LTLA and UTLA names
        # Therefore simulating a guest from a different LA by creating a new guest and
        # AR, where the guest is missing the link to the AR but is in the AR.person_id
        guest = MvPersonFactory(id="person-id", first_name="John", last_name="Doe")
        acc_req = AccReqFactory(
            title="One guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one],
            number_of_people=1,
            person_id=[guest.pk],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
        )

        self.client.force_login(get_la_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-actions",
                args=[acc_req.pk],
            )
        )

        self.assertContains(response, "All guests moved")


class AccommodationRequestSoftLockTestCase(
    TestSessionTokenMixin, AccommodationRequestsBaseTestCase
):
    def test_actions_returns_empty_list_when_pending_reassignment_request_exists(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Create a reassignment request with PENDING outcome
        ReassignmentRequestFactory(
            accommodation_request=self.checks_required_req,
            outcome=ReassignmentRequest.Outcome.PENDING,
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-actions",
                args=[self.checks_required_req.pk],
            )
        )

        # Check that no action
        self.assertNotContains(response, "Close accommodation request")
        self.assertNotContains(response, "Reopen accommodation request")
        self.assertNotContains(response, "Move guests")
        self.assertNotContains(response, "Withdraw sponsor")

    def test_actions_available_when_no_pending_reassignment_requests(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-actions",
                args=[self.checks_required_req.pk],
            )
        )

        self.assertContains(response, "Close accommodation request")

    def test_actions_available_when_reassignment_request_not_pending(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Create reassignment requests with non-pending outcomes
        ReassignmentRequestFactory(
            accommodation_request=self.checks_required_req,
            outcome=ReassignmentRequest.Outcome.ACCEPTED,
        )
        ReassignmentRequestFactory(
            accommodation_request=self.checks_required_req,
            outcome=ReassignmentRequest.Outcome.REJECTED,
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-actions",
                args=[self.checks_required_req.pk],
            )
        )

        self.assertContains(response, "Close accommodation request")

    def test_pending_reassignment_notification_is_visible(self):
        self.client.force_login(get_admin_user())
        reassignment = ReassignmentRequestFactory(
            accommodation_request=self.checks_required_req,
            outcome=ReassignmentRequest.Outcome.PENDING,
        )
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-actions",
                args=[self.checks_required_req.pk],
            )
        )
        for guest in reassignment.guests.all():
            self.assertContains(response, guest.get_full_name())
        self.assertContains(response, reassignment.destination_ltla_name)
        self.assertContains(response, "You sent a request to move")
        self.assertContains(response, "pending request to move guests")
        self.assertContains(response, "govuk-notification-banner__content")
