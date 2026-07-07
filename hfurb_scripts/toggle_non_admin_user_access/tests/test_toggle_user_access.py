from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from accounts.models import User
from hfurb_scripts.toggle_non_admin_user_access import (
    disable_users,
    enable_users,
    toggle_non_admin_user_access,
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)
from webapp.constants import INACTIVE_ACCOUNT_SUSPEND_DAYS


@freeze_time("2026-06-01 12:00:00")
class TestToggleUserAccess(TestCase):
    def setUp(self):
        now = timezone.now()
        suspended_date = now - timedelta(days=INACTIVE_ACCOUNT_SUSPEND_DAYS + 1)

        self.admin_user = get_admin_user()
        self.admin_user.is_staff = True
        self.admin_user.save()

        self.la_user = get_la_user()
        self.mhclg_user = get_mhclg_user()
        self.ukvi_user = get_ukvi_user()
        self.service_support_user = get_service_support_user()
        self.da_user = get_da_user()

        self.all_non_staff_users = [
            self.la_user,
            self.mhclg_user,
            self.ukvi_user,
            self.service_support_user,
            self.da_user,
        ]

        self.all_non_staff_users_ids = [user.id for user in self.all_non_staff_users]

        self.suspended_user = get_la_user()
        self.suspended_user.is_active = False
        self.suspended_user.last_login = suspended_date
        self.suspended_user.save()

        self.user_no_groups = get_la_user()
        self.user_no_groups.is_active = False
        self.user_no_groups.groups.clear()
        self.user_no_groups.save()

    def test_toggle_user_access_disables_non_staff_users(self):
        for user in self.all_non_staff_users:
            assert user.is_active

        toggle_non_admin_user_access(disable=True, enable=False)

        # Non staff users should be disabled
        non_staff_users = User.objects.filter(id__in=self.all_non_staff_users_ids)
        for user in non_staff_users:
            assert user.is_active is False

        # Staff users should be unaffected
        staff_users = User.objects.filter(is_staff=True)
        for user in staff_users:
            assert user.is_active

    def test_toggle_user_access_reenables_non_staff_users(self):
        # Users start off inactive except our admin user
        for user in self.all_non_staff_users:
            user.is_active = False
            user.save()
        assert self.admin_user.is_active

        toggle_non_admin_user_access(disable=False, enable=True)

        # Non staff users should be enabled
        non_staff_users = User.objects.filter(id__in=self.all_non_staff_users_ids)
        for user in non_staff_users:
            assert user.is_active
        # Staff users should be unaffected
        staff_users = User.objects.filter(is_staff=True)
        for user in staff_users:
            assert user.is_active

    def test_toggle_user_access_doesnt_reenable_suspended_user(self):
        disable_users()
        enable_users()

        self.suspended_user.refresh_from_db()

        self.assertFalse(self.suspended_user.is_active)

    def test_toggle_user_access_doesnt_reenable_no_group_user(self):
        self.assertFalse(self.user_no_groups.is_active)

        disable_users()
        enable_users()

        self.user_no_groups.refresh_from_db()

        self.assertFalse(self.user_no_groups.is_active)
