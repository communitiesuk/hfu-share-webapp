# Disable all non-admin users (regardless of Group membership) via the command line.
# Use this script to revoke access in an emergency or during planned maintenance.
import logging
import os
import sys
from datetime import timedelta
from pathlib import Path

import django
from django.utils import timezone
from dotenv import load_dotenv

from webapp.constants import INACTIVE_ACCOUNT_SUSPEND_DAYS

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "case_management.settings")
django.setup()

from accounts.models import User  # noqa: E402


def toggle_non_admin_user_access(disable=False, enable=False):
    now = timezone.now()
    suspended_cutoff = now - timedelta(days=INACTIVE_ACCOUNT_SUSPEND_DAYS)

    staff_users = User.objects.filter(is_staff=True)
    non_staff_non_suspended_users_with_groups = User.objects.filter(
        is_staff=False, last_login__gte=suspended_cutoff, groups__isnull=False
    ).distinct()

    enabled_or_disabled = "enabled" if enable else "disabled"

    logging.info(
        "%d non-admin users will be %s.",
        non_staff_non_suspended_users_with_groups.count(),
        enabled_or_disabled,
    )
    logging.info("%d admin users will be unaffected.", staff_users.count())

    for user in non_staff_non_suspended_users_with_groups:
        if disable:
            user.is_active = False
            user.save()
        if enable:
            user.is_active = True
            user.save()
    logging.info("Script complete.")


def disable_users():
    toggle_non_admin_user_access(disable=True, enable=False)


def enable_users():
    toggle_non_admin_user_access(disable=False, enable=True)
