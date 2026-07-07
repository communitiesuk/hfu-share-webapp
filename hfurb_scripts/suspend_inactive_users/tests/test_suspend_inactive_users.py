from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from accounts.tests.factories import GroupFactory, UserFactory
from hfurb_scripts.suspend_inactive_users import (
    get_users_for_warning_email,
    get_users_to_suspend,
    suspend_inactive_users,
)
from webapp.constants import (
    INACTIVE_ACCOUNT_SUSPEND_DAYS,
    INACTIVE_ACCOUNT_WARNING_DAYS,
)


@freeze_time("2026-02-25 12:00:00")
class TestGetUsersForWarningEmail(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.warning_date = self.now - timedelta(days=INACTIVE_ACCOUNT_WARNING_DAYS)
        self.before_warning_date = self.now - timedelta(
            days=INACTIVE_ACCOUNT_WARNING_DAYS + 1
        )
        self.after_warning_date = self.now - timedelta(
            days=INACTIVE_ACCOUNT_WARNING_DAYS - 1
        )

    def test_includes_user_when_last_login_on_warning_date(self):
        user = UserFactory()
        user.last_login = self.warning_date
        user.save(update_fields=["last_login"])

        result = list(get_users_for_warning_email())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], user)

    def test_includes_user_when_last_login_null_and_date_joined_on_warning_date(self):
        user = UserFactory()
        user.last_login = None
        user.date_joined = self.warning_date
        user.save(update_fields=["last_login", "date_joined"])

        result = list(get_users_for_warning_email())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], user)

    def test_includes_user_when_last_login_before_warning_date(self):
        user = UserFactory()
        user.last_login = self.before_warning_date
        user.save(update_fields=["last_login"])

        result = list(get_users_for_warning_email())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], user)

    def test_includes_user_when_last_login_null_and_joined_before_warning_date(self):
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

    def test_excludes_superuser_last_login_on_warning_date(self):
        user = UserFactory(is_superuser=True)
        user.last_login = self.warning_date
        user.save(update_fields=["last_login"])

        result = list(get_users_for_warning_email())

        self.assertEqual(len(result), 0)

    def test_excludes_staff_user_last_login_on_warning_date(self):
        user = UserFactory(is_staff=True)
        user.last_login = self.warning_date
        user.save(update_fields=["last_login"])

        result = list(get_users_for_warning_email())

        self.assertEqual(len(result), 0)


@freeze_time("2026-02-25 12:00:00")
class TestGetUsersToSuspend(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.suspend_date = self.now - timedelta(days=INACTIVE_ACCOUNT_SUSPEND_DAYS)
        self.before_suspend_date = self.now - timedelta(
            days=INACTIVE_ACCOUNT_SUSPEND_DAYS + 1
        )
        self.after_suspend_date = self.now - timedelta(
            days=INACTIVE_ACCOUNT_SUSPEND_DAYS - 1
        )

    def test_includes_user_when_last_login_on_suspend_date(self):
        user = UserFactory()
        user.last_login = self.suspend_date
        user.save(update_fields=["last_login"])

        result = list(get_users_to_suspend())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], user)

    def test_includes_user_when_last_login_before_suspend_date(self):
        user = UserFactory()
        user.last_login = self.before_suspend_date
        user.save(update_fields=["last_login"])

        result = list(get_users_to_suspend())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], user)

    def test_includes_user_when_last_login_null_and_date_joined_on_suspend_date(
        self,
    ):
        user = UserFactory()
        user.last_login = None
        user.date_joined = self.suspend_date
        user.save(update_fields=["last_login", "date_joined"])

        result = list(get_users_to_suspend())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], user)

    def test_includes_user_when_last_login_null_and_date_joined_before_suspend_date(
        self,
    ):
        user = UserFactory()
        user.last_login = None
        user.date_joined = self.before_suspend_date
        user.save(update_fields=["last_login", "date_joined"])

        result = list(get_users_to_suspend())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], user)

    def test_excludes_user_when_last_login_after_suspend_date(self):
        user = UserFactory()
        user.last_login = self.after_suspend_date
        user.save(update_fields=["last_login"])

        result = list(get_users_to_suspend())

        self.assertEqual(len(result), 0)

    def test_excludes_user_when_last_login_null_and_date_joined_after_suspend_date(
        self,
    ):
        user = UserFactory()
        user.last_login = None
        user.date_joined = self.after_suspend_date
        user.save(update_fields=["last_login", "date_joined"])

        result = list(get_users_to_suspend())

        self.assertEqual(len(result), 0)

    def test_excludes_inactive_user_last_login_before_suspend_date(self):
        user = UserFactory(is_active=False)
        user.last_login = self.before_suspend_date
        user.save(update_fields=["last_login"])

        result = list(get_users_to_suspend())

        self.assertEqual(len(result), 0)

    def test_excludes_superuser_last_login_before_suspend_date(self):
        user = UserFactory(is_superuser=True)
        user.last_login = self.before_suspend_date
        user.save(update_fields=["last_login"])

        result = list(get_users_to_suspend())

        self.assertEqual(len(result), 0)

    def test_excludes_staff_last_login_before_suspend_date(self):
        user = UserFactory(is_staff=True)
        user.last_login = self.before_suspend_date
        user.save(update_fields=["last_login"])

        result = list(get_users_to_suspend())

        self.assertEqual(len(result), 0)


@freeze_time("2026-02-25 12:00:00")
class TestSuspendInactiveUsers(TestCase):
    def setUp(self):
        self.before_suspend_date = timezone.now() - timedelta(
            days=INACTIVE_ACCOUNT_SUSPEND_DAYS + 1
        )
        self.before_warning_date = timezone.now() - timedelta(
            days=INACTIVE_ACCOUNT_WARNING_DAYS + 1
        )

    @patch("hfurb_scripts.suspend_inactive_users.send_email")
    def test_dry_run_does_not_suspend_users(self, mock_send_email):
        user = UserFactory()
        user.last_login = self.before_suspend_date
        user.save(update_fields=["last_login"])

        suspend_inactive_users(dry_run=True)

        user.refresh_from_db()

        self.assertTrue(user.is_active)
        self.assertEqual(mock_send_email.call_count, 0)

    @patch("hfurb_scripts.suspend_inactive_users.send_email")
    def test_dry_run_false_sends_warning_email(self, mock_send_email):
        user = UserFactory()
        user.last_login = self.before_warning_date
        user.save(update_fields=["last_login"])

        suspend_inactive_users(dry_run=False)

        user.refresh_from_db()

        self.assertTrue(user.is_active)
        self.assertEqual(mock_send_email.call_count, 1)

    @patch("hfurb_scripts.suspend_inactive_users.send_email")
    def test_dry_run_false_suspends_user_and_sends_emails(self, mock_send_email):
        user = UserFactory()
        user.last_login = self.before_suspend_date
        user.save(update_fields=["last_login"])

        self.assertTrue(user.is_active)
        self.assertEqual(user.groups.count(), 0)

        suspend_inactive_users(dry_run=False)

        user.refresh_from_db()

        self.assertFalse(user.is_active)
        self.assertEqual(user.groups.count(), 0)
        self.assertEqual(mock_send_email.call_count, 1)

    @patch("hfurb_scripts.suspend_inactive_users.send_email")
    def test_dry_run_false_clears_groups_on_suspended_user(self, mock_send_email):
        user = UserFactory()
        user.last_login = self.before_suspend_date
        user.save(update_fields=["last_login"])

        # Add a group to the user
        group = GroupFactory()
        user.groups.add(group)

        user.refresh_from_db()

        self.assertTrue(user.is_active)
        self.assertEqual(user.groups.count(), 1)

        suspend_inactive_users(dry_run=False)

        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertEqual(user.groups.count(), 0)
        self.assertEqual(mock_send_email.call_count, 1)
