from django.test import TestCase

from ontology.models import MvVolunteer as Sponsor
from ontology.tests.factories import MvVolunteerFactory as SponsorFactory
from webapp.constants import SPONSORS_SEARCH_FIELDS
from webapp.search import perform_search


class SearchSponsorsTestCase(TestCase):
    def setUp(self):
        self.sponsor1 = SponsorFactory(
            first_name="John",
            last_name="Doe",
            full_name="John Doe",
            email="sponsor1@example.com",
            phone_number=["000"],
        )
        self.sponsor2 = SponsorFactory(
            first_name="Jane",
            last_name="Smith",
            full_name="Jane Smith",
            email="sponsor2@example.com",
            phone_number=["999"],
        )

    def _check_object_in_results(self, obj, results):
        return str(obj.pk) in [result.pk for result in results]

    def test_search_by_phone_number(self):
        results = perform_search("000", Sponsor.objects.all(), SPONSORS_SEARCH_FIELDS)

        self.assertTrue(self._check_object_in_results(self.sponsor1, results))
        self.assertFalse(self._check_object_in_results(self.sponsor2, results))

    def test_search_by_email(self):
        results = perform_search(
            "sponsor1@example.com", Sponsor.objects.all(), SPONSORS_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.sponsor1, results))
        self.assertFalse(self._check_object_in_results(self.sponsor2, results))

    def test_search_by_full_name(self):
        results = perform_search(
            "John Doe", Sponsor.objects.all(), SPONSORS_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.sponsor1, results))
        self.assertFalse(self._check_object_in_results(self.sponsor2, results))

    def test_search_no_match_should_return_no_results(self):
        results = perform_search(
            "Nonexistent", Sponsor.objects.all(), SPONSORS_SEARCH_FIELDS
        )

        self.assertEqual(len(results), 0)

    def test_search_empty_query_should_return_all(self):
        # Empty query
        results = perform_search("", Sponsor.objects.all(), SPONSORS_SEARCH_FIELDS)

        self.assertEqual(len(results), len(Sponsor.objects.all()))

    def test_search_accepts_short_params(self):
        results = perform_search("r1", Sponsor.objects.all(), SPONSORS_SEARCH_FIELDS)

        self.assertEqual(len(results), 1)

    def test_search_partial_by_partial_value(self):
        # Partial match for "sponsor" (email addresses are sponsor1 and sponsor 2)
        results = perform_search(
            "sponsor", Sponsor.objects.all(), SPONSORS_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.sponsor1, results))
        self.assertTrue(self._check_object_in_results(self.sponsor2, results))

    def test_search_by_multiple_keywords(self):
        # Tokenised search
        results = perform_search(
            "Jane,- John", Sponsor.objects.all(), SPONSORS_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.sponsor1, results))
        self.assertTrue(self._check_object_in_results(self.sponsor2, results))

    def test_search_with_existing_queryset(self):
        queryset = Sponsor.objects.filter(first_name="John")
        self.assertEqual(len(queryset), 1)
        results = perform_search("Doe", queryset)

        self.assertTrue(self._check_object_in_results(self.sponsor1, results))
        self.assertFalse(self._check_object_in_results(self.sponsor2, results))
