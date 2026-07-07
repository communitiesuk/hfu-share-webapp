from django.test import TestCase
from django.urls import reverse
from freezegun import freeze_time

from accounts.tests.base import TestSessionTokenMixin
from downloads.forms import DownloadType
from user_management.tests.base import get_admin_user, get_da_user, get_la_user


class DownloadsViewGeneralTestCase(TestSessionTokenMixin, TestCase):
    def test_download_view_loads_correctly_for_la_user(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(reverse("downloads:download-page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "All data")
        self.assertContains(response, "Visa applications")
        self.assertContains(response, "Guests")
        self.assertContains(response, "Sponsors and hosts")
        self.assertContains(response, "Accommodation")
        self.assertContains(response, "Applications to sponsor a child")

    def test_download_view_loads_correctly_for_da_user(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(reverse("downloads:download-page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "All data")
        self.assertContains(response, "Visa applications")
        self.assertContains(response, "Guests")
        self.assertContains(response, "Sponsors and hosts")
        self.assertContains(response, "Accommodation")
        self.assertContains(response, "Applications to sponsor a child")

    def test_download_view_loads_correctly_for_admin_user(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(reverse("downloads:download-page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "All data")
        self.assertContains(response, "Visa applications")
        self.assertContains(response, "Guests")
        self.assertContains(response, "Sponsors and hosts")
        self.assertContains(response, "Accommodation")
        self.assertContains(response, "Applications to sponsor a child")

    def test_download_view_post_invalid_data(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": ""},
        )

        self.assertContains(response, "govuk-error-summary")
        self.assertContains(response, "govuk-error-message")

    @freeze_time("2024-07-01 12:00:00")
    def test_timestamp_in_bst_summer(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.GUESTS},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("24-07-01_13-00", response["Content-Disposition"])

    @freeze_time("2024-01-01 12:00:00")
    def test_timestamp_in_gmt_winter(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.GUESTS},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("24-01-01_12-00", response["Content-Disposition"])
