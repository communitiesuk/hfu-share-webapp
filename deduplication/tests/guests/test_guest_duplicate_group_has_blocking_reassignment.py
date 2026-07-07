from datetime import datetime, timezone

from django.test import TestCase

from deduplication.tests.factories import GuestDuplicateGroupFactory
from ontology.models import ReassignmentRequest
from ontology.tests.factories import (
    MvPersonFactory,
    ReassignmentRequestFactory,
)


class GuestDuplicateGroupHasBlockingReassignmentForUndoTestCase(TestCase):
    def setUp(self):
        self.first_guest = MvPersonFactory(is_principal=True)
        self.second_guest = MvPersonFactory(is_principal=True)
        self.principal_guest = MvPersonFactory(is_principal=True)

        self.dup_group = GuestDuplicateGroupFactory.create(
            principal_record=self.principal_guest,
            created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        self.dup_group.guests.set([self.first_guest, self.second_guest])
        self.dup_group.save()

    def test_should_not_block_when_no_reassignment_exists(self):
        self.assertFalse(
            self.dup_group.has_blocking_reassignment_for_undo(self.principal_guest.pk)
        )

    def test_should_not_block_when_reassignment_responded_before_dedup(self):
        rr = ReassignmentRequestFactory(
            outcome=ReassignmentRequest.Outcome.ACCEPTED,
            responded_at=datetime(2025, 12, 31, 23, 59, tzinfo=timezone.utc),
        )
        rr.guests.set([self.principal_guest])

        self.assertFalse(
            self.dup_group.has_blocking_reassignment_for_undo(self.principal_guest.pk)
        )

    def test_should_block_when_reassignment_is_pending(self):
        rr = ReassignmentRequestFactory(outcome=ReassignmentRequest.Outcome.PENDING)
        rr.guests.set([self.principal_guest])

        self.assertTrue(
            self.dup_group.has_blocking_reassignment_for_undo(self.principal_guest.pk)
        )

    def test_should_block_when_reassignment_responded_after_dedup(self):
        rr = ReassignmentRequestFactory(
            outcome=ReassignmentRequest.Outcome.ACCEPTED,
            responded_at=datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc),
        )
        rr.guests.set([self.principal_guest])

        self.assertTrue(
            self.dup_group.has_blocking_reassignment_for_undo(self.principal_guest.pk)
        )

    def test_should_not_block_when_reassignment_is_rejected(self):
        rr = ReassignmentRequestFactory(
            outcome=ReassignmentRequest.Outcome.REJECTED,
            responded_at=datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc),
        )
        rr.guests.set([self.principal_guest])

        self.assertFalse(
            self.dup_group.has_blocking_reassignment_for_undo(self.principal_guest.pk)
        )

    def test_should_return_true_for_can_undo_when_no_blocking_reassignment_exists(self):
        self.assertTrue(self.dup_group.can_undo_deduplication(self.principal_guest.pk))

    def test_should_return_false_for_can_undo_when_blocking_reassignment_exists(self):
        rr = ReassignmentRequestFactory(
            outcome=ReassignmentRequest.Outcome.ACCEPTED,
            responded_at=datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc),
        )
        rr.guests.set([self.principal_guest])

        self.assertFalse(self.dup_group.can_undo_deduplication(self.principal_guest.pk))


class GuestDuplicateGroupHasBlockingReassignmentForDedupeTestCase(TestCase):
    def setUp(self):
        self.first_guest = MvPersonFactory(is_principal=True)
        self.second_guest = MvPersonFactory(is_principal=True)
        self.principal_guest = MvPersonFactory(is_principal=True)

        self.dup_group = GuestDuplicateGroupFactory.create(
            principal_record=self.principal_guest,
            created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        self.dup_group.guests.set([self.first_guest, self.second_guest])
        self.dup_group.save()

    def test_should_not_block_when_no_reassignment_exists(self):
        self.assertFalse(
            self.dup_group.has_blocking_reassignment_for_dedupe(self.principal_guest.pk)
        )

    def test_should_block_when_reassignment_is_pending(self):
        rr = ReassignmentRequestFactory(outcome=ReassignmentRequest.Outcome.PENDING)
        rr.guests.set([self.principal_guest])

        self.assertTrue(
            self.dup_group.has_blocking_reassignment_for_dedupe(self.principal_guest.pk)
        )

    def test_should_not_block_when_reassignment_is_rejected(self):
        rr = ReassignmentRequestFactory(
            outcome=ReassignmentRequest.Outcome.REJECTED,
            responded_at=datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc),
        )
        rr.guests.set([self.principal_guest])

        self.assertFalse(
            self.dup_group.has_blocking_reassignment_for_dedupe(self.principal_guest.pk)
        )

    def test_should_return_true_for_can_dedupe_when_no_pending_reassignment_exists(
        self,
    ):
        self.assertTrue(self.dup_group.can_deduplicate(self.principal_guest.pk))

    def test_should_return_false_for_can_dedupe_when_pending_reassignment_exists(self):
        rr = ReassignmentRequestFactory(
            outcome=ReassignmentRequest.Outcome.PENDING,
            responded_at=datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc),
        )
        rr.guests.set([self.principal_guest])

        self.assertFalse(self.dup_group.can_deduplicate(self.principal_guest.pk))
