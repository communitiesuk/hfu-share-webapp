from django.test import TestCase

from ontology.tests.factories import MvAccommodationFactory


class MvAccommodationTestCase(TestCase):
    def test_mv_accommodation_factory_does_not_create_archived_record(self):
        sponsor = MvAccommodationFactory()

        self.assertFalse(sponsor.is_archived)
        self.assertIsNone(sponsor.archived_at)
