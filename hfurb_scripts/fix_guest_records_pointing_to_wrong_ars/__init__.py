import logging
import os
import sys
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

import django
from django.db import DatabaseError, transaction
from dotenv import load_dotenv

from ontology.models import MvAccommodationRequest, MvPerson

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "case_management.settings")
django.setup()

logger = logging.getLogger(__name__)


# This is needed because ChecksStatus.CLOSED_LEFT_PROGRAMME is slightly different
# as although it is Closed, it can be reopened
CLOSED_STATUSES = (
    MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE,
    MvAccommodationRequest.ChecksStatus.CANCELLED,
    MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY,
)


@contextmanager
def log_and_wrap_record_processing(
    scenario_number: int,
    accommodation_request: MvAccommodationRequest,
    guest: MvPerson,
    dry_run: bool = True,
):
    result = {"success": True}

    try:
        with transaction.atomic():
            yield result
            logger.info(
                "Processed AR: %s and Guest: %s for scenario %s",
                accommodation_request.id,
                guest.id,
                scenario_number,
            )
            if dry_run:
                transaction.set_rollback(True)

    except DatabaseError as exc:
        logger.exception(
            "Exception processing AR: %s and Guest: %s for scenario %s; error: %s",
            accommodation_request.id,
            guest.id,
            scenario_number,
            exc,
        )
        result["success"] = False


def assign_ar_to_guest(accommodation_request: MvAccommodationRequest, guest: MvPerson):
    guest.accommodation_request_id = accommodation_request.id  # type: ignore[attr-defined]
    guest.save()


# It was decided that we would not remove th guest from any ARs at this current time
# but I am leaving this here to show how would do it if we were
def remove_guest_from_ar(
    accommodation_request: MvAccommodationRequest, guest: MvPerson
):
    accommodation_request.person_id.remove(guest.id)
    accommodation_request.save()


# This method returns only ARs which are open and
# the guest they are linked to but the guest is not linked to them
def find_records_for_each_scenario():
    openable_ars = MvAccommodationRequest.objects.exclude(
        checks_status__in=CLOSED_STATUSES,
    )

    for ar in openable_ars.iterator():
        for guest in MvPerson.objects.filter(id__in=ar.person_id or []):
            if str(guest.accommodation_request_id) != str(ar.id):
                yield ar, guest


# Here are the different scenarios we want to fix:
# 1) the AR has the Guest ID but the Guest has an ID for an AR which
#    does not contain that Guest
# 2) an open and a permanently closed AR has the guest ID but
#    the Guest has the ID for the AR that is closed
# 3) an open and a permanently closed AR has the guest ID but
#    the Guest has an ID for an AR which does not contain that Guest
def determine_scenario(
    guest: MvPerson,
) -> Literal[1] | Literal[2] | None:
    ars_with_guest = MvAccommodationRequest.objects.filter(
        person_id__contains=[guest.id]
    )
    ars_with_guest_count = ars_with_guest.count()

    # If the guest is only on one AR then we know it's scenario 1 becuase we
    # know that the guest is attached to the open AR that is passed into this method
    # so by the count being 1 we know they are not attched to any other ARs
    if ars_with_guest.count() == 1:
        return 1

    closed_ars_with_guest = ars_with_guest.filter(checks_status__in=CLOSED_STATUSES)

    # If they are attached to other ARs but they're only attached one open then
    # this is scenario 2/3 and they can be attached to the correct AR
    if (ars_with_guest_count - closed_ars_with_guest.count()) == 1:
        return 2

    # If they are attached to more than one open AR then we can't be sure how to fix it
    # so we have to skip it

    return None


def percentage(count: int, total: int) -> float:
    return count / total * 100 if total else 0.0


def log_scenario_stats(scenario_number: int, counts: Counter):
    success_score = counts[f"scenario_{scenario_number}_success"]
    failed_score = counts[f"scenario_{scenario_number}_failed"]

    scenario_total = success_score + failed_score

    success_pct = percentage(success_score, scenario_total)
    failed_pct = percentage(failed_score, scenario_total)

    logger.info(
        "Scenario %s: %s succeeded (%.1f%%), %s failed (%.1f%%)",
        scenario_number,
        success_score,
        success_pct,
        failed_score,
        failed_pct,
    )


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
        scenario_number = determine_scenario(guest)

        counter_key = "other_scenario"

        if scenario_number == 1 or scenario_number == 2:
            with log_and_wrap_record_processing(
                scenario_number,
                accommodation_request,
                guest,
                dry_run=dry_run,
            ) as result:
                assign_ar_to_guest(accommodation_request, guest)

            counter_key = (
                f"scenario_{scenario_number}_success"
                if result["success"]
                else f"scenario_{scenario_number}_failed"
            )

        else:
            logger.info(
                "Skipping processing AR: %s and Guest: %s for unfixable scenario",
                accommodation_request.id,
                guest.id,
            )

        counts[counter_key] += 1

    logger.info("End fix_guest_records_pointing_to_wrong_ars with dry_run=%s", dry_run)
    logger.info("Inspected %s records", counts.total())

    log_scenario_stats(1, counts)
    log_scenario_stats(2, counts)

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
