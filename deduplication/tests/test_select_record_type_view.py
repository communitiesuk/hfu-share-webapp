import http.client

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class DeduplicationSponsorSelectedViewTests(TestSessionTokenMixin, TestCase):
    def test_dev_user_can_access_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertEqual(response.status_code, http.client.OK)

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=False)
    def test_flag_off_dev_user_can_still_access_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertEqual(response.status_code, http.client.OK)

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=True)
    def test_flag_on_da_user_can_access_view(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertEqual(response.status_code, http.client.OK)

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=False)
    def test_flag_off_da_user_cannot_access_view(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=True)
    def test_flag_on_la_user_can_access_view(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertEqual(response.status_code, http.client.OK)

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=False)
    def test_flag_off_la_user_cannot_access_view(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=True)
    def test_flag_on_mhclg_user_can_access_view(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertEqual(response.status_code, http.client.OK)

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=False)
    def test_flag_off_mhclg_user_cannot_access_view(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_ukvi_user_cannot_access_view(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_renders_review_list_with_correct_layout(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))

        self.assertContains(response, "Fix duplicate records")
        self.assertContains(response, "Select the type of record you want to fix")

        self.assertContains(response, "Accommodation")
        self.assertContains(response, "Guests")
        self.assertContains(response, "Sponsors and hosts")

        self.assertContains(
            response,
            "Continue to find records using filter and search, and deduplicate them.",
        )

        self.assertContains(
            response,
            '<button class="govuk-button"type="submit">Continue</button>',
            html=True,
        )

        self.assertContains(
            response,
            '<a class="govuk-button govuk-button--secondary" '
            'href="/landing-page">Cancel</a>',
            html=True,
        )

    def test_dev_user_can_see_guests_option(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertContains(response, 'value="Guests"')

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=True)
    def test_la_user_cannot_see_guests_option(self):
        self.client.force_login(get_la_user())
        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertNotContains(response, 'value="Guests"')

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=True)
    def test_la_user_can_see_accommodation_and_sponsors_options(self):
        self.client.force_login(get_la_user())
        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertContains(response, "Accommodation")
        self.assertContains(response, "Sponsors and hosts")

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=True)
    def test_da_user_can_see_accommodation_and_sponsors_options(self):
        self.client.force_login(get_da_user())
        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertContains(response, "Accommodation")
        self.assertContains(response, "Sponsors and hosts")

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=True)
    def test_mhclg_user_can_see_accommodation_and_sponsors_options(self):
        self.client.force_login(get_mhclg_user())
        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertContains(response, "Accommodation")
        self.assertContains(response, "Sponsors and hosts")

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=True)
    def test_service_support_user_can_see_accommodation_and_sponsors_options(self):
        self.client.force_login(get_service_support_user())
        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertContains(response, "Accommodation")
        self.assertContains(response, "Sponsors and hosts")
