import http.client
from unittest.mock import call, patch

from django.urls import reverse
from django.utils import timezone

from accounts.enums import GroupType
from ontology.models import ReassignmentRequest
from reassignment_requests.tests.base import ReassignmentRequestsBaseTestCase
from user_management.tests.base import (
    UserGroup,
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_user_with_groups,
)


class ReassignmentRequestsCancelRequestTestCase(ReassignmentRequestsBaseTestCase):
    def test_form_renders_correctly_single_guest_case(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "reassignment_requests:cancel-made",
                kwargs={"pk": self.pending_request_somerset_source_single_guest.pk},
            )
        )

        self.assertContains(
            response, "Cancel request to move guests to a different local authority"
        )
        self.assertContains(
            response,
            f"Are you sure you want to cancel the request to move "
            f"{
                self.pending_request_somerset_source_single_guest.formatted_guest_names()
            }"
            f" to {
                self.pending_request_somerset_source_single_guest.destination_ltla_name
            }?",
            html=True,
        )
        self.assertContains(response, "Yes, cancel the request", html=True)
        self.assertContains(response, "Cancel request", html=True)
        self.assertContains(response, "Go back", html=True)

    def test_form_renders_correctly_multi_guest_case(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "reassignment_requests:cancel-made",
                kwargs={"pk": self.pending_request_somerset_source_multiple_guests.pk},
            )
        )

        self.assertContains(
            response, "Cancel request to move guests to a different local authority"
        )
        self.assertContains(
            response,
            f"Are you sure you want to cancel the request to move "
            f"{
                self.pending_request_somerset_source_multiple_guests.formatted_guest_names()
            }"
            f" to {
                self.pending_request_somerset_source_multiple_guests.destination_ltla_name
            }?",
            html=True,
        )
        self.assertContains(response, "Yes, cancel the request", html=True)
        self.assertContains(response, "Cancel request", html=True)
        self.assertContains(response, "Go back", html=True)

    def test_validation_error_appears(self):
        self.client.force_login(get_admin_user())
        response = self.client.post(
            reverse(
                "reassignment_requests:cancel-made",
                kwargs={"pk": self.pending_request_somerset_source_multiple_guests.pk},
            ),
            data={"submit": ""},
            follow=True,
        )

        self.assertContains(
            response, "Tick the box to confirm you want to cancel the request"
        )

    def test_redirected_to_ar_actions_after_success(self):
        self.client.force_login(get_admin_user())
        response = self.client.post(
            reverse(
                "reassignment_requests:cancel-made",
                kwargs={"pk": self.pending_request_somerset_source_multiple_guests.pk},
            ),
            data={"confirmation": "on", "submit": ""},
            follow=True,
        )

        ar = self.pending_request_somerset_source_multiple_guests.accommodation_request
        self.assertRedirects(
            response,
            reverse(
                "accommodation-requests:detail-actions",
                kwargs={
                    "pk": ar.pk,
                },
            ),
        )

    def test_shows_success_message(self):
        self.client.force_login(get_admin_user())
        response = self.client.post(
            reverse(
                "reassignment_requests:cancel-made",
                kwargs={"pk": self.pending_request_somerset_source_multiple_guests.pk},
            ),
            data={"confirmation": "on", "submit": ""},
            follow=True,
        )

        self.assertContains(
            response,
            f"You have cancelled the request to move "
            f"{
                self.pending_request_somerset_source_multiple_guests.formatted_guest_names()
            }"
            f" to {
                self.pending_request_somerset_source_multiple_guests.destination_ltla_name
            }",
        )

    def test_reassignment_request_correctly_updated_after_cancellation(self):
        reassignment_request: ReassignmentRequest = (
            self.pending_request_somerset_source_multiple_guests
        )

        user = get_admin_user()
        self.client.force_login(user)
        self.client.post(
            reverse(
                "reassignment_requests:cancel-made",
                kwargs={"pk": reassignment_request.pk},
            ),
            data={"confirmation": "on", "submit": ""},
            follow=True,
        )

        reassignment_request.refresh_from_db()

        self.assertEqual(
            reassignment_request.outcome, ReassignmentRequest.Outcome.REJECTED
        )
        self.assertEqual(reassignment_request.comments, "Cancelled by sending LA")
        self.assertLessEqual(
            abs((timezone.now() - reassignment_request.responded_at).total_seconds()),
            10,
        )
        self.assertEqual(reassignment_request.responded_by, user)

    def test_mhclg_users_cant_access(self):
        self.client.force_login(get_mhclg_user())

        response = self.client.get(
            reverse(
                "reassignment_requests:cancel-made",
                kwargs={"pk": self.pending_request_somerset_source_multiple_guests.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_ukvi_users_cant_access(self):
        self.client.force_login(
            get_user_with_groups(
                [
                    UserGroup(name="ukvi", type=GroupType.HOME_OFFICE),
                ]
            )
        )

        response = self.client.get(
            reverse(
                "reassignment_requests:cancel-made",
                kwargs={"pk": self.pending_request_somerset_source_multiple_guests.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_service_support_users_cant_access(self):
        self.client.force_login(get_service_support_user())

        response = self.client.get(
            reverse(
                "reassignment_requests:cancel-made",
                kwargs={"pk": self.pending_request_somerset_source_multiple_guests.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_admin_users_can_access(self):
        self.client.force_login(get_admin_user())

        response = self.client.get(
            reverse(
                "reassignment_requests:cancel-made",
                kwargs={"pk": self.pending_request_somerset_source_multiple_guests.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_la_users_can_access(self):
        self.client.force_login(get_la_user())

        response = self.client.get(
            reverse(
                "reassignment_requests:cancel-made",
                kwargs={"pk": self.pending_request_somerset_source_multiple_guests.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_da_users_can_access(self):
        self.client.force_login(get_da_user())

        response = self.client.get(
            reverse(
                "reassignment_requests:cancel-made",
                kwargs={"pk": self.pending_request_edinburgh_source.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    @patch("reassignment_requests.views.sentry_sdk.metrics.count")
    def test_sentry_metric_sent_following_cancellation(self, sentry_metrics):
        self.user = get_la_user()
        self.client.force_login(self.user)
        self.client.post(
            reverse(
                "reassignment_requests:cancel-made",
                kwargs={"pk": self.pending_request_somerset_source_multiple_guests.pk},
            ),
            data={"confirmation": "on", "submit": ""},
        )

        # Assert that the metric has been sent to Sentry
        expected_call_attributes = {
            "action": "cancelled",
            "user_id": self.user.id,
            "is_partial": False,
        }
        self.assertEqual(sentry_metrics.call_count, 1)
        self.assertEqual(
            sentry_metrics.call_args_list,
            [call("reassignment_request", 1, attributes=expected_call_attributes)],
        )
