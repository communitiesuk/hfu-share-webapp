import http.client

from django.urls import reverse

from accommodation_requests.tests.base import AccommodationRequestsBaseTestCase
from accounts.tests.base import TestSessionTokenMixin
from ontology.models import MvAccommodationRequest, MvInteraction
from user_management.tests.base import get_admin_user, get_user_with_no_access


class AccommodationRequestReopenTestCase(
    TestSessionTokenMixin, AccommodationRequestsBaseTestCase
):
    def test_should_return_409_for_open_accommodation_requests(self):
        user = get_admin_user()
        self.client.force_login(user)

        for open_acc_req in self.open_acc_reqs:
            response = self.client.get(
                reverse(
                    "accommodation-requests:reopen",
                    args=[open_acc_req.id],
                )
            )

            self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_should_return_409_for_closed_non_reopenable_accommodation_requests(self):
        user = get_admin_user()
        self.client.force_login(user)

        for closed_acc_req in self.closed_cannot_be_reopened_reqs:
            response = self.client.get(
                reverse(
                    "accommodation-requests:reopen",
                    args=[closed_acc_req.id],
                )
            )

            self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_should_return_404_for_ar_user_has_no_access_to(self):
        no_access_user = get_user_with_no_access()

        self.client.force_login(no_access_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:reopen",
                args=[self.closed_left_prog_acc_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_return_reopen_req_form_for_closed_reopenable_accommodation_reqs(self):
        user = get_admin_user()
        self.client.force_login(user)

        for closed_acc_req in self.closed_can_be_reopened_reqs:
            response = self.client.get(
                reverse(
                    "accommodation-requests:reopen",
                    args=[closed_acc_req.id],
                )
            )

            self.assertEqual(response.status_code, http.client.OK)
            self.assertContains(response, "Reopen accommodation request for")

            self.assertContains(
                response, "Are you sure you want to reopen this accommodation request?"
            )
            self.assertContains(
                response,
                "Please confirm you want to reopen this request",
            )
            self.assertContains(response, "Yes, reopen this accommodation request")

            self.assertContains(response, "Reopen accommodation request")
            self.assertContains(response, "Cancel")

    def test_reopen_accommodation_request_updates_record_and_tracks_interaction(self):
        user = get_admin_user()
        self.client.force_login(user)

        closed_acc_req = self.closed_left_prog_acc_req

        initial_interaction_count = MvInteraction.objects.count()

        response = self.client.post(
            f"/accommodation-requests/{closed_acc_req.id}/reopen",
            {
                "confirmation": True,
            },
        )

        self.assertEqual(response.status_code, http.client.FOUND)

        closed_acc_req.refresh_from_db()
        self.assertEqual(
            closed_acc_req.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )
        self.assertEqual(closed_acc_req.last_modified_by, user.username)
        self.assertTrue(closed_acc_req.edited_in_app)

        self.assertEqual(MvInteraction.objects.count(), initial_interaction_count + 1)
        new_interaction = MvInteraction.objects.get(
            linked_accommodation_request=closed_acc_req
        )
        self.assertEqual(
            new_interaction.interaction_contact,
            MvInteraction.InteractionContact.RETURNED_TO_PROGRAMME,
        )
        self.assertEqual(
            new_interaction.interaction_type,
            MvInteraction.InteractionContact.RETURNED_TO_PROGRAMME,
        )
        self.assertEqual(new_interaction.created_by, user)
        self.assertEqual(
            new_interaction.title,
            MvInteraction.InteractionContact.RETURNED_TO_PROGRAMME,
        )
