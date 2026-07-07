from django.test import TestCase

from accounts.models import AccessRequest
from accounts.tests.factories import AccessRequestFactory
from webapp.constants import ACCESS_REQUEST_SEARCH_FIELDS
from webapp.search import perform_search


class SearchAccessRequestsTestCase(TestCase):
    def setUp(self):
        self.access_request1 = AccessRequestFactory(requester__first_name="Jennifer")
        self.access_request2 = AccessRequestFactory(requester__first_name="Emma")

    def _check_object_in_results(self, obj, results):
        return str(obj.pk) in [str(result.pk) for result in results]

    def test_search_access_requests(self):
        results = perform_search(
            "Jenn", AccessRequest.objects.all(), ACCESS_REQUEST_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.access_request1, results))
        self.assertFalse(self._check_object_in_results(self.access_request2, results))
