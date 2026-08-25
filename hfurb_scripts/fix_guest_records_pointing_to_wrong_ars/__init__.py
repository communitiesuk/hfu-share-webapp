import logging
import os
import sys
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Literal, Optional, Tuple

import django
from django.db import DatabaseError, transaction
from django.db.models import QuerySet
from dotenv import load_dotenv

from ontology.models import MvAccommodationRequest, MvPerson

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "case_management.settings")
django.setup()

logger = logging.getLogger(__name__)


@contextmanager
def log_and_wrap_record_processing(
    scenario_number: int,
    accommodation_request: MvAccommodationRequest,
    guest: MvPerson,
    closed_accommodation_requests: Optional[QuerySet[MvAccommodationRequest]],
):
    result = {"success": True}
    record_log = f"AR: {accommodation_request.id}; Guest: {guest.id};"

    if closed_accommodation_requests:
        for closed_ar in closed_accommodation_requests:
            record_log += f" Closed AR: {closed_ar.id};"

    try:
        with transaction.atomic():
            logger.info(
                "Started processing %s for scenario %s",
                record_log,
                scenario_number,
            )
            yield result
            logger.info(
                "Finished processing %s for scenario %s",
                record_log,
                scenario_number,
            )

    except DatabaseError as exc:
        logger.exception(
            "Exception processing %s for scenario %s; error: %s",
            record_log,
            scenario_number,
            exc,
        )
        result["success"] = False


def assign_ar_to_guest(accommodation_request: MvAccommodationRequest, guest: MvPerson):
    guest.accommodation_request_id = accommodation_request.id  # type: ignore[attr-defined]
    guest.save()


def remove_guest_from_ar(
    accommodation_request: MvAccommodationRequest, guest: MvPerson
):
    accommodation_request.person_id.remove(guest.id)
    accommodation_request.save()


def find_records_for_each_scenario():
    open_ars = MvAccommodationRequest.objects.exclude(
        status__in=MvAccommodationRequest.CLOSED_STATUSES,
    )

    for ar in open_ars.iterator():
        for guest in MvPerson.objects.filter(id__in=ar.person_id or []):
            if str(guest.accommodation_request_id) != str(ar.id):
                yield ar, guest


# Here are the different scenarios we want to fix:
# 1) the AR has the Guest ID but the Guest has an ID for an AR which
#    does not contain that Guest
# 2) an open and a closed AR has the guest ID but
#    the Guest has the ID for the AR that is closed
# 3) an open and a closed AR has the guest ID but
#    the Guest has an ID for an AR which does not contain that Guest
def determine_scenario(
    accommodation_request: MvAccommodationRequest,
    guest: MvPerson,
) -> (
    Tuple[Literal[1], None]
    | Tuple[Literal[2], QuerySet[MvAccommodationRequest]]
    | Tuple[None, None]
):
    ars_with_guest = MvAccommodationRequest.objects.filter(
        person_id__contains=[guest.id]
    )
    ars_with_guest_count = ars_with_guest.count()

    if ars_with_guest.count() == 1:
        logger.info("AR: %s meets conditions for scenario 1", accommodation_request.id)
        return (1, None)

    closed_ars_with_guest = ars_with_guest.filter(
        status__in=MvAccommodationRequest.CLOSED_STATUSES
    )

    if (ars_with_guest_count - closed_ars_with_guest.count()) == 1:
        logger.info("AR: %s meets conditions for scenario 2", accommodation_request.id)
        return (2, closed_ars_with_guest.all())

    logger.info(
        "AR: %s does not meet the conditions for a fixable scenario",
        accommodation_request.id,
    )

    return (None, None)


def fix_guest_records_pointing_to_wrong_ars(dry_run=True):
    logger.info(
        "Start fix_guest_records_pointing_to_wrong_ars with dry_run=%s", dry_run
    )

    counts = Counter(
        scenario_1_success=0,
        scenario_1_failed=0,
        scenario_2_or_3_success=0,
        scenario_2_or_3_failed=0,
        other_scenario=0,
    )

    for accommodation_request, guest in find_records_for_each_scenario():
        scenario_number, closed_accommodation_requests = determine_scenario(
            accommodation_request, guest
        )

        counter_key = "other_scenario"

        if scenario_number == 1:
            with log_and_wrap_record_processing(
                scenario_number,
                accommodation_request,
                guest,
                closed_accommodation_requests,
            ) as result:
                if not dry_run:
                    assign_ar_to_guest(accommodation_request, guest)

            counter_key = (
                "scenario_1_success" if result["success"] else "scenario_1_failed"
            )

        elif scenario_number == 2:
            with log_and_wrap_record_processing(
                scenario_number,
                accommodation_request,
                guest,
                closed_accommodation_requests,
            ) as result:
                if not dry_run:
                    assign_ar_to_guest(accommodation_request, guest)

                    for closed_accommodation_request in closed_accommodation_requests:
                        remove_guest_from_ar(closed_accommodation_request, guest)

            counter_key = (
                "scenario_2_success" if result["success"] else "scenario_2_failed"
            )

        else:
            logger.info(
                "Skipping processing AR: %s; Guest: %s; for unfixable scenario",
                accommodation_request.id,
                guest.id,
            )

        counts[counter_key] += 1

    logger.info("End fix_guest_records_pointing_to_wrong_ars with dry_run=%s", dry_run)
    logger.info(
        "Scenario 1: %s succeeded, %s failed",
        counts["scenario_1_success"],
        counts["scenario_1_failed"],
    )
    logger.info(
        "Scenario 2: %s succeeded, %s failed",
        counts["scenario_2_success"],
        counts["scenario_2_failed"],
    )
    logger.info(
        "Other scenarios: %s skipped",
        counts["other_scenario"],
    )


def run(dry_run=True):
    """
    Usage from within ECS container:
        # Normal run (makes changes):
        python manage.py shell \
        -c "from hfurb_scripts.fix_guest_records_pointing_to_wrong_ars import run; \
        run(dry_run=False)"


        # Dry run (shows what would be changed):
        python manage.py shell \
        -c "from hfurb_scripts.fix_guest_records_pointing_to_wrong_ars import run; \
        run()"
    """

    fix_guest_records_pointing_to_wrong_ars(dry_run=dry_run)
