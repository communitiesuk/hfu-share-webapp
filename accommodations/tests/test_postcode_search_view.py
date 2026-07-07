import http.client
import json

from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.base import UamsBaseTestCase
from ontology.tests.factories import MvUkPostcodeFactory
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class PostcodeSearchViewTests(TestSessionTokenMixin, UamsBaseTestCase):
    def setUp(self):
        super().setUp()

        self.postcode_ltla_one_a = MvUkPostcodeFactory(
            postcode="SW1A1AA",
            postcode_formatted="SW1A 1AA",
            ltla_name=self.ltla_one_a_name,
        )

        self.postcode_ltla_one_b = MvUkPostcodeFactory(
            postcode="SW1A2BB",
            postcode_formatted="SW1A 2BB",
            ltla_name=self.ltla_one_b_name,
        )

        self.postcode_ltla_two_a = MvUkPostcodeFactory(
            postcode="SW1A3CC",
            postcode_formatted="SW1A 3CC",
            ltla_name=self.ltla_two_a_name,
        )

    def test_dev_user_is_granted_access(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse("accommodations:postcode-search") + "?q=SW1A"
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_user_without_access_is_denied(self):
        user = self.ltla_no_group_user
        self.client.force_login(user)

        response = self.client.get(
            reverse("accommodations:postcode-search") + "?q=SW1A"
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_la_user_is_granted_access(self):
        user = self.ltla_one_a_user
        self.client.force_login(user)

        response = self.client.get(
            reverse("accommodations:postcode-search") + "?q=SW1A"
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_granted_access(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse("accommodations:postcode-search") + "?q=SW1A"
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_mhclg_user_is_granted_access(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse("accommodations:postcode-search") + "?q=SW1A"
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_ukvi_user_is_granted_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse("accommodations:postcode-search") + "?q=SW1A"
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_service_support_user_is_granted_access(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse("accommodations:postcode-search") + "?q=SW1A"
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_valid_query_returns_json_response(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse("accommodations:postcode-search") + "?q=SW1A"
        )

        self.assertEqual(response["Content-Type"], "application/json")

        data = json.loads(response.content)
        self.assertIn("results", data)

    def test_empty_query_returns_empty_results(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(reverse("accommodations:postcode-search"))

        data = json.loads(response.content)
        results = data.get("results", [])

        self.assertEqual(results, [])

    def test_short_query_returns_empty_results(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(reverse("accommodations:postcode-search") + "?q=S")

        data = json.loads(response.content)
        results = data.get("results", [])

        self.assertEqual(results, [])

    def test_no_matching_postcodes_returns_empty_results(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse("accommodations:postcode-search") + "?q=NONEXISTENT"
        )

        data = json.loads(response.content)
        results = data.get("results", [])

        self.assertEqual(results, [])

    def test_admin_user_sees_all_postcodes(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse("accommodations:postcode-search") + "?q=SW1A"
        )

        data = json.loads(response.content)
        results = data.get("results", [])

        self.assertIn("SW1A 1AA", results)
        self.assertIn("SW1A 2BB", results)
        self.assertIn("SW1A 3CC", results)

    def test_ltla_one_a_user_sees_correct_postcodes(self):
        user = self.ltla_one_a_user
        self.client.force_login(user)

        response = self.client.get(
            reverse("accommodations:postcode-search") + "?q=SW1A"
        )

        data = json.loads(response.content)
        results = data.get("results", [])

        self.assertIn("SW1A 1AA", results)
        self.assertNotIn("SW1A 2BB", results)
        self.assertNotIn("SW1A 3CC", results)

    def test_ltla_one_b_user_sees_correct_postcodes_case_insensitive(self):
        user = self.ltla_one_b_user
        self.client.force_login(user)

        response = self.client.get(
            reverse("accommodations:postcode-search") + "?q=sw1a"
        )

        data = json.loads(response.content)
        results = data.get("results", [])

        self.assertNotIn("SW1A 1AA", results)
        self.assertIn("SW1A 2BB", results)
        self.assertNotIn("SW1A 3CC", results)

    def test_admin_postcodes_case_search_without_spaces(self):
        user = self.ltla_user_dev
        self.client.force_login(user)

        response = self.client.get(
            reverse("accommodations:postcode-search") + "?q=SW1A1"
        )

        data = json.loads(response.content)
        results = data.get("results", [])

        self.assertEqual(1, len(results))
        self.assertIn("SW1A 1AA", results)
        self.assertNotIn("SW1A 2BB", results)
        self.assertNotIn("SW1A 3CC", results)

    def test_admin_postcodes_case_search_with_spaces(self):
        user = self.ltla_user_dev
        self.client.force_login(user)

        response = self.client.get(
            reverse("accommodations:postcode-search") + "?q=SW1A 1"
        )

        data = json.loads(response.content)
        results = data.get("results", [])

        self.assertEqual(1, len(results))
        self.assertIn("SW1A 1AA", results)
        self.assertNotIn("SW1A 2BB", results)
        self.assertNotIn("SW1A 3CC", results)
