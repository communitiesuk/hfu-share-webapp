from django.test import TestCase

from ontology.models import MvAccommodation as Accommodation
from ontology.tests.factories import MvAccommodationFactory as AccommodationFactory
from ontology.tests.factories import MvUkPostcodeFactory as PostCodeFactory
from webapp.constants import ACCOMMODATION_SEARCH_FIELDS
from webapp.search import perform_search


class SearchGuestsTestCase(TestCase):
    def setUp(self):
        self.postcode1 = PostCodeFactory()
        self.postcode2 = PostCodeFactory()
        self.accomm1 = AccommodationFactory(
            full_address="1 Street, City, London", postcode=self.postcode1
        )
        self.accomm2 = AccommodationFactory(
            full_address="2 Road, Town, Wondon", postcode=self.postcode2
        )

    def _check_object_in_results(self, obj, results):
        return str(obj.pk) in [result.pk for result in results]

    def test_search_full_address(self):
        results = perform_search(
            "1 Street", Accommodation.objects.all(), ACCOMMODATION_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.accomm1, results))
        self.assertFalse(self._check_object_in_results(self.accomm2, results))

    def test_search_by_postcode(self):
        results = perform_search(
            self.postcode1.postcode,
            Accommodation.objects.all(),
            ACCOMMODATION_SEARCH_FIELDS,
        )

        self.assertTrue(self._check_object_in_results(self.accomm1, results))

    def test_search_no_match_should_return_no_results(self):
        results = perform_search(
            "Nonexistent", Accommodation.objects.all(), ACCOMMODATION_SEARCH_FIELDS
        )

        self.assertEqual(len(results), 0)

    def test_search_empty_query_should_return_all(self):
        # Empty query
        results = perform_search(
            "", Accommodation.objects.all(), ACCOMMODATION_SEARCH_FIELDS
        )

        self.assertEqual(len(results), len(Accommodation.objects.all()))

    def test_search_accepts_short_params(self):
        results = perform_search(
            "1", Accommodation.objects.all(), ACCOMMODATION_SEARCH_FIELDS
        )

        self.assertEqual(len(results), 1)

    def test_search_partial_by_partial_value(self):
        results = perform_search(
            "ondon", Accommodation.objects.all(), ACCOMMODATION_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.accomm1, results))
        self.assertTrue(self._check_object_in_results(self.accomm2, results))

    def test_search_by_multiple_keywords(self):
        # Tokenised search
        results = perform_search(
            "Street,- Road", Accommodation.objects.all(), ACCOMMODATION_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.accomm1, results))
        self.assertTrue(self._check_object_in_results(self.accomm2, results))

    def test_search_with_existing_queryset(self):
        queryset = Accommodation.objects.filter(postcode=self.postcode1)
        self.assertEqual(len(queryset), 1)
        results = perform_search(self.postcode1.postcode, queryset)

        self.assertTrue(self._check_object_in_results(self.accomm1, results))
        self.assertFalse(self._check_object_in_results(self.accomm2, results))
