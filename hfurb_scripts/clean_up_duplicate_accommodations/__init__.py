import logging
import os
import sys
from collections import defaultdict
from pathlib import Path

import django
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
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


# Reasons a duplicate is not archived
NOT_FOUND = "it was not found"
ALREADY_ARCHIVED = "it is already archived"
NOT_EDITABLE = "it is not editable"
HAS_LINKED_RECORDS = "it has linked records"
FAILED = "it failed to archive"


# TODO: replace with the real source of IDs once decided, either a temporary
# table populated with the records to process or a file read from S3.
# Each row is a list of duplicate accommodation IDs with the "master" record first
def get_records_to_process() -> list[list[str]]:
    records_to_process: list[list[str]] = []
    return records_to_process


def has_dependencies(accommodation: MvAccommodation) -> bool:
    """
    Returns True if the accommodation has linked records, so is not safe to archive
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


def get_reason_not_to_archive(accommodation: MvAccommodation) -> str | None:
    if accommodation.is_archived:
        return ALREADY_ARCHIVED

    # save() refuses accommodations that are not editable
    if not accommodation.is_editable:
        return NOT_EDITABLE

    if has_dependencies(accommodation):
        return HAS_LINKED_RECORDS

    return None


def archive(accommodation: MvAccommodation, dry_run: bool):
    with transaction.atomic():
        accommodation.is_archived = True
        accommodation.archived_at = timezone.now()
        accommodation.save()
        if dry_run:
            transaction.set_rollback(True)


def archive_duplicate(accommodation: MvAccommodation, dry_run: bool) -> str | None:
    """
    Archives the duplicate if it is safe to, otherwise returns the reason it was
    not archived
    """
    try:
        reason = get_reason_not_to_archive(accommodation)
        if reason:
            return reason

        archive(accommodation, dry_run)
    except Exception as exc:
        logger.exception(
            "Exception archiving Accommodation: %s; error: %s", accommodation.id, exc
        )
        return FAILED

    return None


def clean_up_duplicate_accommodations(dry_run=True):
    logger.info("Start clean_up_duplicate_accommodations with dry_run=%s", dry_run)

    archived_count = 0
    # Duplicates we want to archive but can't, grouped by the reason why
    not_archived_ids: dict[str, list[str]] = defaultdict(list)

    records_to_process = get_records_to_process()

    for row in records_to_process:
        # The master is first in the row and is never archived
        duplicate_ids = row[1:]
        duplicates = MvAccommodation.objects_including_archived.in_bulk(duplicate_ids)

        for duplicate_id in duplicate_ids:
            duplicate = duplicates.get(duplicate_id)
            reason = archive_duplicate(duplicate, dry_run) if duplicate else NOT_FOUND

            if reason:
                logger.info(
                    "Not archiving Accommodation: %s as %s", duplicate_id, reason
                )
                not_archived_ids[reason].append(duplicate_id)
            else:
                logger.info("Archived Accommodation: %s", duplicate_id)
                archived_count += 1

    logger.info("End clean_up_duplicate_accommodations with dry_run=%s", dry_run)
    logger.info(
        "Accommodations: %s archived, %s not archived",
        archived_count,
        sum(len(ids) for ids in not_archived_ids.values()),
    )
    for reason, ids in not_archived_ids.items():
        logger.info("%s not archived as %s: %s", len(ids), reason, ", ".join(ids))


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
