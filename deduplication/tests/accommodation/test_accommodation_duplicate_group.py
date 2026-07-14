from datetime import datetime, timezone

from django.test import TestCase

from deduplication.models import AccommodationDuplicateGroup
from deduplication.tests.factories import AccommodationDuplicateGroupFactory
from ontology.tests.factories import MvAccommodationFactory


class AccommodationDuplicateGroupTestCase(TestCase):
    def setUp(self):
        self.accommodation_one = MvAccommodationFactory()
        self.accommodation_two = MvAccommodationFactory()

        self.duplicate_group = AccommodationDuplicateGroupFactory(
            is_archived=True,
            archived_at=datetime(2025, 12, 25, tzinfo=timezone.utc),
        )

        self.duplicate_group.accommodations.add(self.accommodation_one)
        self.duplicate_group.accommodations.add(self.accommodation_two)
        self.duplicate_group.save()

    def test_archived_accommodation_is_not_in_results(self):
        results = AccommodationDuplicateGroup.objects.all()

        self.assertNotIn(self.duplicate_group, results)
