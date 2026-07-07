import logging
import os
import sys
from pathlib import Path

import django
from dotenv import load_dotenv

from ontology.models import MvAccommodationRequest

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "case_management.settings")
django.setup()

logger = logging.getLogger(__name__)


def recalculate_checks_status(dry_run=True):
    logger.info("Start recalculate_checks_status with dry_run=%s", dry_run)

    ars = MvAccommodationRequest.objects.filter(
        requires_checks_status_recalculation=True
    )

    ar_count = ars.count()

    logger.info("ARs to process: %s", ar_count)

    for ar in ars:
        if dry_run:
            logger.info(
                "Dry Run - Skipping AR: %s, checks_status: %s",
                ar.id,
                ar.checks_status,
            )
        else:
            logger.info("Processing AR: %s, checks_status: %s", ar.id, ar.checks_status)

            try:
                ar.reset_and_redetermine_status(
                    author="recalculate_checks_status_job",
                    unset_recalculation_flag=True,
                )
            except Exception as exc:
                logger.exception(
                    "Exception calling reset_and_redetermine_status for AR: %s;"
                    " error: %s",
                    ar.id,
                    exc,
                )
            else:
                logger.info(
                    "Finished processing AR: %s, checks_status: %s",
                    ar.id,
                    ar.checks_status,
                )

    ars_after = MvAccommodationRequest.objects.filter(
        requires_checks_status_recalculation=True
    )
    ar_count_after = ars_after.count()

    logger.info("ARs to process after completion: %s", ar_count_after)

    if not dry_run:
        if ar_count_after > 0:
            logger.error("Some ARs were not updated during the script run")

    logger.info("End recalculate_checks_status with dry_run=%s", dry_run)


def run(dry_run=True):
    """
    Usage from within ECS container:
        # Normal run (makes changes):
        python manage.py shell \
        -c "from hfurb_scripts.recalculate_checks_status import run; \
        run(dry_run=False)"


        # Dry run (shows what would be changed):
        python manage.py shell \
        -c "from hfurb_scripts.recalculate_checks_status import run; \
        run()"
    """

    recalculate_checks_status(dry_run=dry_run)
