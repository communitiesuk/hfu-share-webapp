from unittest.mock import call, patch

from django.urls import reverse

from accounts.enums import GroupType
from accounts.tests.factories import GroupInfoFactory
from ontology.models import ReassignmentRequest
from ontology.models.MvAccommodationRequest import MvAccommodationRequest
from ontology.models.MvInteraction import MvInteraction
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
    ReassignmentRequestFactory,
)
from reassignment_requests.tests.base import ReassignmentRequestsBaseTestCase
from user_management.tests.base import (
    UserGroup,
    get_admin_user,
    get_user_with_groups,
)


class ReassignmentRequestsAcceptRejectTestCase(ReassignmentRequestsBaseTestCase):
    def setUp(self):
        super().setUp()

        GroupInfoFactory(
            ltla_name="ltla_destination",
            utla_name="utla_destination",
            gss_code="E000",
            utla_gss_code="E001",
        )

        self.user = get_user_with_groups(
            [
                UserGroup(
                    name="ltla_destination",
                    type=GroupType.LOCAL_AUTHORITY,
                )
            ]
        )

    def test_accept_reject_request_form_errors_if_user_not_from_destination_la(self):
        self.client.force_login(self.user)

        url = reverse(
            "reassignment-requests:detail-received",
            kwargs={"pk": self.request_to_somerset.pk},
        )

        response = self.client.post(
            url, {"action": "accept", "comments": "Approved for transfer"}
        )

        self.assertEqual(response.status_code, 404)

    def test_accept_reject_request_form_errors_if_form_is_empty(self):
        self.client.force_login(self.user)

        url = reverse(
            "reassignment-requests:detail-received",
            kwargs={"pk": self.pending_request_somerset_source.pk},
        )

        response = self.client.post(url, {"action": "", "comments": ""}, follow=True)

        self.assertContains(response, "This field is required.")

    @patch("reassignment_requests.views.sentry_sdk.metrics.count")
    def test_accept_request_journey_for_full_ar_reassignment(self, sentry_metrics):
        acc = MvAccommodationFactory()

        # create accommodation request with multiple guests
        ar = MvAccommodationRequestFactory(
            number_of_people=2,
            person_id=[self.guest_a.id, self.guest_b.id],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            accommodation_id=[acc.id],
            primary_accommodation=acc,
            active_host=MvVolunteerFactory(),
        )

        request = self.pending_request_somerset_source_multiple_guests
        request.accommodation_request = ar
        request.save()

        # Check before state
        self.assertIsNone(ar.ltla_code_id)
        self.assertIsNone(ar.utla_code_id)

        self.client.force_login(self.user)

        url = reverse(
            "reassignment-requests:detail-received", kwargs={"pk": request.pk}
        )

        response = self.client.post(
            url,
            {"action": "accept", "comments": "Approved for transfer"},
            follow=True,
        )

        # Check success message
        self.assertContains(response, "You have approved the request to move")

        request.refresh_from_db()

        # Same AR is updated
        ar.refresh_from_db()

        self.assertEqual(request.outcome, ReassignmentRequest.Outcome.ACCEPTED)
        self.assertEqual(request.comments, "Approved for transfer")
        self.assertIsNotNone(request.responded_at)
        self.assertEqual(request.responded_by.id, self.user.id)

        # Check AR's location is updated
        self.assertEqual(ar.ltla_name, [request.destination_ltla_name])
        self.assertEqual(ar.utla_name, [request.destination_utla_name])
        self.assertEqual(ar.ltla_code_id, ["E000"])
        self.assertEqual(ar.utla_code_id, ["E001"])

        # Check AR's accommodation is updated
        self.assertIsNone(ar.primary_accommodation)

        # Check AR's checks status is updated
        self.assertEqual(
            ar.checks_status, MvAccommodationRequest.ChecksStatus.REMATCH_REQUIRED
        )

        # Check that the host is unlinked
        self.assertIsNone(ar.is_eoi_host)
        self.assertIsNone(ar.active_host)
        self.assertIsNone(ar.active_eoi_host)

        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=ar
        ).first()

        self.assertIsNotNone(interaction)

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
        )

        # Assert that the metric has been sent to Sentry
        expected_call_attributes = {
            "action": "accept",
            "user_id": self.user.id,
            "is_partial": False,
        }
        self.assertEqual(sentry_metrics.call_count, 1)
        self.assertEqual(
            sentry_metrics.call_args_list,
            [call("reassignment_request", 1, attributes=expected_call_attributes)],
        )

    @patch("reassignment_requests.views.sentry_sdk.metrics.count")
    def test_accept_request_journey_for_partial_reassignment(self, sentry_metrics):
        acc = MvAccommodationFactory()

        # create accommodation request with multiple guests
        ar = MvAccommodationRequestFactory(
            number_of_people=3,
            person_id=[self.guest_a.id, self.guest_b.id, self.guest_c.id],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            accommodation_id=[acc.id],
            primary_accommodation=acc,
            active_host=MvVolunteerFactory(),
        )

        # RR has guest_a and guest_b
        request = self.pending_request_somerset_source_multiple_guests
        request.accommodation_request = ar
        request.save()

        self.client.force_login(self.user)

        url = reverse(
            "reassignment-requests:detail-received", kwargs={"pk": request.pk}
        )

        response = self.client.post(
            url,
            {"action": "accept", "comments": "Approved for transfer"},
            follow=True,
        )

        # Check success message
        self.assertContains(response, "You have approved the request to move")

        ar.refresh_from_db()

        # Old AR is updated
        self.assertEqual(ar.number_of_people, 1)

        # Check old AR's accommodation is not updated
        self.assertEqual(ar.primary_accommodation.id, acc.id)

        # Old AR location is not updated
        self.assertEqual(ar.ltla_name, ["ltla_somerset"])
        self.assertEqual(ar.utla_name, ["utla_somerset"])

        # Old AR's active host is not updated
        self.assertIsNotNone(ar.active_host)

        request.refresh_from_db()

        # New AR resulted from split
        new_ar = MvAccommodationRequest.objects.filter(
            person_id__contained_by=[self.guest_a.id, self.guest_b.id],
            person_id__contains=[self.guest_a.id, self.guest_b.id],
        ).first()

        self.assertEqual(request.outcome, ReassignmentRequest.Outcome.ACCEPTED)
        self.assertEqual(request.comments, "Approved for transfer")
        self.assertIsNotNone(request.responded_at)
        self.assertEqual(request.responded_by.id, self.user.id)

        # Check AR's location is updated
        self.assertEqual(new_ar.ltla_name, [request.destination_ltla_name])
        self.assertEqual(new_ar.utla_name, [request.destination_utla_name])

        # Check AR's checks status is updated
        self.assertEqual(
            new_ar.checks_status, MvAccommodationRequest.ChecksStatus.REMATCH_REQUIRED
        )

        # Check that the host is unlinked
        self.assertIsNone(new_ar.is_eoi_host)
        self.assertIsNone(new_ar.active_host)
        self.assertIsNone(new_ar.active_eoi_host)

        new_ar_interaction = MvInteraction.objects.filter(
            linked_accommodation_request=new_ar
        ).first()
        self.assertIsNotNone(new_ar_interaction)
        self.assertEqual(
            new_ar_interaction.interaction_contact,
            MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
        )

        # Check the old AR also has the accepted reassignment interaction
        old_ar_interaction = MvInteraction.objects.filter(
            linked_accommodation_request=ar
        ).first()
        self.assertIsNotNone(old_ar_interaction)
        self.assertEqual(
            old_ar_interaction.interaction_contact,
            MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
        )

        # Assert that the metric has been sent to Sentry
        expected_call_attributes = {
            "action": "accept",
            "user_id": self.user.id,
            "is_partial": True,
        }
        self.assertEqual(sentry_metrics.call_count, 1)
        self.assertEqual(
            sentry_metrics.call_args_list,
            [call("reassignment_request", 1, attributes=expected_call_attributes)],
        )

    @patch("reassignment_requests.views.sentry_sdk.metrics.count")
    def test_reject_request_journey_for_reassignment(self, sentry_metrics):
        self.client.force_login(self.user)

        # create accommodation request with multiple guests
        ar = MvAccommodationRequestFactory(
            number_of_people=2,
            person_id=[self.guest_a, self.guest_b],
            ltla_name=["ltla_somerset"],
        )

        request = self.pending_request_somerset_source_multiple_guests
        request.accommodation_request = ar
        request.save()

        url = reverse(
            "reassignment-requests:detail-received", kwargs={"pk": request.pk}
        )
        response = self.client.post(
            url,
            {"action": "reject", "comments": "Reasons for rejection"},
            follow=True,
        )

        # Check success message
        self.assertContains(response, "You have rejected the request")

        request.refresh_from_db()

        self.assertEqual(request.outcome, ReassignmentRequest.Outcome.REJECTED)
        self.assertEqual(request.comments, "Reasons for rejection")
        self.assertIsNotNone(request.responded_at)
        self.assertEqual(request.responded_by.id, self.user.id)

        ar.refresh_from_db()

        self.assertEqual(ar.ltla_name, ["ltla_somerset"])

        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=ar
        ).first()
        self.assertIsNotNone(interaction)
        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.REASSIGNMENT_REJECTED,
        )

        # Assert that the metric has been sent to Sentry
        expected_call_attributes = {
            "action": "reject",
            "user_id": self.user.id,
            "is_partial": False,
        }
        self.assertEqual(sentry_metrics.call_count, 1)
        self.assertEqual(
            sentry_metrics.call_args_list,
            [call("reassignment_request", 1, attributes=expected_call_attributes)],
        )

    def test_accept_rr_wont_500_for_missing_source_ltla(self):
        self.client.force_login(self.user)

        acc = MvAccommodationFactory()

        # create accommodation request with multiple guests
        ar = MvAccommodationRequestFactory(
            number_of_people=1,
            person_id=[self.guest_a.id],
            ltla_name=[],
            utla_name=[],
            accommodation_id=[acc.id],
            primary_accommodation=acc,
            active_host=MvVolunteerFactory(),
        )

        request = ReassignmentRequestFactory(
            source_ltla_name=[],
            source_utla_name=[],
            destination_ltla_name="ltla_destination",
            destination_utla_name="utla_destination",
            outcome=ReassignmentRequest.Outcome.PENDING,
            reason="Example reason",
            accommodation_request=ar,
        )

        request.guests.set([self.guest_a])

        response = self.client.post(
            reverse("reassignment-requests:detail-received", kwargs={"pk": request.pk}),
            {"action": "accept", "comments": "Approved for transfer"},
            follow=True,
        )

        # Check success message
        self.assertContains(
            response, "You have approved the request to move Guest A from Unknown LTLA"
        )

    def test_reject_rr_wont_500_for_missing_source_ltla(self):
        self.client.force_login(self.user)

        # create accommodation request with multiple guests
        ar = MvAccommodationRequestFactory(
            number_of_people=1,
            person_id=[self.guest_a],
            ltla_name=[],
        )

        request = ReassignmentRequestFactory(
            source_ltla_name=[],
            source_utla_name=[],
            destination_ltla_name="ltla_destination",
            destination_utla_name="utla_destination",
            outcome=ReassignmentRequest.Outcome.PENDING,
            reason="Example reason",
            accommodation_request=ar,
        )

        request.guests.set([self.guest_a])

        response = self.client.post(
            reverse("reassignment-requests:detail-received", kwargs={"pk": request.pk}),
            {"action": "reject", "comments": "Reasons for rejection"},
            follow=True,
        )

        # Check success message
        self.assertContains(
            response, "You have rejected the request to move Guest A from Unknown LTLA"
        )

    def test_error_message_when_ar_is_none(self):
        self.client.force_login(self.user)

        request = ReassignmentRequestFactory(
            source_ltla_name=["ltla_somerset"],
            source_utla_name=["utla_somerset"],
            destination_ltla_name="ltla_destination",
            destination_utla_name="utla_destination",
            outcome=ReassignmentRequest.Outcome.PENDING,
            reason="Example reason",
            accommodation_request=None,
        )

        request.guests.set([self.guest_a])

        response = self.client.post(
            reverse("reassignment-requests:detail-received", kwargs={"pk": request.pk}),
            {"action": "reject", "comments": "Reasons for rejection"},
            follow=True,
        )

        # Check success message
        self.assertContains(
            response,
            "We are unable to find the the accommodation request for this "
            "reassignment request.",
        )

    def test_interaction_created_when_rr_accepted(self):
        acc = MvAccommodationFactory()

        ar = MvAccommodationRequestFactory(
            number_of_people=1,
            person_id=[self.guest_a.id],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            accommodation_id=[acc.id],
            primary_accommodation=acc,
            active_host=MvVolunteerFactory(),
        )

        request = self.pending_request_somerset_source_single_guest
        request.accommodation_request = ar
        request.save()

        self.client.force_login(self.user)

        url = reverse(
            "reassignment-requests:detail-received", kwargs={"pk": request.pk}
        )

        response = self.client.post(
            url,
            {"action": "accept", "comments": "Approved for transfer"},
            follow=True,
        )

        # Check success message
        self.assertContains(response, "You have approved the request to move")

        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=ar
        ).first()

        self.assertIsNotNone(interaction)
        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
        )
        self.assertEqual(
            interaction.interaction_notes,
            "ltla_destination accepted the reassignment request from ltla_somerset "
            "for [names_list]Guest A.[names_list_end] "
            "Reason for accepting: Approved for transfer",
        )
        self.assertEqual(
            interaction.created_by,
            self.user,
        )

    def test_interaction_created_for_both_ars_when_partial_rr_accepted(self):
        acc = MvAccommodationFactory()

        original_ar = MvAccommodationRequestFactory(
            number_of_people=2,
            person_id=[self.guest_a.id, self.guest_b.id],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            accommodation_id=[acc.id],
            primary_accommodation=acc,
            active_host=MvVolunteerFactory(),
        )

        reassignment_request = ReassignmentRequestFactory(
            source_ltla_name=["ltla_somerset"],
            source_utla_name=["utla_somerset"],
            destination_ltla_name="ltla_destination",
            destination_utla_name="utla_destination",
            outcome=ReassignmentRequest.Outcome.PENDING,
            reason="Example reason",
        )
        reassignment_request.guests.set([self.guest_a])
        reassignment_request.accommodation_request = original_ar
        reassignment_request.save()

        self.client.force_login(self.user)

        url = reverse(
            "reassignment-requests:detail-received",
            kwargs={"pk": reassignment_request.pk},
        )

        response = self.client.post(
            url,
            {"action": "accept", "comments": "Approved for transfer"},
            follow=True,
        )

        # Check success message
        self.assertContains(response, "You have approved the request to move")

        new_ar = MvAccommodationRequest.objects.filter(
            person_id__contained_by=[self.guest_a.id],
            person_id__contains=[self.guest_a.id],
        ).first()

        for ar in [original_ar, new_ar]:
            interaction = MvInteraction.objects.filter(
                linked_accommodation_request=ar
            ).first()

            self.assertIsNotNone(interaction)
            self.assertEqual(
                interaction.interaction_contact,
                MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            )
            self.assertEqual(
                interaction.interaction_type,
                MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            )
            self.assertEqual(
                interaction.interaction_notes,
                "ltla_destination accepted the reassignment request from ltla_somerset "
                "for [names_list]Guest A.[names_list_end] "
                "Reason for accepting: Approved for transfer",
            )
            self.assertEqual(
                interaction.created_by,
                self.user,
            )

    def test_interaction_created_when_rr_with_multi_la_source_accepted(self):
        acc = MvAccommodationFactory()

        ar = MvAccommodationRequestFactory(
            number_of_people=1,
            person_id=[self.guest_a.id],
            ltla_name=["ltla_somerset", "ltla_manchester"],
            utla_name=["utla_somerset", "utla_manchester"],
            accommodation_id=[acc.id],
            primary_accommodation=acc,
            active_host=MvVolunteerFactory(),
        )

        request = self.pending_request_somerset_source_single_guest
        request.source_ltla_name = (
            "ltla_somerset",
            "ltla_manchester",
        )
        request.source_utla_name = (
            "utla_somerset",
            "utla_manchester",
        )
        request.accommodation_request = ar
        request.save()

        self.client.force_login(self.user)

        url = reverse(
            "reassignment-requests:detail-received", kwargs={"pk": request.pk}
        )

        response = self.client.post(
            url,
            {"action": "accept", "comments": "Approved for transfer"},
            follow=True,
        )

        # Check success message
        self.assertContains(response, "You have approved the request to move")

        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=ar
        ).first()

        self.assertIsNotNone(interaction)
        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
        )
        self.assertEqual(
            interaction.interaction_notes,
            "ltla_destination accepted the reassignment request from "
            "ltla_somerset|ltla_manchester for "
            "[names_list]Guest A.[names_list_end] Reason for accepting: "
            "Approved for transfer",
        )
        self.assertEqual(
            interaction.created_by,
            self.user,
        )

    def test_interaction_created_when_rr_with_multiple_guests_accepted(self):
        acc = MvAccommodationFactory()

        guest_a = MvPersonFactory(
            id="guest_a",
            first_name="Guest",
            last_name="A",
        )
        guest_b = MvPersonFactory(
            id="guest_b",
            first_name="Guest",
            last_name="B",
        )

        request = ReassignmentRequestFactory(
            source_ltla_name=["ltla_somerset"],
            source_utla_name=["utla_somerset"],
            destination_ltla_name="ltla_destination",
            destination_utla_name="utla_destination",
            outcome=ReassignmentRequest.Outcome.PENDING,
            reason="Example reason",
        )

        ar = MvAccommodationRequestFactory(
            number_of_people=1,
            person_id=[guest_a.id, guest_b.id],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            accommodation_id=[acc.id],
            primary_accommodation=acc,
            active_host=MvVolunteerFactory(),
        )

        request.guests.set([guest_a, guest_b])
        request.accommodation_request = ar
        request.save()

        self.client.force_login(self.user)

        url = reverse(
            "reassignment-requests:detail-received", kwargs={"pk": request.pk}
        )

        response = self.client.post(
            url,
            {"action": "accept", "comments": "These guests have moved to my LA."},
            follow=True,
        )

        # Check success message
        self.assertContains(response, "You have approved the request to move")

        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=ar
        ).first()

        self.assertIsNotNone(interaction)
        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
        )
        self.assertEqual(
            interaction.interaction_notes,
            "ltla_destination accepted the reassignment request from "
            "ltla_somerset for "
            "[names_list]Guest A and Guest B.[names_list_end] Reason for accepting: "
            "These guests have moved to my LA.",
        )
        self.assertEqual(
            interaction.created_by,
            self.user,
        )

    def test_interaction_created_when_rr_rejected(self):
        acc = MvAccommodationFactory()

        ar = MvAccommodationRequestFactory(
            number_of_people=1,
            person_id=[self.guest_a.id],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            accommodation_id=[acc.id],
            primary_accommodation=acc,
            active_host=MvVolunteerFactory(),
        )

        request = self.pending_request_somerset_source_single_guest
        request.accommodation_request = ar
        request.save()

        self.client.force_login(self.user)

        url = reverse(
            "reassignment-requests:detail-received", kwargs={"pk": request.pk}
        )

        response = self.client.post(
            url,
            {"action": "reject", "comments": "This guest has not moved to my LA."},
            follow=True,
        )

        # Check success message
        self.assertContains(response, "You have rejected the request to move")

        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=ar
        ).first()

        self.assertIsNotNone(interaction)
        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.REASSIGNMENT_REJECTED,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.REASSIGNMENT_REJECTED,
        )
        self.assertEqual(
            interaction.interaction_notes,
            "ltla_destination rejected the reassignment request from ltla_somerset "
            "for [names_list]Guest A.[names_list_end] Reason for rejecting: "
            "This guest has not moved to my LA.",
        )
        self.assertEqual(
            interaction.created_by,
            self.user,
        )

    def test_interaction_created_for_ar_when_partial_rr_rejected(self):
        acc = MvAccommodationFactory()

        ar = MvAccommodationRequestFactory(
            number_of_people=2,
            person_id=[self.guest_a.id, self.guest_b.id],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            accommodation_id=[acc.id],
            primary_accommodation=acc,
            active_host=MvVolunteerFactory(),
        )

        reassignment_request = ReassignmentRequestFactory(
            source_ltla_name=["ltla_somerset"],
            source_utla_name=["utla_somerset"],
            destination_ltla_name="ltla_destination",
            destination_utla_name="utla_destination",
            outcome=ReassignmentRequest.Outcome.PENDING,
            reason="Example reason",
        )
        reassignment_request.guests.set([self.guest_a])
        reassignment_request.accommodation_request = ar
        reassignment_request.save()

        self.client.force_login(self.user)

        url = reverse(
            "reassignment-requests:detail-received",
            kwargs={"pk": reassignment_request.pk},
        )

        response = self.client.post(
            url,
            {"action": "reject", "comments": "Rejected for transfer"},
            follow=True,
        )

        # Check success message
        self.assertContains(response, "You have rejected the request to move")

        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=ar
        ).first()

        self.assertIsNotNone(interaction)
        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.REASSIGNMENT_REJECTED,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.REASSIGNMENT_REJECTED,
        )
        self.assertEqual(
            interaction.interaction_notes,
            "ltla_destination rejected the reassignment request from ltla_somerset "
            "for [names_list]Guest A.[names_list_end] "
            "Reason for rejecting: Rejected for transfer",
        )
        self.assertEqual(
            interaction.created_by,
            self.user,
        )

    def test_interaction_created_when_rr_with_multi_la_source_rejected(self):
        acc = MvAccommodationFactory()

        ar = MvAccommodationRequestFactory(
            number_of_people=1,
            person_id=[self.guest_a.id],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            accommodation_id=[acc.id],
            primary_accommodation=acc,
            active_host=MvVolunteerFactory(),
        )

        request = self.pending_request_somerset_source_single_guest
        request.source_ltla_name = (
            "ltla_somerset",
            "ltla_manchester",
        )
        request.source_utla_name = (
            "utla_somerset",
            "utla_manchester",
        )
        request.accommodation_request = ar
        request.save()

        self.client.force_login(self.user)

        url = reverse(
            "reassignment-requests:detail-received", kwargs={"pk": request.pk}
        )

        response = self.client.post(
            url,
            {"action": "reject", "comments": "This guest has not moved to my LA."},
            follow=True,
        )

        # Check success message
        self.assertContains(response, "You have rejected the request to move")

        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=ar
        ).first()

        self.assertIsNotNone(interaction)
        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.REASSIGNMENT_REJECTED,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.REASSIGNMENT_REJECTED,
        )
        self.assertEqual(
            interaction.interaction_notes,
            "ltla_destination rejected the reassignment request from "
            "ltla_somerset|ltla_manchester for "
            "[names_list]Guest A.[names_list_end] Reason for rejecting: "
            "This guest has not moved to my LA.",
        )
        self.assertEqual(
            interaction.created_by,
            self.user,
        )

    def test_interaction_created_when_rr_with_multiple_guests_rejected(self):
        acc = MvAccommodationFactory()

        ar = MvAccommodationRequestFactory(
            number_of_people=1,
            person_id=[self.guest_a.id, self.guest_b.id],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            accommodation_id=[acc.id],
            primary_accommodation=acc,
            active_host=MvVolunteerFactory(),
        )

        request = self.pending_request_somerset_source_multiple_guests
        request.accommodation_request = ar
        request.save()

        self.client.force_login(self.user)

        url = reverse(
            "reassignment-requests:detail-received", kwargs={"pk": request.pk}
        )

        response = self.client.post(
            url,
            {"action": "reject", "comments": "This guest has not moved to my LA."},
            follow=True,
        )

        # Check success message
        self.assertContains(response, "You have rejected the request to move")

        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=ar
        ).first()

        self.assertIsNotNone(interaction)
        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.REASSIGNMENT_REJECTED,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.REASSIGNMENT_REJECTED,
        )
        self.assertEqual(
            interaction.interaction_notes,
            "ltla_destination rejected the reassignment request from "
            "ltla_somerset for [names_list]Guest A and Guest B.[names_list_end] "
            "Reason for rejecting: This guest has not moved to my LA.",
        )
        self.assertEqual(
            interaction.created_by,
            self.user,
        )

    def test_rr_ltla_utla_code_is_set_to_none_if_groupinfo_is_none(self):
        acc = MvAccommodationFactory()

        # create accommodation request with multiple guests
        ar = MvAccommodationRequestFactory(
            number_of_people=2,
            person_id=[self.guest_a.id, self.guest_b.id],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            ltla_code_id=["E001"],
            utla_code_id=["E002"],
            accommodation_id=[acc.id],
            primary_accommodation=acc,
            active_host=MvVolunteerFactory(),
        )

        # Ltla and Utla without GroupInfo
        self.pending_request_somerset_source_multiple_guests.destination_ltla_name = (
            "other_ltla_destination"
        )
        self.pending_request_somerset_source_multiple_guests.destination_utla_name = (
            "other_utla_destination"
        )
        self.pending_request_somerset_source_multiple_guests.save()

        request = self.pending_request_somerset_source_multiple_guests
        request.accommodation_request = ar
        request.save()

        # Check before state
        self.assertEqual(ar.ltla_code_id, ["E001"])
        self.assertEqual(ar.utla_code_id, ["E002"])

        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse("reassignment-requests:detail-received", kwargs={"pk": request.pk}),
            {"action": "accept", "comments": "Approved for transfer"},
            follow=True,
        )

        # Check success message
        self.assertContains(response, "You have approved the request to move")

        request.refresh_from_db()

        # Same AR is updated
        ar.refresh_from_db()

        # Check AR's location is updated
        self.assertIsNone(ar.ltla_code_id)
        self.assertIsNone(ar.utla_code_id)

    def test_rr_ltla_utla_code_is_set_to_none_if_groupinfo_exists_with_none_gss(self):
        # Test group with no gss and utla gss codes
        GroupInfoFactory(
            ltla_name="other_ltla_destination_2",
            utla_name="other_utla_destination_2",
            gss_code=None,
            utla_gss_code=None,
        )

        acc = MvAccommodationFactory()

        # create accommodation request with multiple guests
        ar = MvAccommodationRequestFactory(
            number_of_people=2,
            person_id=[self.guest_a.id, self.guest_b.id],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            ltla_code_id=["E001"],
            utla_code_id=["E002"],
            accommodation_id=[acc.id],
            primary_accommodation=acc,
            active_host=MvVolunteerFactory(),
        )

        # Ltla and Utla without GroupInfo
        self.pending_request_somerset_source_multiple_guests.destination_ltla_name = (
            "other_ltla_destination_2"
        )
        self.pending_request_somerset_source_multiple_guests.destination_utla_name = (
            "other_utla_destination_2"
        )
        self.pending_request_somerset_source_multiple_guests.save()

        request = self.pending_request_somerset_source_multiple_guests
        request.accommodation_request = ar
        request.save()

        # Check before state
        self.assertEqual(ar.ltla_code_id, ["E001"])
        self.assertEqual(ar.utla_code_id, ["E002"])

        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse("reassignment-requests:detail-received", kwargs={"pk": request.pk}),
            {"action": "accept", "comments": "Approved for transfer"},
            follow=True,
        )

        # Check success message
        self.assertContains(response, "You have approved the request to move")

        request.refresh_from_db()

        # Same AR is updated
        ar.refresh_from_db()

        # Check AR's location is updated
        self.assertIsNone(ar.ltla_code_id)
        self.assertIsNone(ar.utla_code_id)
