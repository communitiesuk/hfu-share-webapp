from django.test import TestCase

from ontology.models import ReassignmentRequest
from ontology.tests.factories import MvPersonFactory, ReassignmentRequestFactory
from webapp.constants import REASSIGNMENT_REQUEST_SEARCH_FIELDS
from webapp.search import perform_search


class SearchReassignmentRequestsTestCase(TestCase):
    def _check_object_in_results(self, obj, results):
        return str(obj.pk) in [str(result.pk) for result in results]

    def setUp(self):
        # Reassignment request with a single guest
        self.rr_single_guest = ReassignmentRequestFactory()
        self.guest_alice = MvPersonFactory(
            first_name="Alice",
            last_name="Smith",
        )
        self.rr_single_guest.guests.set([self.guest_alice])

        # Reassignment request with multiple guests
        self.rr_multiple_guests = ReassignmentRequestFactory()
        self.guest_john = MvPersonFactory(
            first_name="John",
            last_name="Doe",
        )
        self.guest_jane = MvPersonFactory(
            first_name="Jane",
            last_name="Doe",
        )
        self.rr_multiple_guests.guests.set([self.guest_john, self.guest_jane])

        # Reassignment request with no guests (should not match name search)
        self.rr_no_guests = ReassignmentRequestFactory()

    def test_search_by_guest_full_name_single_guest(self):
        results = perform_search(
            "Alice Smith",
            ReassignmentRequest.objects,
            REASSIGNMENT_REQUEST_SEARCH_FIELDS,
        )

        self.assertTrue(self._check_object_in_results(self.rr_single_guest, results))
        self.assertFalse(
            self._check_object_in_results(self.rr_multiple_guests, results)
        )
        self.assertFalse(self._check_object_in_results(self.rr_no_guests, results))

    def test_search_by_guest_full_name_multiple_guests_first_guest(self):
        results = perform_search(
            "John Doe",
            ReassignmentRequest.objects,
            REASSIGNMENT_REQUEST_SEARCH_FIELDS,
        )

        self.assertTrue(self._check_object_in_results(self.rr_multiple_guests, results))
        self.assertFalse(self._check_object_in_results(self.rr_single_guest, results))

    def test_search_by_guest_full_name_multiple_guests_second_guest(self):
        results = perform_search(
            "Jane Doe",
            ReassignmentRequest.objects,
            REASSIGNMENT_REQUEST_SEARCH_FIELDS,
        )

        self.assertTrue(self._check_object_in_results(self.rr_multiple_guests, results))
        self.assertFalse(self._check_object_in_results(self.rr_single_guest, results))

    def test_search_by_partial_first_name_single_guest(self):
        results = perform_search(
            "Alice",
            ReassignmentRequest.objects,
            REASSIGNMENT_REQUEST_SEARCH_FIELDS,
        )

        self.assertTrue(self._check_object_in_results(self.rr_single_guest, results))
        self.assertFalse(
            self._check_object_in_results(self.rr_multiple_guests, results)
        )

    def test_search_by_partial_first_name_multiple_guests(self):
        results = perform_search(
            "John",
            ReassignmentRequest.objects,
            REASSIGNMENT_REQUEST_SEARCH_FIELDS,
        )

        self.assertTrue(self._check_object_in_results(self.rr_multiple_guests, results))

        results_jane = perform_search(
            "Jane",
            ReassignmentRequest.objects,
            REASSIGNMENT_REQUEST_SEARCH_FIELDS,
        )
        self.assertTrue(
            self._check_object_in_results(self.rr_multiple_guests, results_jane)
        )

    def test_search_no_match_should_return_no_results(self):
        results = perform_search(
            "Nonexistent",
            ReassignmentRequest.objects,
            REASSIGNMENT_REQUEST_SEARCH_FIELDS,
        )

        self.assertEqual(len(results), 0)
