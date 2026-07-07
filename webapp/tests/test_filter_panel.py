from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from user_management.tests.base import get_admin_user


class FilterPanelIntegrationTest(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = get_admin_user()
        self.client.force_login(self.user)
        self.url = reverse("accommodation-requests:accommodation-requests")

    def assert_panel_open(self, response):
        self.assertContains(response, 'id="filter-container"')
        self.assertIn("display: block", response.content.decode())

    def assert_panel_closed(self, response):
        self.assertContains(response, 'id="filter-container"')
        self.assertIn("display: none", response.content.decode())

    def test_panel_remains_open_after_sorting_without_filters(self):
        """
        Filter panel should remain open after sorting, even if no filters are applied.
        """
        response = self.client.get(self.url + "?show_filters_panel=True")
        self.assert_panel_open(response)
        self.assertIn("show_filters_panel", response.request["QUERY_STRING"])

        response = self.client.get(
            self.url + "?show_filters_panel=True&sort=checks_status"
        )
        self.assert_panel_open(response)
        self.assertIn("show_filters_panel", response.request["QUERY_STRING"])

    def test_panel_toggle_link_opens_and_closes_panel(self):
        """
        Toggle link should add or remove show_filters_panel in the query string.
        """
        response = self.client.get(self.url)
        self.assert_panel_closed(response)

        response = self.client.get(self.url + "?show_filters_panel=True")
        self.assert_panel_open(response)

        response = self.client.get(self.url)
        self.assert_panel_closed(response)
