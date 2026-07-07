import logging
import os
import sys
from datetime import timedelta
from pathlib import Path

import django
from django.db.models import Q
from django.utils import timezone
from dotenv import load_dotenv

from case_management.settings import (
    SUSPEND_INACTIVE_USERS_TEMPLATE,
    WARNING_INACTIVE_USERS_TEMPLATE,
)
from webapp.constants import (
    INACTIVE_ACCOUNT_SUSPEND_DAYS,
    INACTIVE_ACCOUNT_WARNING_DAYS,
)
from webapp.notify import send_email

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "case_management.settings")
django.setup()

from accounts.models import User  # noqa: E402

logger = logging.getLogger(__name__)


def get_users_for_warning_email():
    today = timezone.now()
    warning_date = today - timedelta(days=INACTIVE_ACCOUNT_WARNING_DAYS)
    suspend_date = today - timedelta(days=INACTIVE_ACCOUNT_SUSPEND_DAYS)

    return User.objects.filter(
        Q(last_login__gt=suspend_date, last_login__lte=warning_date)
        | Q(
            last_login__isnull=True,
            date_joined__gt=suspend_date,
            date_joined__lte=warning_date,
        )
    ).exclude(Q(is_superuser=True) | Q(is_staff=True))


def get_users_to_suspend():
    suspend_date = timezone.now() - timedelta(days=INACTIVE_ACCOUNT_SUSPEND_DAYS)

    return (
        User.objects.filter(
            is_active=True,
        )
        .filter(
            Q(last_login__lte=suspend_date)
            | Q(last_login__isnull=True, date_joined__lte=suspend_date)
        )
        .exclude(Q(is_superuser=True) | Q(is_staff=True))
    )


def suspend_inactive_users(dry_run=True):
    logging.info("Starting suspend_inactive_users")

    if dry_run:
        logging.info("DRY RUN MODE")

    logging.info(
        "Using SUSPEND_INACTIVE_USERS_TEMPLATE id: %s", SUSPEND_INACTIVE_USERS_TEMPLATE
    )
    logging.info(
        "Using WARNING_INACTIVE_USERS_TEMPLATE id: %s", WARNING_INACTIVE_USERS_TEMPLATE
    )

    warning_users = get_users_for_warning_email()
    suspend_users = get_users_to_suspend()
    logger.info("Warning (60d): %s users", warning_users.count())
    logger.info("Suspend (90d): %s users", suspend_users.count())

    for warned_user in warning_users:
        last_login = warned_user.last_login if warned_user.last_login else "None"
        logger.info(
            "Sending WARNING email to %s, last_login: %s, date_joined: %s",
            warned_user.email,
            last_login,
            warned_user.date_joined,
        )

        if not dry_run:
            send_email(
                email_address=warned_user.email,
                template_id=WARNING_INACTIVE_USERS_TEMPLATE,
            )

    for suspended_user in suspend_users:
        last_login = suspended_user.last_login if suspended_user.last_login else "None"
        logger.info(
            "Suspending account and sending SUSPEND email to %s,"
            "last_login: %s, date_joined %s",
            suspended_user.email,
            last_login,
            suspended_user.date_joined,
        )

        if not dry_run:
            suspended_user.is_active = False
            suspended_user.groups.clear()
            suspended_user.save()

            send_email(
                email_address=suspended_user.email,
                template_id=SUSPEND_INACTIVE_USERS_TEMPLATE,
            )

    logging.info("Ending suspend_inactive_users")


def run(dry_run=True):
    """
    Usage from within ECS container:
        # Normal run (makes changes):
        python manage.py shell \
        -c "from hfurb_scripts.suspend_inactive_users import run; \
        run(dry_run=False)"

        # Dry run (shows what would be changed):
        python manage.py shell \
        -c "from hfurb_scripts.suspend_inactive_users import run; \
        run()"
    """

    suspend_inactive_users(dry_run=dry_run)
