from django.test import TestCase

from ontology.models import MvPerson as Guest
from ontology.tests.factories import MvPersonFactory as GuestFactory
from webapp.constants import GUEST_SEARCH_FIELDS
from webapp.search import perform_search


class SearchGuestsTestCase(TestCase):
    def setUp(self):
        self.guest1 = GuestFactory(
            first_name="John",
            last_name="Doe",
            email=["guest1@example.com"],
            passport_id=["ID123"],
            application_number=["AN123"],
        )
        self.guest2 = GuestFactory(
            first_name="Jane",
            last_name="Smith",
            email=["guest2@example.com"],
            passport_id=["ID124"],
            application_number=["AN124"],
        )

    def _check_object_in_results(self, obj, results):
        return str(obj.pk) in [result.pk for result in results]

    def test_search_by_passport_id(self):
        results = perform_search("ID123", Guest.objects.all(), GUEST_SEARCH_FIELDS)

        self.assertTrue(self._check_object_in_results(self.guest1, results))
        self.assertFalse(self._check_object_in_results(self.guest2, results))

    def test_search_by_email(self):
        results = perform_search(
            "guest1@example.com", Guest.objects.all(), GUEST_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.guest1, results))
        self.assertFalse(self._check_object_in_results(self.guest2, results))

    def test_search_by_full_name(self):
        results = perform_search("John Doe", Guest.objects.all(), GUEST_SEARCH_FIELDS)

        self.assertTrue(self._check_object_in_results(self.guest1, results))
        self.assertFalse(self._check_object_in_results(self.guest2, results))

    def test_search_by_application_number(self):
        results = perform_search("AN123", Guest.objects.all(), GUEST_SEARCH_FIELDS)

        self.assertTrue(self._check_object_in_results(self.guest1, results))
        self.assertFalse(self._check_object_in_results(self.guest2, results))

    def test_search_no_match_should_return_no_results(self):
        results = perform_search(
            "Nonexistent", Guest.objects.all(), GUEST_SEARCH_FIELDS
        )

        self.assertEqual(len(results), 0)

    def test_search_empty_query_should_return_all(self):
        # Empty query
        results = perform_search("", Guest.objects.all(), GUEST_SEARCH_FIELDS)

        self.assertEqual(len(results), 2)

    def test_search_accepts_short_params(self):
        results = perform_search("Jo", Guest.objects.all(), GUEST_SEARCH_FIELDS)

        self.assertEqual(len(results), 1)

    def test_search_partial_by_partial_value(self):
        # Partial match for "guest" (email addresses are guest1 and guest 2)
        results = perform_search("guest", Guest.objects.all(), GUEST_SEARCH_FIELDS)

        self.assertTrue(self._check_object_in_results(self.guest1, results))
        self.assertTrue(self._check_object_in_results(self.guest2, results))

    def test_search_by_multiple_keywords(self):
        # Tokenised search
        results = perform_search(
            "Jane,- John", Guest.objects.all(), GUEST_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.guest1, results))
        self.assertTrue(self._check_object_in_results(self.guest2, results))

    def test_search_with_existing_queryset(self):
        queryset = Guest.objects.filter(first_name="John")
        self.assertEqual(len(queryset), 1)
        results = perform_search("Doe", queryset)

        self.assertTrue(self._check_object_in_results(self.guest1, results))
        self.assertFalse(self._check_object_in_results(self.guest2, results))

    def test_search_with_exact_match(self):
        guest3 = GuestFactory(
            first_name="Joe",
            last_name="Smith",
            email=["guest4@example.com"],
            passport_id=["ID125"],
            application_number=["AN125"],
        )

        # Tokenised search
        results = perform_search(
            '"Jane Smith"', Guest.objects.all(), GUEST_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.guest2, results))
        self.assertFalse(self._check_object_in_results(guest3, results))
