from datetime import datetime, timezone

from django.test import TestCase

from deduplication.models import GuestDuplicateGroup
from deduplication.tests.factories import GuestDuplicateGroupFactory
from ontology.tests.factories import MvPersonFactory


class GuestDuplicateGroupTestCase(TestCase):
    def setUp(self):
        self.guest_one = MvPersonFactory()
        self.guest_two = MvPersonFactory()

        self.duplicate_group = GuestDuplicateGroupFactory(
            is_archived=True,
            archived_at=datetime(2025, 12, 25, tzinfo=timezone.utc),
        )

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

    def _check_object_in_results(self, obj, results):
        return str(obj.pk) in [str(result.pk) for result in results]

    def test_archived_guest_is_not_in_results(self):
        results = GuestDuplicateGroup.objects.all()

        self.assertFalse(self._check_object_in_results(self.duplicate_group, results))
