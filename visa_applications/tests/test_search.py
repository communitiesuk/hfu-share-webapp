from django.test import TestCase

from ontology.models import VisaApplication
from ontology.tests.factories import VisaApplicationFactory
from webapp.constants import VISA_APPLICATION_SEARCH_FIELDS
from webapp.search import perform_search


class SearchVisaApplicationsTest(TestCase):
    def setUp(self):
        self.app1 = VisaApplicationFactory(
            application_unique_application_number="1313-0000-3216-0635",
            title="John Doe",
            Q97c_sponsor_name="Jane Smith",
            ltla_name="York",
            gwf="GWF88998600",
        )
        self.app2 = VisaApplicationFactory(
            application_unique_application_number="4950-1234-2930-0495",
            title="Alice Johnson",
            Q97c_sponsor_name="Bob Williams",
            ltla_name="London",
            gwf="GWF78290394",
        )
        self.app3 = VisaApplicationFactory(
            application_unique_application_number="1313-0000-0000-1111",
            title="John Doe",
            Q97c_sponsor_name="Jane Smith",
            ltla_name="York",
            gwf="GWF88991313",
        )

    def _check_object_in_results(self, obj, results):
        return str(obj.pk) in [result.pk for result in results]

    def test_search_by_untokenised_field(self):
        results = perform_search(
            "1313-0000-3216-0635",
            VisaApplication.objects.all(),
            VISA_APPLICATION_SEARCH_FIELDS,
        )

        self.assertTrue(self._check_object_in_results(self.app1, results))
        self.assertFalse(self._check_object_in_results(self.app2, results))
        self.assertFalse(self._check_object_in_results(self.app3, results))

    def test_search_by_full_name(self):
        results = perform_search(
            "Jane Smith", VisaApplication.objects.all(), VISA_APPLICATION_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.app1, results))
        self.assertFalse(self._check_object_in_results(self.app2, results))

    def test_search_by_ltla_name(self):
        results = perform_search(
            "York", VisaApplication.objects.all(), VISA_APPLICATION_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.app1, results))
        self.assertFalse(self._check_object_in_results(self.app2, results))

    def test_search_no_match_should_return_no_results(self):
        results = perform_search(
            "Nonexistent", VisaApplication.objects.all(), VISA_APPLICATION_SEARCH_FIELDS
        )

        self.assertEqual(len(results), 0)

    def test_search_empty_query_should_return_all(self):
        # Empty query
        results = perform_search(
            "", VisaApplication.objects.all(), VISA_APPLICATION_SEARCH_FIELDS
        )

        self.assertEqual(len(results), 3)

    def test_search_accepts_short_params(self):
        results = perform_search(
            "Bo", VisaApplication.objects.all(), VISA_APPLICATION_SEARCH_FIELDS
        )

        self.assertEqual(len(results), 1)

    def test_search_partial_by_partial_value(self):
        # Partial match for "John"
        results = perform_search(
            "Joh", VisaApplication.objects.all(), VISA_APPLICATION_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.app1, results))
        self.assertTrue(self._check_object_in_results(self.app2, results))

    def test_search_by_multiple_keywords(self):
        # Tokenised search
        results = perform_search(
            "Jane,- Bob", VisaApplication.objects.all(), VISA_APPLICATION_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.app1, results))
        self.assertTrue(self._check_object_in_results(self.app2, results))

    def test_search_with_existing_queryset(self):
        queryset = VisaApplication.objects.filter(
            application_unique_application_number="1313-0000-3216-0635"
        )
        self.assertEqual(len(queryset), 1)
        results = perform_search("Doe", queryset)

        self.assertTrue(self._check_object_in_results(self.app1, results))
        self.assertFalse(self._check_object_in_results(self.app2, results))

    def test_search_by_gwf(self):
        results = perform_search(
            "GWF88998600", VisaApplication.objects.all(), VISA_APPLICATION_SEARCH_FIELDS
        )
        self.assertTrue(self._check_object_in_results(self.app1, results))
        self.assertFalse(self._check_object_in_results(self.app2, results))

    def test_search_by_application_unique_application_number(self):
        results = perform_search(
            "1313-0000-3216-0635",
            VisaApplication.objects.all(),
            VISA_APPLICATION_SEARCH_FIELDS,
        )
        self.assertTrue(self._check_object_in_results(self.app1, results))
        self.assertFalse(self._check_object_in_results(self.app2, results))
