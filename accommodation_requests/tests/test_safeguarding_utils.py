from contextlib import nullcontext
from unittest.mock import MagicMock, patch

from django.test import TestCase

from accommodation_requests.safeguarding_utils import (
    bulk_create_escalations,
    recalculate_checks_status,
)
from ontology.models import SafeguardingReferral
from ontology.tests.factories import MvPersonFactory, SafeguardingReferralFactory


class RecalculateChecksTests(TestCase):
    def test_updates_status_when_changed(self):
        with (
            patch(
                "accommodation_requests.safeguarding_utils.transaction.atomic",
                return_value=nullcontext(),
            ) as mock_atomic,
            patch(
                "accommodation_requests.safeguarding_utils.MvAccommodationRequest"
            ) as mock_model,
            patch("accommodation_requests.safeguarding_utils.logger"),
            patch("accommodation_requests.safeguarding_utils.sentry_sdk"),
        ):
            ar = MagicMock()
            ar.checks_status = "old-status"
            ar.determine_checks_status_from_linked_objects.return_value = "new-status"

            mock_model.objects.select_for_update.return_value.get.return_value = ar

            result = recalculate_checks_status(
                accommodation_request_id=123,
                recalculate_closed=True,
                author="some_author",
            )

            mock_atomic.assert_called_once_with()
            mock_model.objects.select_for_update.assert_called_once_with()

            ar.determine_checks_status_from_linked_objects.assert_called_once_with(
                excluded_statuses=[]
            )
            ar.update_checks_status.assert_called_once_with(
                "new-status", author="some_author"
            )

            self.assertEqual(result, "new-status")

    def test_does_not_update_when_status_is_unchanged(self):
        with (
            patch(
                "accommodation_requests.safeguarding_utils.transaction.atomic",
                return_value=nullcontext(),
            ),
            patch(
                "accommodation_requests.safeguarding_utils.MvAccommodationRequest"
            ) as mock_model,
            patch("accommodation_requests.safeguarding_utils.logger"),
            patch("accommodation_requests.safeguarding_utils.sentry_sdk"),
        ):
            ar = MagicMock()
            ar.checks_status = "same-status"
            ar.determine_checks_status_from_linked_objects.return_value = "same-status"

            mock_model.objects.select_for_update.return_value.get.return_value = ar

            result = recalculate_checks_status(
                accommodation_request_id=123, recalculate_closed=False
            )

            ar.update_checks_status.assert_not_called()
            self.assertEqual(result, "same-status")

    def test_returns_none_and_logs_when_determine_raises(self):
        with (
            patch(
                "accommodation_requests.safeguarding_utils.transaction.atomic",
                return_value=nullcontext(),
            ),
            patch(
                "accommodation_requests.safeguarding_utils.MvAccommodationRequest"
            ) as mock_model,
            patch("accommodation_requests.safeguarding_utils.logger") as mock_logger,
            patch(
                "accommodation_requests.safeguarding_utils.sentry_sdk"
            ) as mock_sentry,
        ):
            ar = MagicMock()
            ar.checks_status = "old-status"
            ar.determine_checks_status_from_linked_objects.side_effect = Exception(
                "some exception"
            )

            mock_model.objects.select_for_update.return_value.get.return_value = ar

            result = recalculate_checks_status(accommodation_request_id=123)

            ar.update_checks_status.assert_not_called()
            mock_logger.exception.assert_called_once()
            mock_sentry.capture_exception.assert_called_once_with()
            self.assertIsNone(result)

    def test_raises_if_accommodation_request_not_found(self):
        with (
            patch(
                "accommodation_requests.safeguarding_utils.transaction.atomic",
                return_value=nullcontext(),
            ),
            patch(
                "accommodation_requests.safeguarding_utils.MvAccommodationRequest"
            ) as mock_model,
            patch("accommodation_requests.safeguarding_utils.logger"),
            patch("accommodation_requests.safeguarding_utils.sentry_sdk"),
        ):
            mock_model.objects.select_for_update.return_value.get.side_effect = (
                Exception("not found")
            )

            with self.assertRaises(Exception):  # noqa: B017
                recalculate_checks_status(accommodation_request_id=123)


class BulkCreateEscalationsPrincipalFilterTests(TestCase):
    def test_does_not_create_referrals_for_duplicate_people(self):
        duplicate = MvPersonFactory(is_principal=False)

        bulk_create_escalations([duplicate])

        self.assertFalse(
            SafeguardingReferral.objects.filter(person_id=duplicate.id).exists()
        )

    def test_creates_referrals_for_principal_and_unmerged_people_only(self):
        principal = MvPersonFactory(is_principal=True)
        duplicate = MvPersonFactory(is_principal=False)
        blank = MvPersonFactory(is_principal=None)

        bulk_create_escalations([principal, duplicate, blank])

        referral_person_ids = set(
            SafeguardingReferral.objects.values_list("person_id", flat=True)
        )
        self.assertEqual(referral_person_ids, {principal.id, blank.id})

    def test_does_not_update_existing_referral_for_duplicate_person(self):
        duplicate = MvPersonFactory(is_principal=False)
        existing = SafeguardingReferralFactory(
            person=duplicate,
            alerted_status=SafeguardingReferral.AlertedStatus.ALERTED,
            modified_at=None,
        )

        bulk_create_escalations([duplicate])

        existing.refresh_from_db()
        self.assertEqual(
            existing.alerted_status, SafeguardingReferral.AlertedStatus.ALERTED
        )
        self.assertIsNone(existing.modified_at)
