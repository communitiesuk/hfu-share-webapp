import logging
import os
import sys
from collections import Counter
from pathlib import Path

import django
from django.db import transaction
from django.db.models import Q
from dotenv import load_dotenv

from deduplication.models import AccommodationDuplicateGroup
from ontology.models import (
    DevCheckV2,
    MvAccommodation,
    MvAccommodationRequest,
    MvInteraction,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "case_management.settings")
django.setup()

logger = logging.getLogger(__name__)


AUTHOR = "clean_up_duplicate_accommodations_job"


class SkipRow(Exception):
    pass


# TODO: replace with the real source of IDs once decided, either a temporary
# table populated with the records to process or a file read from S3.
# Each row is a list of duplicate accommodation IDs with the "master" record first
def get_records_to_process() -> list[list[str]]:
    records_to_process: list[list[str]] = []
    return records_to_process


def has_dependencies(accommodation: MvAccommodation) -> bool:
    """
    Returns True if deleting the accommodation would lose a linked record
    """
    if MvAccommodationRequest.objects.filter(
        Q(accommodation_id__contains=[accommodation.id])
        | Q(primary_accommodation_id=accommodation.id)
        | Q(bridging_accommodation_id=accommodation.id)
        | Q(temporary_accommodation_id=accommodation.id)
        | Q(previous_accommodation_id__contains=[accommodation.id])
    ).exists():
        return True

    if MvInteraction.objects.filter(linked_accommodation=accommodation).exists():
        return True

    if DevCheckV2.objects.filter(accommodation=accommodation).exists():
        return True

    return AccommodationDuplicateGroup.objects_including_archived.filter(
        Q(principal_record=accommodation) | Q(accommodations=accommodation)
    ).exists()


def get_principal_record_values(master: MvAccommodation) -> dict:
    return {
        "full_address": master.full_address,
        "postcode": master.postcode,
        "ltla_name": master.ltla_name,
        "utla_name": master.utla_name,
    }


def process_row(row: list[str]) -> tuple[int, int]:
    """
    Deletes the duplicates nothing depends on, and deduplicates the master with
    the rest. Returns the number of records deleted and deduplicated
    """
    if len(row) < 2:
        raise SkipRow("needs a master and at least one duplicate")

    accommodations = MvAccommodation.objects_including_archived.in_bulk(row)
    missing = [
        accommodation_id
        for accommodation_id in row
        if accommodation_id not in accommodations
    ]
    if missing:
        raise SkipRow(f"accommodations not found: {missing}")

    master, *duplicates = [accommodations[accommodation_id] for accommodation_id in row]

    to_delete = []
    to_deduplicate = []

    for duplicate in duplicates:
        if has_dependencies(duplicate):
            logger.info(
                "Accommodation: %s will be deduplicated as it has linked records",
                duplicate.id,
            )
            to_deduplicate.append(duplicate)
        else:
            to_delete.append(duplicate)

    # Deduplication only accepts principal records, the same rule as the app
    if to_deduplicate:
        non_principal = [
            accommodation.id
            for accommodation in [master, *to_deduplicate]
            if not accommodation.is_principal
        ]
        if non_principal:
            raise SkipRow(f"non principal records need deduplicating: {non_principal}")

    for duplicate in to_delete:
        # Django clears the ID on delete, so keep it for logging
        duplicate_id = duplicate.id
        duplicate.delete()
        logger.info("Deleted Accommodation: %s", duplicate_id)

    if to_deduplicate:
        group = AccommodationDuplicateGroup.objects.create()
        group.accommodations.set([master, *to_deduplicate])
        group.deduplicate(get_principal_record_values(master), user=AUTHOR)
        logger.info(
            "Deduplicated Accommodations: %s into new principal: %s",
            [master.id, *[duplicate.id for duplicate in to_deduplicate]],
            group.principal_record_id,
        )

    return len(to_delete), len(to_deduplicate)


def clean_up_duplicate_accommodations(dry_run=True):
    logger.info("Start clean_up_duplicate_accommodations with dry_run=%s", dry_run)

    counts = Counter(
        rows_succeeded=0,
        rows_skipped=0,
        rows_failed=0,
        deleted=0,
        deduplicated=0,
    )

    for row_number, row in enumerate(get_records_to_process()):
        try:
            # Each row is all or nothing so a failure never leaves a half done row
            with transaction.atomic():
                deleted, deduplicated = process_row(row)
                if dry_run:
                    transaction.set_rollback(True)
        except SkipRow as reason:
            logger.warning("Skipping row %s: %s", row_number, reason)
            counts["rows_skipped"] += 1
            continue
        except Exception as exc:
            logger.exception("Exception processing row %s; error: %s", row_number, exc)
            counts["rows_failed"] += 1
            continue

        logger.info(
            "Processed row %s: %s deleted, %s deduplicated",
            row_number,
            deleted,
            deduplicated,
        )
        counts["rows_succeeded"] += 1
        counts["deleted"] += deleted
        counts["deduplicated"] += deduplicated

    logger.info("End clean_up_duplicate_accommodations with dry_run=%s", dry_run)
    logger.info(
        "Rows: %s succeeded, %s skipped, %s failed",
        counts["rows_succeeded"],
        counts["rows_skipped"],
        counts["rows_failed"],
    )
    logger.info(
        "Accommodations: %s deleted, %s deduplicated",
        counts["deleted"],
        counts["deduplicated"],
    )


def run(dry_run=True):
    """
    Usage from within ECS container:
        # Normal run (makes changes):
        python manage.py shell \
        -c "from hfurb_scripts.clean_up_duplicate_accommodations import run; \
        run(dry_run=False)"


        # Dry run (shows what would be changed):
        python manage.py shell \
        -c "from hfurb_scripts.clean_up_duplicate_accommodations import run; \
        run()"
    """

    clean_up_duplicate_accommodations(dry_run=dry_run)
