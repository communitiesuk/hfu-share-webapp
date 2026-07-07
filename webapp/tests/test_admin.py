from datetime import datetime, timezone
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from freezegun import freeze_time

from accounts.tests.base import TestSessionTokenMixin
from user_management.tests.base import (
    get_admin_user,
    get_la_user,
    get_user_with_no_access,
)


class AdminStatsTests(TestSessionTokenMixin, TestCase):
    def test_admin_stats_view_inaccessible_to_logged_out_user(self):
        response = self.client.get(reverse("admin:auditlog-stats"))
        self.assertEqual(response.status_code, 404)

    def test_admin_stats_view_inaccessible_to_no_access_user(self):
        user = get_user_with_no_access()
        self.client.force_login(user)

        response = self.client.get(reverse("admin:auditlog-stats"))
        self.assertEqual(response.status_code, 404)

    def test_admin_stats_view_inaccessible_to_la_user(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(reverse("admin:auditlog-stats"))
        self.assertEqual(response.status_code, 404)

    def test_admin_stats_view_inaccessible_to_dev_but_not_staff_user(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(reverse("admin:auditlog-stats"))
        self.assertEqual(response.status_code, 404)

    def test_admin_stats_view_inaccessible_to_staff_but_not_dev_user(self):
        user = get_user_with_no_access()
        user.is_staff = True
        user.save()
        self.client.force_login(user)

        response = self.client.get(reverse("admin:auditlog-stats"))
        self.assertEqual(response.status_code, 403)

    def test_admin_stats_view_visible_to_dev_staff_user(self):
        user = get_admin_user()
        user.is_staff = True
        user.save()

        self.client.force_login(user)
        response = self.client.get(reverse("admin:auditlog-stats"))

        self.assertEqual(response.status_code, 200)

    def test_auditlog_app_index_shows_links(self):
        user = get_admin_user()
        user.is_staff = True
        user.save()
        user.user_permissions.add(
            Permission.objects.get(
                codename="view_logentry", content_type__app_label="auditlog"
            )
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse("admin:app_list", kwargs={"app_label": "auditlog"})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log entries")
        self.assertContains(
            response,
            reverse("admin:auditlog-stats"),
        )

    @patch("webapp.admin.get_user_stats")
    @patch("webapp.admin.generate_monthly_audit_stats")
    def test_admin_stats_view_shows_monthly_stats(
        self, mock_generate_monthly_audit_stats, mock_get_user_stats
    ):
        mock_generate_monthly_audit_stats.return_value = {
            "MvAccommodation": {
                "total_changes": 1,
                "January 2026": 1,
                "February 2026": 0,
                "March 2026": 0,
            },
            "MvAccommodationRequest": {
                "total_changes": 1,
                "January 2026": 0,
                "February 2026": 1,
                "March 2026": 0,
            },
        }
        mock_get_user_stats.return_value = {
            "total_users": 3,
            "users_active_in_last_90_days": 1,
            "new_users_in_last_90_days": 2,
        }

        user = get_admin_user()
        user.is_staff = True
        user.save()

        self.client.force_login(user)

        with freeze_time(datetime(2026, 3, 2, tzinfo=timezone.utc)):
            response = self.client.get(reverse("admin:auditlog-stats"))

        self.assertTemplateUsed(response, "webapp/pages/admin/auditlog_stats.html")
        self.assertEqual(
            list(response.context["month_names"]),
            ["total_changes", "January 2026", "February 2026", "March 2026"],
        )
        self.assertEqual(
            response.context["all_stats"],
            mock_generate_monthly_audit_stats.return_value,
        )
        self.assertEqual(
            response.context["user_stats"],
            mock_get_user_stats.return_value,
        )

        expected_table_header_html = "<thead><tr><th>Model</th><th>total_changes</th><th>January 2026</th><th>February 2026</th><th>March 2026</th></tr></thead>"  # noqa E501
        expected_first_row_html = (
            "<tr><td>MvAccommodation</td><td>1</td><td>1</td><td>0</td><td>0</td></tr>"
        )
        expected_second_row_html = "<tr><td>MvAccommodationRequest</td><td>1</td><td>0</td><td>1</td><td>0</td></tr>"  # noqa E501

        self.assertContains(response, expected_table_header_html, html=True)
        self.assertContains(response, expected_first_row_html, html=True)
        self.assertContains(response, expected_second_row_html, html=True)
        self.assertContains(
            response,
            reverse("admin:app_list", kwargs={"app_label": "auditlog"}),
        )
