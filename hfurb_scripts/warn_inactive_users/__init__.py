import logging
import os
import sys
from datetime import timedelta
from pathlib import Path

import django
from django.db.models import Q
from django.utils import timezone
from dotenv import load_dotenv

from case_management.settings import WARNING_INACTIVE_USERS_TEMPLATE
from webapp.notify import send_email

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "case_management.settings")
django.setup()

from accounts.models import User  # noqa: E402

logger = logging.getLogger(__name__)

WARNING_DAYS = 60


def get_users_for_warning_email():
    cutoff = timezone.now() - timedelta(days=WARNING_DAYS)

    return (
        User.objects.filter(
            is_active=True,
        )
        .filter(
            Q(last_login__lte=cutoff)
            | Q(last_login__isnull=True, date_joined__lte=cutoff)
        )
        .exclude(Q(is_superuser=True) | Q(is_staff=True))
    )


def warn_inactive_users(dry_run=True):
    logger.info("Starting warn_inactive_users")

    logging.info(
        "Using WARNING_INACTIVE_USERS_TEMPLATE id: %s", WARNING_INACTIVE_USERS_TEMPLATE
    )

    if dry_run:
        logging.info("DRY RUN MODE")

    warning_users = get_users_for_warning_email()
    logger.info("Warning (90d): %s users", warning_users.count())

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

    logger.info("Ending warn_inactive_users")


def run(dry_run=True):
    """
    Usage from within ECS container:
        # Normal run (makes changes):
        python manage.py shell \
        -c "from hfurb_scripts.warn_inactive_users import run; \
        run(dry_run=False)"

        # Dry run (shows what would be changed):
        python manage.py shell \
        -c "from hfurb_scripts.warn_inactive_users import run; \
        run()"
    """

    warn_inactive_users(dry_run=dry_run)
