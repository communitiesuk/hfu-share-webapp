from django.test import TestCase

from accommodations.views import AccommodationFilter
from ontology.models import MvAccommodation
from ontology.tests.factories import MvAccommodationFactory


class AccommodationFilterIncludeDuplicatesTestCase(TestCase):
    def setUp(self):
        self.record_1 = MvAccommodationFactory(is_principal=True)
        self.record_2 = MvAccommodationFactory(is_principal=False)
        self.record_3 = MvAccommodationFactory(is_principal=None)

    def test_filter_duplicates(self):
        filter_set = AccommodationFilter(
            queryset=MvAccommodation.objects.all(),
            data={},
        )

        results = filter_set.qs
        accommodation_ids = results.values_list("id", flat=True)

        self.assertIn(self.record_1.id, accommodation_ids)
        self.assertNotIn(self.record_2.id, accommodation_ids)
        self.assertNotIn(self.record_3.id, accommodation_ids)

        filter_set = AccommodationFilter(
            queryset=MvAccommodation.objects.all(),
            data={"include_duplicates": "Yes"},
        )

        results = filter_set.qs
        accommodation_ids = results.values_list("id", flat=True)

        self.assertIn(self.record_1.id, accommodation_ids)
        self.assertIn(self.record_2.id, accommodation_ids)
        self.assertIn(self.record_3.id, accommodation_ids)
