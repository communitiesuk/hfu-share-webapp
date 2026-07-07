from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from accounts.tests.factories import UserFactory
from hfurb_scripts.warn_inactive_users import (
    WARNING_DAYS,
    get_users_for_warning_email,
    warn_inactive_users,
)


@freeze_time("2026-02-25 12:00:00")
class TestGetUsersToWarn(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.warning_date = self.now - timedelta(days=WARNING_DAYS)
        self.before_warning_date = self.now - timedelta(days=WARNING_DAYS + 1)
        self.after_warning_date = self.now - timedelta(days=WARNING_DAYS - 1)

    def test_includes_user_when_last_login_exactly_on_warning_date(self):
        user = UserFactory()
        user.last_login = self.warning_date
        user.save(update_fields=["last_login"])

        result = list(get_users_for_warning_email())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], user)

    def test_includes_user_when_last_login_over_warning_days_ago(self):
        user = UserFactory()
        user.last_login = self.before_warning_date
        user.save(update_fields=["last_login"])

        result = list(get_users_for_warning_email())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], user)

    def test_includes_user_when_last_login_null_and_joined_warning_days_ago(
        self,
    ):
        user = UserFactory()
        user.last_login = None
        user.date_joined = self.warning_date
        user.save(update_fields=["last_login", "date_joined"])

        result = list(get_users_for_warning_email())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], user)

    def test_includes_user_when_last_login_null_and_joined_over_warning_days_ago(self):
        user = UserFactory()
        user.last_login = None
        user.date_joined = self.before_warning_date
        user.save(update_fields=["last_login", "date_joined"])

        result = list(get_users_for_warning_email())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], user)

    def test_excludes_user_when_last_login_after_warning_date(self):
        user = UserFactory()
        user.last_login = self.after_warning_date
        user.save(update_fields=["last_login"])

        result = list(get_users_for_warning_email())

        self.assertEqual(len(result), 0)

    def test_excludes_user_when_last_login_null_and_joined_after_warning_date(self):
        user = UserFactory()
        user.last_login = None
        user.date_joined = self.after_warning_date
        user.save(update_fields=["last_login", "date_joined"])

        result = list(get_users_for_warning_email())

        self.assertEqual(len(result), 0)

    def test_excludes_inactive_user_from_before_warning_date(self):
        user = UserFactory(is_active=False)
        user.last_login = self.before_warning_date
        user.save(update_fields=["last_login"])

        result = list(get_users_for_warning_email())

        self.assertEqual(len(result), 0)

    def test_excludes_inactive_superuser_from_before_warning_date(self):
        user = UserFactory(is_superuser=True)
        user.last_login = self.before_warning_date
        user.save(update_fields=["last_login"])

        result = list(get_users_for_warning_email())

        self.assertEqual(len(result), 0)

    def test_excludes_inactive_staff_user_from_before_warning_date(self):
        user = UserFactory(is_staff=True)
        user.last_login = self.before_warning_date
        user.save(update_fields=["last_login"])

        result = list(get_users_for_warning_email())

        self.assertEqual(len(result), 0)


@freeze_time("2026-02-25 12:00:00")
class TestWarnInactiveUsers(TestCase):
    @patch("hfurb_scripts.warn_inactive_users.send_email")
    def test_dry_run_does_not_suspend_users(self, mock_send_email):
        warning_date = timezone.now() - timedelta(days=WARNING_DAYS)

        # Create user with last_login exactly 90 days ago
        user = UserFactory()
        user.last_login = warning_date
        user.save(update_fields=["last_login"])

        warn_inactive_users(dry_run=True)

        user.refresh_from_db()

        self.assertTrue(user.is_active)
        self.assertEqual(mock_send_email.call_count, 0)

    @patch("hfurb_scripts.warn_inactive_users.send_email")
    def test_dry_run_false_sends_warning_email_at_60_days(self, mock_send_email):
        warning_date = timezone.now() - timedelta(days=WARNING_DAYS)

        # Create user with last_login exactly 60 days ago
        user = UserFactory()
        user.last_login = warning_date
        user.save(update_fields=["last_login"])

        warn_inactive_users(dry_run=False)

        user.refresh_from_db()

        self.assertTrue(user.is_active)
        self.assertEqual(mock_send_email.call_count, 1)
