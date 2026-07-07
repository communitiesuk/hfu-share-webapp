from unittest.mock import patch

from django.db import DatabaseError
from django.urls import reverse

from ontology.models import MvAccommodationRequest, MvInteraction, ReassignmentRequest
from ontology.tests.factories import MvAccommodationFactory
from reassignment_requests.tests.base import ReassignmentRequestsBaseTestCase
from user_management.tests.base import get_la_user


class ReassignmentRequestsDBErrorTestCase(ReassignmentRequestsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = get_la_user()
        self.client.force_login(self.user)
        self.request = self.pending_request_somerset_source_multiple_guests

    def _post_action(self, action="accept"):
        url = reverse(
            "reassignment-requests:detail-received",
            kwargs={"pk": self.request.pk},
        )
        return self.client.post(
            url, {"action": action, "comments": "test"}, follow=True
        )

    def _assert_error_message(self, response):
        self.assertContains(
            response,
            "The reassignment request was not updated. "
            "If the problem continues raise a support ticket.",
        )

    def _assert_rollback(self, ar_count_before, interaction_count_before):
        self.assertEqual(MvAccommodationRequest.objects.count(), ar_count_before)
        self.assertEqual(MvInteraction.objects.count(), interaction_count_before)
        self.request.refresh_from_db()
        self.assertEqual(self.request.outcome, ReassignmentRequest.Outcome.PENDING)

    def test_db_error_on_ar_save(self):
        ar_count = MvAccommodationRequest.objects.count()
        interaction_count = MvInteraction.objects.count()
        with patch(
            "ontology.models.MvAccommodationRequest.MvAccommodationRequest.save",
            side_effect=DatabaseError,
        ):
            response = self._post_action()
        self._assert_error_message(response)
        self._assert_rollback(ar_count, interaction_count)

    def test_db_error_on_update_accommodation(self):
        self.pending_request_somerset_source_multiple_guests_ar.person_id = [
            self.guest_a.id,
            self.guest_b.id,
        ]
        self.pending_request_somerset_source_multiple_guests_ar.save()
        ar_count = MvAccommodationRequest.objects.count()
        interaction_count = MvInteraction.objects.count()
        with patch(
            "ontology.models.MvAccommodationRequest.MvAccommodationRequest.update_accommodation",
            side_effect=DatabaseError,
        ):
            response = self._post_action()
        self._assert_error_message(response)
        self._assert_rollback(ar_count, interaction_count)

    def test_db_error_on_unlink_host(self):
        self.pending_request_somerset_source_multiple_guests_ar.person_id = [
            self.guest_a.id,
            self.guest_b.id,
        ]
        accommodation = MvAccommodationFactory(
            ltla_name="ltla_somerset", utla_name="utla_somerset"
        )
        self.pending_request_somerset_source_multiple_guests_ar.accommodation_id = [
            accommodation.id,
        ]
        self.pending_request_somerset_source_multiple_guests_ar.save()
        ar_count = MvAccommodationRequest.objects.count()
        interaction_count = MvInteraction.objects.count()
        with patch(
            "ontology.models.MvAccommodationRequest.MvAccommodationRequest.unlink_host",
            side_effect=DatabaseError,
        ):
            response = self._post_action()
        self._assert_error_message(response)
        self._assert_rollback(ar_count, interaction_count)

    def test_db_error_on_split_guests(self):
        ar_count = MvAccommodationRequest.objects.count()
        interaction_count = MvInteraction.objects.count()
        with patch(
            "ontology.models.MvAccommodationRequest.MvAccommodationRequest.split_guests",
            side_effect=DatabaseError,
        ):
            response = self._post_action()
        self._assert_error_message(response)
        self._assert_rollback(ar_count, interaction_count)

    def test_db_error_on_create_interaction_on_reject(self):
        ar_count = MvAccommodationRequest.objects.count()
        interaction_count = MvInteraction.objects.count()
        with patch(
            "ontology.models.MvInteraction.MvInteraction.create_interaction",
            side_effect=DatabaseError,
        ):
            response = self._post_action(action="reject")
        self._assert_error_message(response)
        self._assert_rollback(ar_count, interaction_count)

    def test_db_error_on_reassignment_request_save_on_reject(self):
        ar_count = MvAccommodationRequest.objects.count()
        interaction_count = MvInteraction.objects.count()
        with patch(
            "ontology.models.ReassignmentRequest.ReassignmentRequest.save",
            side_effect=DatabaseError,
        ):
            response = self._post_action(action="reject")
        self._assert_error_message(response)
        self._assert_rollback(ar_count, interaction_count)
