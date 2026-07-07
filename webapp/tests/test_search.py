from django.test import TestCase

from webapp.search import perform_search, query_to_tokens


class SearchBaseTests(TestCase):
    def test_query_to_tokens(self):
        results = query_to_tokens("Jane,- Bob")

        self.assertListEqual(["jane", "bob"], results)

    def test_search_with_no_queryset(self):
        with self.assertRaises(ValueError):
            perform_search("Doe")
