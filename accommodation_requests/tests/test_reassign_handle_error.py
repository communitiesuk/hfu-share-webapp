from unittest.mock import patch

from django.db import DatabaseError
from django.db.models import QuerySet
from django.urls import reverse

from accommodation_requests.tests.base import AccommodationRequestsBaseTestCase
from accommodation_requests.views import ReassignGuestsFormSteps
from accounts.tests.base import TestSessionTokenMixin
from ontology.models import MvAccommodationRequest, MvInteraction
from ontology.models.ReassignmentRequest import ReassignmentRequest
from user_management.tests.base import get_admin_user


class ReassignGuestsDBErrorTestCase(
    TestSessionTokenMixin, AccommodationRequestsBaseTestCase
):
    def setUp(self):
        super().setUp()
        self.user = get_admin_user()
        self.client.force_login(self.user)

    def get_reassign_step_url(self, step):
        return reverse(
            "accommodation-requests:reassign-guests-step",
            kwargs={"pk": self.one_guest_acc_req.pk, "step": step},
        )

    def _run_reassign_wizard_to_confirmation(self):
        pk = self.one_guest_acc_req.pk

        # Step 1: Select country
        response = self.client.post(
            self.get_reassign_step_url(ReassignGuestsFormSteps.COUNTRY),
            {
                "country-country": "England",
                f"reassign_guests_form_wizard_{pk}-current_step": (
                    ReassignGuestsFormSteps.COUNTRY
                ),
            },
            follow=True,
        )
        self.assertContains(response, "Select local authority")

        # Step 2: Select local authority
        response = self.client.post(
            self.get_reassign_step_url(ReassignGuestsFormSteps.LOCAL_AUTHORITY),
            {
                "local_authority-local_authority": self.english_ltla_name,
                f"reassign_guests_form_wizard_{pk}-current_step": (
                    ReassignGuestsFormSteps.LOCAL_AUTHORITY
                ),
            },
            follow=True,
        )
        self.assertContains(response, "Reason for moving guest")

        # Step 3: Provide reason
        response = self.client.post(
            self.get_reassign_step_url(ReassignGuestsFormSteps.REASON),
            {
                "reason-reason": "Test reason for reassignment.",
                f"reassign_guests_form_wizard_{pk}-current_step": (
                    ReassignGuestsFormSteps.REASON
                ),
            },
            follow=True,
        )
        self.assertContains(response, "Are you sure you want to move")
        return pk

    def _post_confirmation(self, pk):
        return self.client.post(
            self.get_reassign_step_url(ReassignGuestsFormSteps.CONFIRMATION),
            {
                "confirmation-confirm_guests_moved": "on",
                f"reassign_guests_form_wizard_{pk}-current_step": (
                    ReassignGuestsFormSteps.CONFIRMATION
                ),
            },
            follow=True,
        )

    def _assert_rollback(self, reassignment_count_before, interaction_count_before):
        self.assertEqual(ReassignmentRequest.objects.count(), reassignment_count_before)
        self.assertEqual(MvInteraction.objects.count(), interaction_count_before)
        self.one_guest_acc_req.refresh_from_db()
        self.assertEqual(
            self.one_guest_acc_req.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

    def _assert_error_message(self, response):
        self.assertContains(
            response,
            "The reassignment request was not sent. "
            "If the problem continues raise a support ticket.",
        )

    def test_db_error_on_reassignment_request_create(self):
        pk = self._run_reassign_wizard_to_confirmation()
        reassignment_count = ReassignmentRequest.objects.count()
        interaction_count = MvInteraction.objects.count()
        with patch(
            "ontology.models.ReassignmentRequest.ReassignmentRequest.objects.create",
            side_effect=DatabaseError,
        ):
            response = self._post_confirmation(pk)
        self._assert_error_message(response)
        self._assert_rollback(reassignment_count, interaction_count)

    def test_db_error_on_set_guests(self):
        pk = self._run_reassign_wizard_to_confirmation()
        through_model = ReassignmentRequest.guests.through
        original_bulk_create = QuerySet.bulk_create
        reassignment_count = ReassignmentRequest.objects.count()
        interaction_count = MvInteraction.objects.count()

        def fail_for_through(self, *args, **kwargs):
            if self.model == through_model:
                raise DatabaseError
            return original_bulk_create(self, *args, **kwargs)

        with patch.object(QuerySet, "bulk_create", fail_for_through):
            response = self._post_confirmation(pk)
        self._assert_error_message(response)
        self._assert_rollback(reassignment_count, interaction_count)

    def test_db_error_on_reassignment_request_save(self):
        pk = self._run_reassign_wizard_to_confirmation()
        reassignment_count = ReassignmentRequest.objects.count()
        interaction_count = MvInteraction.objects.count()
        with patch(
            "ontology.models.ReassignmentRequest.ReassignmentRequest.save",
            side_effect=DatabaseError,
        ):
            response = self._post_confirmation(pk)
        self._assert_error_message(response)
        self._assert_rollback(reassignment_count, interaction_count)

    def test_db_error_on_create_interaction(self):
        pk = self._run_reassign_wizard_to_confirmation()
        reassignment_count = ReassignmentRequest.objects.count()
        interaction_count = MvInteraction.objects.count()
        with patch(
            "ontology.models.MvInteraction.MvInteraction.create_interaction",
            side_effect=DatabaseError,
        ):
            response = self._post_confirmation(pk)
        self._assert_error_message(response)
        self._assert_rollback(reassignment_count, interaction_count)
