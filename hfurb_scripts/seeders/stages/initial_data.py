import os
import random
from random import choices

from django.db import transaction

from hfurb_scripts.seeders.constants import ALL_LTLA_NAMES, VISA_STATUS_LIST
from hfurb_scripts.seeders.helpers import build_complete_accommodation_scenario
from hfurb_scripts.seeders.mutators import (
    mutate_checks,
    mutate_closed_left_programme,
    mutate_rematch_required,
)
from ontology.models import MvAccommodationRequest

SEEDING_COUNT = int(os.environ.get("SEEDING_COUNT", 250))


def seed_initial_data():
    # Define weights for number of guests (favoring 1)
    guest_numbers = [1, 2, 3, 4, 5, 6]
    guest_weights = [50, 20, 15, 10, 3, 2]  # Heavily weighted towards 1 guest

    # Define favored visa statuses with weights
    favored_visa_statuses = ["Arrived", "Issued", "Confirmed", "Pending"]
    other_visa_statuses = [
        status for status in VISA_STATUS_LIST if status not in favored_visa_statuses
    ]
    all_visa_statuses = favored_visa_statuses * 10 + other_visa_statuses

    # Choose random check statuses from AR.ChecksStatus
    checks_statuses = {
        MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED: 50,
        MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED: 20,
        MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED: 10,
        MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED: 9,
        MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME: 5,
        MvAccommodationRequest.ChecksStatus.CANCELLED: 1,
        MvAccommodationRequest.ChecksStatus.REMATCH_REQUIRED: 5,
    }

    with transaction.atomic():
        for i in range(SEEDING_COUNT):
            # Randomly select parameters
            num_guests = choices(guest_numbers, weights=guest_weights)[0]
            ltla_name = random.choice(ALL_LTLA_NAMES)

            # Generate individual visa statuses for each guest
            visa_statuses = [
                random.choice(all_visa_statuses) for _ in range(num_guests)
            ]

            # Randomly select checks status
            checks_status = choices(
                list(checks_statuses.keys()), weights=list(checks_statuses.values())
            )[0]

            # Create accommodation request
            ar = build_complete_accommodation_scenario(
                num_guests=num_guests,
                ltla_name=ltla_name,
                visa_statuses=visa_statuses,
                checks_status=checks_status,
            )

            # Mutate the accommodation request
            match ar.checks_status:
                case MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME:
                    mutate_closed_left_programme(ar)
                case MvAccommodationRequest.ChecksStatus.REMATCH_REQUIRED:
                    mutate_rematch_required(ar)
                case MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED:
                    mutate_checks(ar)
                case MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED:
                    mutate_checks(ar)
                case MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED:
                    mutate_checks(ar)

            uam_text = (
                "(UAM)" if ar.sponsorship_certification_number_id is not None else ""
            )

            print(f"{i}: AccommodationRequests[{ar.checks_status}] {uam_text}")

    print(f"Successfully seeded {SEEDING_COUNT} AccommodationRequest objects.")
