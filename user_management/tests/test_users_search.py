from django.test import TestCase

from accounts.models import User
from accounts.tests.factories import UserFactory
from webapp.constants import USERS_SEARCH_FIELDS
from webapp.search import perform_search


class SearchUsersTestCase(TestCase):
    def setUp(self):
        self.user1 = UserFactory(
            username="user1",
            first_name="John",
            last_name="Doe",
            email="user1@example.com",
        )
        self.user2 = UserFactory(
            username="user2",
            first_name="Jane",
            last_name="Smith",
            email="user2@example.com",
        )

    def _check_object_in_results(self, obj, results):
        return obj.pk in [result.pk for result in results]

    def test_search_by_email(self):
        results = perform_search(
            "user1@example.com", User.objects.all(), USERS_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.user1, results))
        self.assertFalse(self._check_object_in_results(self.user2, results))

    def test_search_by_full_name(self):
        results = perform_search("John Doe", User.objects.all(), USERS_SEARCH_FIELDS)

        self.assertTrue(self._check_object_in_results(self.user1, results))
        self.assertFalse(self._check_object_in_results(self.user2, results))

    def test_search_no_match_should_return_no_results(self):
        results = perform_search("Nonexistent", User.objects.all(), USERS_SEARCH_FIELDS)

        self.assertEqual(len(results), 0)

    def test_search_empty_query_should_return_all(self):
        # Empty query
        results = perform_search("", User.objects.all(), USERS_SEARCH_FIELDS)

        self.assertEqual(len(results), 2)

    def test_search_accepts_short_params(self):
        results = perform_search("1", User.objects.all(), USERS_SEARCH_FIELDS)

        self.assertEqual(len(results), 1)

    def test_search_partial_by_partial_value(self):
        # Partial match for "user" (email addresses are user1 and user 2)
        results = perform_search("user", User.objects.all(), USERS_SEARCH_FIELDS)

        self.assertTrue(self._check_object_in_results(self.user1, results))
        self.assertTrue(self._check_object_in_results(self.user2, results))

    def test_search_by_multiple_keywords(self):
        # Tokenised search
        results = perform_search("Jane,- John", User.objects.all(), USERS_SEARCH_FIELDS)

        self.assertTrue(self._check_object_in_results(self.user1, results))
        self.assertTrue(self._check_object_in_results(self.user2, results))

    def test_search_with_existing_queryset(self):
        queryset = User.objects.filter(first_name="John")
        self.assertEqual(len(queryset), 1)
        results = perform_search("Doe", queryset)

        self.assertTrue(self._check_object_in_results(self.user1, results))
        self.assertFalse(self._check_object_in_results(self.user2, results))
