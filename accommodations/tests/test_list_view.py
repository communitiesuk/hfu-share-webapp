from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import MvAccommodationFactory, MvUkPostcodeFactory
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class DeduplicationAccommodationListViewTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.accommodation = MvAccommodationFactory(
            full_address="123 Street",
            postcode=MvUkPostcodeFactory(postcode="TEST 123"),
            ltla_name="LTLA",
            utla_name="UTLA",
            is_principal=True,
        )

        self.non_principal_accommodation = MvAccommodationFactory(
            full_address="321 Avenue",
            is_principal=False,
        )

        self.archived_accommodation = MvAccommodationFactory(
            full_address="Archived address",
            is_principal=True,
            is_archived=True,
            archived_at=datetime(2025, 12, 25, tzinfo=timezone.utc),
        )

    def test_renders_accommodation_list_with_correct_layout(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:accommodations",
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Accommodation")
        self.assertContains(response, "Address")
        self.assertContains(response, "Postcode")
        self.assertContains(response, "Lower tier LA")
        self.assertContains(response, "Upper tier LA")

    def test_renders_accommodation_list_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:accommodations",
            )
        )

        self.assertContains(response, self.accommodation.full_address)
        self.assertContains(response, self.accommodation.postcode.postcode)
        self.assertContains(response, self.accommodation.ltla_name)
        self.assertContains(response, self.accommodation.utla_name)

    def test_does_not_render_non_principal_accommodation(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:accommodations",
            )
        )

        self.assertNotContains(response, self.non_principal_accommodation.full_address)

    def test_does_not_render_archived_accommodation(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:accommodations",
            )
        )

        self.assertNotContains(response, self.archived_accommodation.full_address)

    def test_admin_user_can_access_list_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:accommodations",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_la_user_can_access_list_view(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:accommodations",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_da_user_can_access_list_view(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:accommodations",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_mhclg_user_can_access_list_view(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:accommodations",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_service_support_user_can_access_list_view(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:accommodations",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_ukvi_user_can_access_list_view(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:accommodations",
            )
        )

        self.assertEqual(response.status_code, 200)
