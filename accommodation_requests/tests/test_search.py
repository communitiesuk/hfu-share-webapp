from django.test import TestCase

from ontology.models import MvAccommodationRequest as AccReq
from ontology.tests.factories import MvAccommodationRequestFactory as AccReqFactory
from webapp.constants import ACCOMMODATION_REQUEST_SEARCH_FIELDS
from webapp.search import perform_search


class AccommodationRequestSearchTestCase(TestCase):
    def setUp(self):
        self.acc_req1 = AccReqFactory(
            title="John Doe acc req",
        )
        self.acc_req2 = AccReqFactory(
            title="Jane Smith acc req",
        )

    def _check_object_in_results(self, obj, results):
        return str(obj.pk) in [result.pk for result in results]

    def test_search_by_title(self):
        results = perform_search(
            "John Doe",
            AccReq.objects.all(),
            ACCOMMODATION_REQUEST_SEARCH_FIELDS,
        )

        self.assertTrue(self._check_object_in_results(self.acc_req1, results))
        self.assertFalse(self._check_object_in_results(self.acc_req2, results))

    def test_search_no_match_should_return_no_results(self):
        results = perform_search(
            "Nonexistent", AccReq.objects.all(), ACCOMMODATION_REQUEST_SEARCH_FIELDS
        )

        self.assertEqual(len(results), 0)

    def test_search_empty_query_should_return_all(self):
        # Empty query
        results = perform_search(
            "", AccReq.objects.all(), ACCOMMODATION_REQUEST_SEARCH_FIELDS
        )

        self.assertEqual(len(results), 2)

    def test_search_accepts_short_params(self):
        results = perform_search(
            "Jo", AccReq.objects.all(), ACCOMMODATION_REQUEST_SEARCH_FIELDS
        )

        self.assertEqual(len(results), 1)

    def test_search_partial_by_partial_value(self):
        # Partial match for "acc"
        results = perform_search(
            "acc", AccReq.objects.all(), ACCOMMODATION_REQUEST_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.acc_req1, results))
        self.assertTrue(self._check_object_in_results(self.acc_req2, results))

    def test_search_by_multiple_keywords(self):
        # Tokenised search
        results = perform_search(
            "Jane,- John", AccReq.objects.all(), ACCOMMODATION_REQUEST_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.acc_req1, results))
        self.assertTrue(self._check_object_in_results(self.acc_req2, results))

    def test_search_with_existing_queryset(self):
        queryset = AccReq.objects.filter(title="John Doe acc req")
        self.assertEqual(len(queryset), 1)
        results = perform_search("Doe", queryset)

        self.assertTrue(self._check_object_in_results(self.acc_req1, results))
        self.assertFalse(self._check_object_in_results(self.acc_req2, results))
