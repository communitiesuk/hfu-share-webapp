from datetime import datetime, timezone

from django.test import TestCase

from deduplication.models import SponsorDuplicateGroup
from deduplication.tests.factories import SponsorDuplicateGroupFactory
from ontology.tests.factories import MvVolunteerFactory


class SponsorDuplicateGroupTestCase(TestCase):
    def setUp(self):
        self.sponsor_one = MvVolunteerFactory()
        self.sponsor_two = MvVolunteerFactory()

        self.duplicate_group = SponsorDuplicateGroupFactory(
            is_archived=True,
            archived_at=datetime(2025, 12, 25, tzinfo=timezone.utc),
        )

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

    def _check_object_in_results(self, obj, results):
        return str(obj.pk) in [str(result.pk) for result in results]

    def test_archived_sponsor_is_not_in_results(self):
        results = SponsorDuplicateGroup.objects.all()

        self.assertFalse(self._check_object_in_results(self.duplicate_group, results))
