import http.client

from django.urls import reverse

from accommodation_requests.tests.base import AccommodationRequestsBaseTestCase
from accounts.tests.base import TestSessionTokenMixin
from ontology.models import MvAccommodationRequest, MvInteraction, MvPerson
from ontology.tests.factories import MvGroupFactory
from user_management.tests.base import get_admin_user, get_user_with_no_access


class AccommodationRequestCloseTestCase(
    TestSessionTokenMixin, AccommodationRequestsBaseTestCase
):
    def test_should_return_409_for_closed_accommodation_requests(self):
        self.client.force_login(get_admin_user())
        for closed_acc_req in self.closed_acc_reqs:
            response = self.client.get(
                reverse(
                    "accommodation-requests:close-for-guests",
                    args=[closed_acc_req.id],
                )
            )

            self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_should_return_404_for_ar_user_has_no_access_to(self):
        no_access_user = get_user_with_no_access()
        self.client.force_login(no_access_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:close-for-guests",
                args=[self.checks_required_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_return_close_request_form_for_open_accommodation_requests(self):
        self.client.force_login(get_admin_user())
        for open_acc_req in self.open_acc_reqs:
            response = self.client.get(
                reverse(
                    "accommodation-requests:close-for-guests",
                    args=[open_acc_req.id],
                )
            )

            self.assertEqual(response.status_code, http.client.OK)
            self.assertContains(response, "Close accommodation request to")

            self.assertContains(response, "Reason for closing request")
            self.assertContains(
                response,
                "Select whether the guest chose not to travel to the UK, "
                "or their next steps outside the Homes for Ukraine scheme.",
            )
            self.assertContains(response, "Comment")
            self.assertContains(
                response,
                "Add any relevant notes for audit or reporting (max 500 characters)",
            )

            self.assertContains(response, "Update record")
            self.assertContains(response, "Cancel")

    def test_close_accommodation_request_updates_record_and_tracks_interaction(self):
        user = get_admin_user()
        self.client.force_login(user)
        open_acc_req = self.checks_required_req
        reason = MvAccommodationRequest.ClosedReason.CHOSE_NOT_TO_TRAVEL_TO_UK
        comment = "Test comment"

        initial_interaction_count = MvInteraction.objects.count()
        initial_ar_count = MvAccommodationRequest.objects.count()

        response = self.client.post(
            f"/accommodation-requests/{open_acc_req.id}/close-for-guests",
            {
                "reason": reason,
                "comment": comment,
            },
        )

        self.assertEqual(response.status_code, http.client.FOUND)

        open_acc_req.refresh_from_db()
        self.assertEqual(
            open_acc_req.checks_status,
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
        )
        self.assertEqual(open_acc_req.last_modified_by, user.get_full_name())

        self.assertEqual(MvAccommodationRequest.objects.count(), initial_ar_count)
        self.assertEqual(MvInteraction.objects.count(), initial_interaction_count + 1)

        new_interaction = MvInteraction.objects.get(
            linked_accommodation_request=open_acc_req
        )
        self.assertEqual(
            new_interaction.interaction_contact,
            MvInteraction.InteractionContact.LEAVING_PROGRAMME,
        )
        self.assertEqual(new_interaction.interaction_type, reason)
        self.assertEqual(new_interaction.interaction_notes, reason + ": " + comment)
        self.assertEqual(new_interaction.created_by, user)
        self.assertEqual(
            new_interaction.title, MvInteraction.InteractionContact.LEAVING_PROGRAMME
        )

    def test_close_ar_journey_updated_ar_and_tracks_interaction_when_no_comment_entered(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)
        open_acc_req = self.checks_required_req
        reason = MvAccommodationRequest.ClosedReason.CHOSE_NOT_TO_TRAVEL_TO_UK

        initial_interaction_count = MvInteraction.objects.count()
        initial_ar_count = MvAccommodationRequest.objects.count()

        response = self.client.post(
            f"/accommodation-requests/{open_acc_req.id}/close-for-guests",
            {
                "reason": reason,
            },
        )

        self.assertEqual(response.status_code, http.client.FOUND)

        open_acc_req.refresh_from_db()
        self.assertEqual(
            open_acc_req.checks_status,
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
        )
        self.assertEqual(open_acc_req.last_modified_by, user.get_full_name())

        self.assertEqual(MvAccommodationRequest.objects.count(), initial_ar_count)
        self.assertEqual(MvInteraction.objects.count(), initial_interaction_count + 1)

        new_interaction = MvInteraction.objects.get(
            linked_accommodation_request=open_acc_req
        )
        self.assertEqual(
            new_interaction.interaction_contact,
            MvInteraction.InteractionContact.LEAVING_PROGRAMME,
        )
        self.assertEqual(new_interaction.interaction_type, reason)
        self.assertEqual(new_interaction.interaction_notes, reason)
        self.assertEqual(new_interaction.created_by, user)
        self.assertEqual(
            new_interaction.title, MvInteraction.InteractionContact.LEAVING_PROGRAMME
        )

    def test_select_guests_appears_for_ar_with_multiple_guests(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:close-for-guests",
                args=[self.multiple_guests_acc_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "Select guests")

        for person_id in self.multiple_guests_acc_req.person_id:
            person = MvPerson.objects.get(id=person_id)
            self.assertContains(response, person.full_name)

    def test_select_guests_does_not_appear_for_ar_with_single_guest(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_request = self.one_guest_acc_req

        response = self.client.get(
            reverse(
                "accommodation-requests:close-for-guests",
                args=[accommodation_request.id],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertNotContains(response, "Select guests")

        person = MvPerson.objects.get(id=accommodation_request.person_id[0])
        self.assertNotContains(response, person.full_name)

    def test_close_ar_creates_new_ar_for_partial_guest_selection(self):
        user = get_admin_user()
        self.client.force_login(user)

        group = MvGroupFactory(id="test-group-id")
        self.guest.group = group
        self.guest.save()
        self.guest_2.group = group
        self.guest_2.save()

        original_acc_req = self.multiple_guests_acc_req
        original_acc_req.group = group
        original_acc_req.save()

        original_acc_req_status = original_acc_req.checks_status

        reason = MvAccommodationRequest.ClosedReason.CHOSE_NOT_TO_TRAVEL_TO_UK
        comment = "Test comment"
        selected_guest = original_acc_req.person_id[-1]

        initial_interaction_count = MvInteraction.objects.count()
        initial_ar_count = MvAccommodationRequest.objects.count()

        response = self.client.post(
            f"/accommodation-requests/{original_acc_req.id}/close-for-guests",
            {
                "reason": reason,
                "comment": comment,
                "guests": [selected_guest],
            },
        )

        self.assertEqual(response.status_code, http.client.FOUND)

        original_acc_req.refresh_from_db()
        self.assertEqual(
            original_acc_req.checks_status,
            original_acc_req_status,
        )
        self.assertTrue(selected_guest not in original_acc_req.person_id)

        self.assertEqual(MvInteraction.objects.count(), initial_interaction_count + 1)
        self.assertEqual(MvAccommodationRequest.objects.count(), initial_ar_count + 1)

        new_acc_req = MvAccommodationRequest.objects.get(person_id=[selected_guest])
        self.assertEqual(
            new_acc_req.checks_status,
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
        )
        self.assertEqual(new_acc_req.last_modified_by, user.get_full_name())
        self.assertTrue(new_acc_req.edited_in_app)
        self.assertNotEqual(new_acc_req.group_id, original_acc_req.group_id)

        new_interaction = MvInteraction.objects.get(
            linked_accommodation_request=new_acc_req
        )
        self.assertEqual(
            new_interaction.interaction_contact,
            MvInteraction.InteractionContact.LEAVING_PROGRAMME,
        )
        self.assertEqual(new_interaction.interaction_type, reason)
        self.assertEqual(new_interaction.interaction_notes, reason + ": " + comment)
        self.assertEqual(new_interaction.created_by, user)
        self.assertEqual(
            new_interaction.title, MvInteraction.InteractionContact.LEAVING_PROGRAMME
        )

    def test_close_ar_uses_same_ar_for_all_guest_selection(self):
        user = get_admin_user()
        self.client.force_login(user)

        open_acc_req = self.multiple_guests_acc_req

        reason = MvAccommodationRequest.ClosedReason.CHOSE_NOT_TO_TRAVEL_TO_UK
        comment = "Test comment"
        selected_guests = open_acc_req.person_id

        initial_interaction_count = MvInteraction.objects.count()
        initial_ar_count = MvAccommodationRequest.objects.count()

        response = self.client.post(
            f"/accommodation-requests/{open_acc_req.id}/close-for-guests",
            {
                "reason": reason,
                "comment": comment,
                "guests": selected_guests,
            },
        )

        self.assertEqual(response.status_code, http.client.FOUND)

        self.assertEqual(MvInteraction.objects.count(), initial_interaction_count + 1)
        self.assertEqual(MvAccommodationRequest.objects.count(), initial_ar_count)

        open_acc_req.refresh_from_db()
        self.assertEqual(
            open_acc_req.checks_status,
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
        )
        self.assertEqual(open_acc_req.last_modified_by, user.get_full_name())
        self.assertTrue(open_acc_req.edited_in_app)

        self.assertEqual(MvInteraction.objects.count(), initial_interaction_count + 1)
        self.assertEqual(MvAccommodationRequest.objects.count(), initial_ar_count)

        new_interaction = MvInteraction.objects.get(
            linked_accommodation_request=open_acc_req
        )
        self.assertEqual(
            new_interaction.interaction_contact,
            MvInteraction.InteractionContact.LEAVING_PROGRAMME,
        )
        self.assertEqual(new_interaction.interaction_type, reason)
        self.assertEqual(new_interaction.interaction_notes, reason + ": " + comment)
        self.assertEqual(new_interaction.created_by, user)
        self.assertEqual(
            new_interaction.title, MvInteraction.InteractionContact.LEAVING_PROGRAMME
        )

    def test_redirects_to_actions_tab_with_success_message(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.guest.accommodation = self.accommodation_one
        self.guest.save()
        self.one_guest_acc_req.primary_accommodation = self.accommodation_one
        self.one_guest_acc_req.save()
        open_acc_req = self.one_guest_acc_req

        reason = MvAccommodationRequest.ClosedReason.RETURNED_TO_UKRAINE
        comment = "Test comment"

        response = self.client.post(
            f"/accommodation-requests/{open_acc_req.id}/close-for-guests",
            {
                "reason": reason,
                "comment": comment,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, http.client.OK)

        self.assertContains(
            response,
            f"{self.guest.get_full_name()} moved out of "
            f"{self.accommodation_one.full_address}. Accommodation request closed.",
        )

    def test_success_message_does_not_include_address_if_unknown(self):
        user = get_admin_user()
        self.client.force_login(user)

        open_acc_req = self.multiple_guests_acc_req

        reason = MvAccommodationRequest.ClosedReason.RETURNED_TO_UKRAINE
        comment = "Test comment"
        selected_guests = open_acc_req.person_id

        response = self.client.post(
            f"/accommodation-requests/{open_acc_req.id}/close-for-guests",
            {
                "reason": reason,
                "comment": comment,
                "guests": selected_guests,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, http.client.OK)

        self.assertContains(response, "You closed this accommodation request.")
