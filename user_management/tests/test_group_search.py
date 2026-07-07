from django.test import TestCase

from accounts.models.GroupProxy import GroupProxy
from accounts.tests.factories import GroupFactory
from webapp.constants import GROUP_SEARCH_FIELDS
from webapp.search import perform_search


class SearchAccessRequestsTestCase(TestCase):
    def setUp(self):
        self.group1 = GroupFactory(
            name="bolton", groupinfo__description="ltla group for bolton"
        )
        self.group2 = GroupFactory(
            name="manchester", groupinfo__description="utla group for manchester"
        )

    def _check_object_in_results(self, obj, results):
        return str(obj.pk) in [str(result.pk) for result in results]

    def test_search_groups_name(self):
        results = perform_search(
            "bolton", GroupProxy.objects.all(), GROUP_SEARCH_FIELDS
        )

        self.assertTrue(self._check_object_in_results(self.group1, results))
        self.assertFalse(self._check_object_in_results(self.group2, results))

    def test_search_groups_description(self):
        results = perform_search("utla", GroupProxy.objects.all(), GROUP_SEARCH_FIELDS)

        self.assertFalse(self._check_object_in_results(self.group1, results))
        self.assertTrue(self._check_object_in_results(self.group2, results))
