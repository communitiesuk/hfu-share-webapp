from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from user_management.tests.base import get_la_user, get_user_with_no_access
from webapp.context_processors import available_links, get_available_links


class AvailableLinksContextProcessorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def build_request(self, user=None):
        request = self.factory.get("/")
        if user is not None:
            request.user = user
        return request

    def test_anonymous_user_has_no_links(self):
        request = self.build_request(AnonymousUser())
        self.assertEqual(available_links(request), {"available_links": {}})

    def test_request_without_a_user_has_no_links(self):
        request = self.build_request()
        self.assertEqual(get_available_links(request), {})

    def test_user_with_no_groups_has_no_links(self):
        request = self.build_request(get_user_with_no_access())
        self.assertEqual(get_available_links(request), {})

    def test_la_user_gets_role_based_links(self):
        request = self.build_request(get_la_user())
        links = get_available_links(request)
        self.assertTrue(links["guests"])
        self.assertTrue(links["accommodation"])
        self.assertTrue(links["visa_applications"])
        self.assertFalse(links["manage_permissions"])
        self.assertFalse(links["escalated_checks"])

    def test_links_are_computed_once_per_request(self):
        request = self.build_request(get_la_user())
        with self.assertNumQueries(1):
            first = get_available_links(request)
            second = get_available_links(request)
        self.assertIs(first, second)
