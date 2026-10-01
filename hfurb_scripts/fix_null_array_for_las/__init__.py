import logging
import os
import sys
from collections import Counter
from pathlib import Path

import django
from django.db import DatabaseError, transaction
from django.db.models import Q
from dotenv import load_dotenv

from hfurb_scripts.script_utils import percentage
from ontology.models import MvAccommodationRequest

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "case_management.settings")
django.setup()

logger = logging.getLogger(__name__)


def find_records():
    ars = MvAccommodationRequest.objects.filter(
        Q(ltla_name=[None]) | Q(utla_name=[None])
    )

    for ar in ars.iterator():
        yield ar, ar.ltla_name == [None], ar.utla_name == [None]


def fix_null_array_for_las(dry_run=True):
    logger.info("Start fix_null_array_for_las with dry_run=%s", dry_run)

    counts = Counter(
        success=0,
        failed=0,
    )

    for accommodation_request, ltla_error, utla_error in find_records():
        if ltla_error:
            accommodation_request.ltla_name = None
        if utla_error:
            accommodation_request.utla_name = None

        try:
            with transaction.atomic():
                accommodation_request.save()
                logger.info(
                    "Processed AR: %s",
                    accommodation_request.id,
                )
                if dry_run:
                    transaction.set_rollback(True)
                counts["success"] += 1
        except DatabaseError as exc:
            logger.exception(
                "Exception processing AR: %s; error: %s",
                accommodation_request.id,
                exc,
            )
            counts["failed"] += 1

    logger.info("End fix_null_array_for_las with dry_run=%s", dry_run)

    logger.info(
        "%s succeeded (%.1f%%), %s failed (%.1f%%)",
        counts["success"],
        percentage(counts["success"], counts.total()),
        counts["failed"],
        percentage(counts["failed"], counts.total()),
    )


def run(dry_run=True):
    """
    Usage from within ECS container:
        # Normal run (makes changes):
        python manage.py shell \
        -c "from hfurb_scripts.fix_null_array_for_las import run; \
        run(dry_run=False)"


        # Dry run (shows what would be changed):
        python manage.py shell \
        -c "from hfurb_scripts.fix_null_array_for_las import run; \
        run()"
    """

    fix_null_array_for_las(dry_run=dry_run)
