from django.test import TestCase

from ontology.models import SponsorshipCertificationForm
from ontology.tests.factories import SponsorshipCertificationFormFactory
from webapp.constants import UAMS_SEARCH_FIELDS
from webapp.search import perform_search


class SearchUamsTestCase(TestCase):
    def setUp(self):
        self.app1 = SponsorshipCertificationFormFactory(
            given_name="John",
            family_name="Doe",
            identification_number="12345678",
            ltla_name=["York"],
            reference="UAM-1234",
        )
        self.app2 = SponsorshipCertificationFormFactory(
            given_name="Jane",
            family_name="Doe",
            identification_number="87654321",
            ltla_name=["Manchester"],
            reference="UAM-5678",
        )

    def _check_object_in_results(self, obj, results):
        return str(obj.pk) in [result.pk for result in results]

    def test_search_by_full_name(self):
        results = perform_search(
            "John", SponsorshipCertificationForm.objects.all(), UAMS_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.app1, results))
        self.assertFalse(self._check_object_in_results(self.app2, results))

    def test_search_by_ltla_name(self):
        results = perform_search(
            "York", SponsorshipCertificationForm.objects.all(), UAMS_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.app1, results))
        self.assertFalse(self._check_object_in_results(self.app2, results))

    def test_search_no_match_should_return_no_results(self):
        results = perform_search(
            "Nonexistent",
            SponsorshipCertificationForm.objects.all(),
            UAMS_SEARCH_FIELDS,
        )

        self.assertEqual(len(results), 0)

    def test_search_empty_query_should_return_all(self):
        # Empty query
        results = perform_search(
            "", SponsorshipCertificationForm.objects.all(), UAMS_SEARCH_FIELDS
        )

        self.assertEqual(len(results), 2)

    def test_search_accepts_short_params(self):
        results = perform_search(
            "Ja", SponsorshipCertificationForm.objects.all(), UAMS_SEARCH_FIELDS
        )

        self.assertEqual(len(results), 1)

    def test_search_partial_by_partial_value(self):
        # Partial match for "John"
        results = perform_search(
            "Joh", SponsorshipCertificationForm.objects.all(), UAMS_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.app1, results))
        self.assertFalse(self._check_object_in_results(self.app2, results))

    def test_search_by_multiple_keywords(self):
        # Tokenised search
        results = perform_search(
            "Doe,- Jane", SponsorshipCertificationForm.objects.all(), UAMS_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.app1, results))
        self.assertTrue(self._check_object_in_results(self.app2, results))

    def test_search_with_existing_queryset(self):
        queryset = SponsorshipCertificationForm.objects.filter(reference="UAM-1234")
        self.assertEqual(len(queryset), 1)
        results = perform_search("Doe", queryset)

        self.assertTrue(self._check_object_in_results(self.app1, results))
        self.assertFalse(self._check_object_in_results(self.app2, results))
