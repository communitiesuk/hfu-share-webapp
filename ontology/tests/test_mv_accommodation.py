from ontology.tests.factories import MvAccommodationFactory
from test_utils.base import BaseTestCase


class MvAccommodationTestCase(BaseTestCase):
    def test_mv_accommodation_factory_does_not_create_archived_record(self):
        sponsor = MvAccommodationFactory()

        self.assertFalse(sponsor.is_archived)
        self.assertIsNone(sponsor.archived_at)
