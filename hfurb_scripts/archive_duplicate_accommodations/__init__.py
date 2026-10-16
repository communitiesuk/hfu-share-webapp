import csv
import json
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple

import django
from django.conf import settings
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
from webapp.s3 import get_s3_client

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


class DuplicateSet(NamedTuple):
    reference: str
    master_id: str
    duplicate_ids: list[str]


RECORDS_FILE_KEY = "duplicate_accommodation_ids_to_remove_10_26.csv"


def get_records_to_process() -> list[DuplicateSet]:
    """
    Reads the CSV of duplicates from S3, which has one row per set of duplicates
    with the columns reference, id (the master) and ids_list (the master and all
    of its duplicates). Returns a DuplicateSet per row
    """
    response = get_s3_client().get_object(
        Bucket=settings.MANUAL_DATA_IMPORTS_S3_BUCKET_NAME, Key=RECORDS_FILE_KEY
    )
    lines = response["Body"].read().decode("utf-8").splitlines()

    records_to_process = []
    for row in csv.DictReader(lines):
        master_id = row["id"].strip()
        # Remove the master by ID, so it is never archived even if it is not first
        duplicate_ids = [
            accommodation_id
            for accommodation_id in json.loads(row["ids_list"])
            if accommodation_id != master_id
        ]
        records_to_process.append(
            DuplicateSet(row["reference"].strip(), master_id, duplicate_ids)
        )

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


def archive_duplicate_accommodations(dry_run=True):
    logger.info("Start archive_duplicate_accommodations with dry_run=%s", dry_run)

    archived_count = 0
    # Duplicates we want to archive but can't, grouped by the reason why
    not_archived_ids: dict[str, list[str]] = defaultdict(list)

    records_to_process = get_records_to_process()

    for duplicate_set in records_to_process:
        duplicate_ids = duplicate_set.duplicate_ids
        duplicates = MvAccommodation.objects_including_archived.in_bulk(duplicate_ids)

        for duplicate_id in duplicate_ids:
            duplicate = duplicates.get(duplicate_id)
            reason = archive_duplicate(duplicate, dry_run) if duplicate else NOT_FOUND

            if reason:
                logger.info(
                    "Reference %s: not archiving Accommodation %s as %s",
                    duplicate_set.reference,
                    duplicate_id,
                    reason,
                )
                not_archived_ids[reason].append(duplicate_id)
            else:
                logger.info(
                    "Reference %s: archived Accommodation %s",
                    duplicate_set.reference,
                    duplicate_id,
                )
                archived_count += 1

    logger.info("End archive_duplicate_accommodations with dry_run=%s", dry_run)
    logger.info(
        "Accommodations: %s archived, %s not archived",
        archived_count,
        sum(len(ids) for ids in not_archived_ids.values()),
    )
    for reason, ids in not_archived_ids.items():
        logger.info("%s not archived as %s: %s", len(ids), reason, ", ".join(ids))
