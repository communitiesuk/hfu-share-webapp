import csv
import logging
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import NamedTuple

import django
from django.conf import settings
from django.db import transaction
from dotenv import load_dotenv

from accounts.enums import GroupType
from accounts.models import GroupInfo
from ontology.models import MvAccommodation, VisaApplication
from webapp.s3 import get_s3_client

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "case_management.settings")
django.setup()

logger = logging.getLogger(__name__)


RECORDS_BUCKET_NAME = settings.MANUAL_DATA_IMPORTS_S3_BUCKET_NAME

ACCOMMODATIONS_FILE_KEY = "accommodations_moved.csv"
VISA_APPLICATIONS_FILE_KEY = "visa_application_candidates.csv"


# Reasons a record is not corrected
NOT_FOUND = "it was not found"
DUPLICATE_IN_FILE = "it appears more than once in the file"
NO_TARGET = "the file does not say which local authority it should have"
NO_LOCAL_AUTHORITY_GROUP = "no local authority group matches the one it should have"
AMBIGUOUS_LOCAL_AUTHORITY_GROUP = (
    "more than one local authority group matches the one it should have"
)
UTLA_DOES_NOT_MATCH_GROUP = "the group's upper tier LA does not match the file"
ALREADY_CORRECT = "it already has the local authority it should have"
CHANGED_SINCE_EXPORT = "its current local authority no longer matches the file"
NOT_EDITABLE = "it is not editable"
FAILED = "it failed to update"

NULL_VALUES = {"", "none", "null"}


class AccommodationFix(NamedTuple):
    accommodation_id: str
    ltla_should_have: str | None
    ltla_changed_to: str | None
    utla_should_have: str | None
    utla_changed_to: str | None


class VisaApplicationFix(NamedTuple):
    visa_application_id: str
    ltla_should_have: str | None
    ltla_changed_to: str | None
    utla_should_have: str | None
    utla_changed_to: str | None
    country_changed_to: str | None


def blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None

    stripped = value.strip()
    return None if stripped.lower() in NULL_VALUES else stripped


def read_csv_rows(file_key: str) -> list[dict[str, str]]:
    response = get_s3_client().get_object(Bucket=RECORDS_BUCKET_NAME, Key=file_key)
    lines = response["Body"].read().decode("utf-8-sig").splitlines()
    return list(csv.DictReader(lines))


def get_accommodations_to_process() -> list[AccommodationFix]:
    return [
        AccommodationFix(
            accommodation_id=row["accommodation_id"].strip(),
            ltla_should_have=blank_to_none(row["ltla_should_have"]),
            ltla_changed_to=blank_to_none(row["ltla_changed_to"]),
            utla_should_have=blank_to_none(row["utla_should_have"]),
            utla_changed_to=blank_to_none(row["utla_changed_to"]),
        )
        for row in read_csv_rows(ACCOMMODATIONS_FILE_KEY)
    ]


def get_visa_applications_to_process() -> list[VisaApplicationFix]:
    return [
        VisaApplicationFix(
            visa_application_id=row["visa_application_id"].strip(),
            ltla_should_have=blank_to_none(row["ltla_should_have"]),
            ltla_changed_to=blank_to_none(row["ltla_changed_to"]),
            utla_should_have=blank_to_none(row["utla_should_have"]),
            utla_changed_to=blank_to_none(row["utla_changed_to"]),
            country_changed_to=blank_to_none(row["country_changed_to"]),
        )
        for row in read_csv_rows(VISA_APPLICATIONS_FILE_KEY)
    ]


def get_local_authority_groups(ltla_name: str) -> list[GroupInfo]:
    return list(
        GroupInfo.objects.filter(
            ltla_name=ltla_name,
            is_utla=False,
            group_type=GroupType.LOCAL_AUTHORITY,
        )[:2]
    )


def get_reason_target_is_invalid(
    groups: list[GroupInfo], utla_should_have: str | None
) -> str | None:
    if not groups:
        return NO_LOCAL_AUTHORITY_GROUP

    if len(groups) > 1:
        return AMBIGUOUS_LOCAL_AUTHORITY_GROUP

    if groups[0].utla_name != utla_should_have:
        return UTLA_DOES_NOT_MATCH_GROUP

    return None


def get_reason_not_to_fix_accommodation(
    accommodation: MvAccommodation, accommodation_fix: AccommodationFix
) -> str | None:
    # Checked before CHANGED_SINCE_EXPORT, which an already corrected record also meets
    if (
        accommodation.ltla_name == accommodation_fix.ltla_should_have
        and accommodation.utla_name == accommodation_fix.utla_should_have
    ):
        return ALREADY_CORRECT

    if (
        accommodation.ltla_name != accommodation_fix.ltla_changed_to
        or accommodation.utla_name != accommodation_fix.utla_changed_to
    ):
        return CHANGED_SINCE_EXPORT

    # save() refuses accommodations that are not editable
    if not accommodation.is_editable:
        return NOT_EDITABLE

    return None


def get_reason_not_to_fix_visa_application(
    visa_application: VisaApplication,
    visa_application_fix: VisaApplicationFix,
    group: GroupInfo,
) -> str | None:
    if (
        visa_application.ltla_name == visa_application_fix.ltla_should_have
        and visa_application.utla_name == group.utla_name
    ):
        return ALREADY_CORRECT

    if (
        visa_application.ltla_name != visa_application_fix.ltla_changed_to
        or visa_application.utla_name != visa_application_fix.utla_changed_to
        or visa_application.country != visa_application_fix.country_changed_to
    ):
        return CHANGED_SINCE_EXPORT

    return None


def revert_accommodation(
    accommodation: MvAccommodation,
    ltla_name: str,
    utla_name: str | None,
    dry_run: bool,
) -> None:
    with transaction.atomic():
        accommodation.ltla_name = ltla_name
        accommodation.utla_name = utla_name
        accommodation.save()
        if dry_run:
            transaction.set_rollback(True)

    logger.info(
        "%s Accommodation %s to %s, %s",
        "Would revert" if dry_run else "Reverted",
        accommodation.id,
        ltla_name,
        utla_name,
    )


def revert_visa_application(
    visa_application: VisaApplication,
    ltla_name: str,
    utla_name: str | None,
    country: str | None,
    dry_run: bool,
) -> None:
    with transaction.atomic():
        visa_application.ltla_name = ltla_name
        visa_application.utla_name = utla_name
        visa_application.country = country
        visa_application.save(update_fields=["ltla_name", "utla_name", "country"])
        if dry_run:
            transaction.set_rollback(True)

    logger.info(
        "%s VisaApplication %s to %s, %s, %s",
        "Would revert" if dry_run else "Reverted",
        visa_application.visa_application_id,
        ltla_name,
        utla_name,
        country,
    )


def fix_accommodation(
    accommodation: MvAccommodation, accommodation_fix: AccommodationFix, dry_run: bool
) -> str | None:
    try:
        if not accommodation_fix.ltla_should_have:
            return NO_TARGET

        groups = get_local_authority_groups(accommodation_fix.ltla_should_have)
        reason = get_reason_target_is_invalid(
            groups, accommodation_fix.utla_should_have
        )
        if reason:
            return reason

        reason = get_reason_not_to_fix_accommodation(accommodation, accommodation_fix)
        if reason:
            return reason

        revert_accommodation(
            accommodation,
            accommodation_fix.ltla_should_have,
            accommodation_fix.utla_should_have,
            dry_run,
        )
    except Exception as exc:
        logger.warning(
            "Failed to revert Accommodation %s: %s",
            accommodation.id,
            type(exc).__name__,
        )
        return FAILED

    return None


def fix_visa_application(
    visa_application: VisaApplication,
    visa_application_fix: VisaApplicationFix,
    dry_run: bool,
) -> str | None:
    try:
        if not visa_application_fix.ltla_should_have:
            return NO_TARGET

        groups = get_local_authority_groups(visa_application_fix.ltla_should_have)
        reason = get_reason_target_is_invalid(
            groups, visa_application_fix.utla_should_have
        )
        if reason:
            return reason

        group = groups[0]
        reason = get_reason_not_to_fix_visa_application(
            visa_application, visa_application_fix, group
        )
        if reason:
            return reason

        revert_visa_application(
            visa_application,
            visa_application_fix.ltla_should_have,
            group.utla_name,
            group.da_name,
            dry_run,
        )
    except Exception as exc:
        logger.warning(
            "Failed to revert VisaApplication %s: %s",
            visa_application.visa_application_id,
            type(exc).__name__,
        )
        return FAILED

    return None


def log_summary(
    record_type: str,
    reverted_count: int,
    not_reverted: dict[str, list[str]],
    dry_run: bool,
) -> None:
    logger.info(
        "%s with dry_run=%s: %s reverted, %s not reverted",
        record_type,
        dry_run,
        reverted_count,
        sum(len(ids) for ids in not_reverted.values()),
    )
    for reason, ids in not_reverted.items():
        logger.info("%s not reverted as %s: %s", len(ids), reason, ", ".join(ids))


def process_accommodations(
    accommodation_fixes: list[AccommodationFix], dry_run: bool
) -> None:
    reverted_count = 0
    not_reverted: dict[str, list[str]] = defaultdict(list)

    id_counts = Counter(
        accommodation_fix.accommodation_id for accommodation_fix in accommodation_fixes
    )
    accommodations = MvAccommodation.objects_including_archived.in_bulk(list(id_counts))

    for accommodation_fix in accommodation_fixes:
        accommodation = accommodations.get(accommodation_fix.accommodation_id)
        reason: str | None
        if id_counts[accommodation_fix.accommodation_id] > 1:
            reason = DUPLICATE_IN_FILE
        elif accommodation is None:
            reason = NOT_FOUND
        else:
            reason = fix_accommodation(accommodation, accommodation_fix, dry_run)

        if reason:
            logger.info(
                "Not reverting Accommodation %s as %s",
                accommodation_fix.accommodation_id,
                reason,
            )
            not_reverted[reason].append(accommodation_fix.accommodation_id)
        else:
            reverted_count += 1

    log_summary("Accommodations", reverted_count, not_reverted, dry_run)


def process_visa_applications(
    visa_application_fixes: list[VisaApplicationFix], dry_run: bool
) -> None:
    reverted_count = 0
    not_reverted: dict[str, list[str]] = defaultdict(list)

    id_counts = Counter(
        visa_application_fix.visa_application_id
        for visa_application_fix in visa_application_fixes
    )
    visa_applications = VisaApplication.objects.in_bulk(list(id_counts))

    for visa_application_fix in visa_application_fixes:
        visa_application = visa_applications.get(
            visa_application_fix.visa_application_id
        )
        reason: str | None
        if id_counts[visa_application_fix.visa_application_id] > 1:
            reason = DUPLICATE_IN_FILE
        elif visa_application is None:
            reason = NOT_FOUND
        else:
            reason = fix_visa_application(
                visa_application, visa_application_fix, dry_run
            )

        if reason:
            logger.info(
                "Not reverting VisaApplication %s as %s",
                visa_application_fix.visa_application_id,
                reason,
            )
            not_reverted[reason].append(visa_application_fix.visa_application_id)
        else:
            reverted_count += 1

    log_summary("Visa applications", reverted_count, not_reverted, dry_run)


def fix_incorrectly_assigned_las(dry_run: bool = True) -> None:
    logger.info("Start fix_incorrectly_assigned_las with dry_run=%s", dry_run)

    accommodation_fixes = get_accommodations_to_process()
    visa_application_fixes = get_visa_applications_to_process()

    process_accommodations(accommodation_fixes, dry_run)
    process_visa_applications(visa_application_fixes, dry_run)

    logger.info("End fix_incorrectly_assigned_las with dry_run=%s", dry_run)
