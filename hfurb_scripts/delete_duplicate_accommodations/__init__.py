import logging
import os
import sys
from collections import Counter
from pathlib import Path

import django
from django.db import DatabaseError, transaction
from dotenv import load_dotenv

from hfurb_scripts.script_utils import percentage
from ontology.models import MvAccommodation

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "case_management.settings")
django.setup()

logger = logging.getLogger(__name__)


# TODO: replace with the real source of IDs once decided, either a temporary
# table populated with the records to delete or a file read from S3
def get_records_to_delete() -> list[str]:
    records_to_delete: list[str] = []
    return records_to_delete


def delete_duplicate_accommodations(dry_run=True):
    logger.info("Start delete_duplicate_accommodations with dry_run=%s", dry_run)

    counts = Counter(
        success=0,
        failed=0,
        not_found=0,
        skipped_linked=0,
    )

    for accommodation_id in get_records_to_delete():
        # Use the manager that includes archived records, as duplicates may
        # already have been archived
        accommodation = MvAccommodation.objects_including_archived.filter(
            id=accommodation_id
        ).first()

        if accommodation is None:
            logger.info("Skipping Accommodation: %s as not found", accommodation_id)
            counts["not_found"] += 1
            continue

        # Avoid deleting accommodations linked to an AR
        if accommodation.get_accommodation_requests().exists():
            logger.warning(
                "Skipping Accommodation: %s as it is linked to an AR",
                accommodation_id,
            )
            counts["skipped_linked"] += 1
            continue

        try:
            with transaction.atomic():
                accommodation.delete()
                logger.info("Deleted Accommodation: %s", accommodation_id)
                if dry_run:
                    transaction.set_rollback(True)
                counts["success"] += 1
        except DatabaseError as exc:
            logger.exception(
                "Exception deleting Accommodation: %s; error: %s",
                accommodation_id,
                exc,
            )
            counts["failed"] += 1

    logger.info("End delete_duplicate_accommodations with dry_run=%s", dry_run)

    logger.info(
        "%s succeeded (%.1f%%), %s failed (%.1f%%)",
        counts["success"],
        percentage(counts["success"], counts.total()),
        counts["failed"],
        percentage(counts["failed"], counts.total()),
    )
    logger.info(
        "%s not found, %s skipped as linked to an AR",
        counts["not_found"],
        counts["skipped_linked"],
    )


def run(dry_run=True):
    """
    Usage from within ECS container:
        # Normal run (makes changes):
        python manage.py shell \
        -c "from hfurb_scripts.delete_duplicate_accommodations import run; \
        run(dry_run=False)"


        # Dry run (shows what would be changed):
        python manage.py shell \
        -c "from hfurb_scripts.delete_duplicate_accommodations import run; \
        run()"
    """

    delete_duplicate_accommodations(dry_run=dry_run)
