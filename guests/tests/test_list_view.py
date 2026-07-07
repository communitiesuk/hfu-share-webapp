from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import MvPersonFactory
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class DeduplicationGuestListViewTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.guest = MvPersonFactory(
            first_name="test1firstname",
            last_name="test1lastname",
            gender="Female",
            date_of_birth=datetime(1999, 11, 11, tzinfo=timezone.utc),
            passport_id=["XX88888"],
            visa_status="Arrived",
            arrival_date=datetime(2025, 12, 10, tzinfo=timezone.utc),
            latest_arrival_date=datetime(2025, 12, 11, tzinfo=timezone.utc),
            visa_application_date_maximum=datetime(2030, 6, 20, tzinfo=timezone.utc),
            application_number=["4242-4242-4242-4242"],
            is_principal=True,
        )

        self.non_principal_guest = MvPersonFactory(
            first_name="[afirstname",
            last_name="duplicate",
            is_principal=False,
        )

    def test_renders_guest_list_with_correct_layout(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:guests",
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Guests")
        self.assertContains(response, "Name")
        self.assertContains(response, "Sex")
        self.assertContains(response, "Date of birth")
        self.assertContains(response, "Passport number")
        self.assertContains(response, "Visa status")
        self.assertContains(response, "First arrival date")
        self.assertContains(response, "Latest arrival date")
        self.assertContains(response, "Latest visa application date")
        self.assertContains(response, "Unique application number (UAN)")

    def test_renders_guest_list_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:guests",
            )
        )

        self.assertContains(response, self.guest.get_full_name())
        self.assertContains(response, self.guest.gender)
        self.assertContains(response, self.guest.date_of_birth.strftime("%-d %b %Y"))
        self.assertContains(response, self.guest.passport_id[0])
        self.assertContains(response, self.guest.visa_status)
        self.assertContains(response, self.guest.arrival_date.strftime("%-d %b %Y"))
        self.assertContains(
            response, self.guest.latest_arrival_date.strftime("%-d %b %Y")
        )
        self.assertContains(
            response, self.guest.visa_application_date_maximum.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.guest.application_number[0])

    def test_does_not_render_non_principal_guest(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:guests",
            )
        )

        self.assertNotContains(response, self.non_principal_guest.get_full_name())

    def test_admin_user_can_access_list_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:guests",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_la_user_can_access_list_view(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:guests",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_da_user_can_access_list_view(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:guests",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_mhclg_user_can_access_list_view(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:guests",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_service_support_user_can_access_list_view(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:guests",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_ukvi_user_can_access_list_view(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:guests",
            )
        )

        self.assertEqual(response.status_code, 200)
