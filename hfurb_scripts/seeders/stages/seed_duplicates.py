import math
import random
import uuid
from copy import deepcopy

from django.utils import timezone

from hfurb_scripts.seeders.helpers import (
    add_accommodation_request_to_person,
    add_accommodation_to_sponsor,
    add_visa_application_to_person,
    create_new_accommodation_request_for_person,
    create_new_visa_application_for_person,
    fake,
)
from ontology.models import (
    MvAccommodation,
    MvPerson,
    MvVolunteer,
    VisaApplication,
)

string_case_transformations = [
    str.upper,
    str.lower,
    str.title,
    str.capitalize,
    str.swapcase,
]

phone_number_prefixes = ["+44", "07", "7"]

guest_visa_status_options = [
    "Arrived",
    "Issued",
    "Confirmed",
    "Flow Visa Pending",
    "Pending",
    "Refused",
    "Withdrawn",
    "Lapsed",
    "Missing Application",
]


def seed_duplicate_sponsors_from_existing():
    # Ignore non-editable sponsors as these are our generated
    # LA sponsors so we don't want to create dupes of them.
    all_sponsors = list(MvVolunteer.objects.filter(is_editable=True))
    total = len(all_sponsors)
    ten_percent = math.ceil(total * 0.10)
    selected_for_duplication = random.sample(all_sponsors, ten_percent)

    all_accoms = MvAccommodation.objects.filter(is_editable=True)

    for sponsor in selected_for_duplication:
        original_sponsor_accoms = sponsor.accommodations.filter(is_editable=True)

        # Create either 1 or 2 duplicates of the sponsor.
        # This mimics number of dupes of a single sponsor we tend to see in prod.
        for _ in range(random.randint(1, 2)):
            duplicate_sponsor = MvVolunteer.objects.create(
                id=f"sponsor-{uuid.uuid4()}", is_editable=True
            )

            # Common differences seen in dupes names are casing
            duplicate_sponsor.first_name = (
                random.choice(string_case_transformations)(sponsor.first_name)
                if sponsor.first_name
                else None
            )
            duplicate_sponsor.last_name = (
                random.choice(string_case_transformations)(sponsor.last_name)
                if sponsor.last_name
                else None
            )
            duplicate_sponsor.full_name = (
                f"{duplicate_sponsor.first_name} {duplicate_sponsor.last_name}"
            )

            # Common differences seen in dupes phone numbers are the prefix
            random_phone_from_sponsor = (
                random.choice(sponsor.phone_number)
                if sponsor.phone_number and len(sponsor.phone_number) > 0
                else None
            )
            duplicate_sponsor.phone_number = [
                random.choice(phone_number_prefixes) + random_phone_from_sponsor[-9:]
                if random_phone_from_sponsor
                else None
            ]

            # Date of birth and age tend to either be the same or missing between dupes
            duplicate_sponsor.date_of_birth = random.choice(
                [sponsor.date_of_birth, None]
            )
            duplicate_sponsor.age = random.choice([sponsor.age, None])

            # All other dates tend to be completely different between dupes
            duplicate_sponsor.requested_checks_latest_date = fake.date_time_between(
                start_date="-1y", end_date="now", tzinfo=timezone.get_current_timezone()
            )
            duplicate_sponsor.last_updated_date = fake.date_time_between(
                start_date="-1y", end_date="now", tzinfo=timezone.get_current_timezone()
            )

            # The following properties all tend to be the same between dupes
            duplicate_sponsor.email = sponsor.email
            duplicate_sponsor.is_principal = True
            duplicate_sponsor.sex = sponsor.sex
            duplicate_sponsor.residential_postcodes = sponsor.residential_postcodes
            duplicate_sponsor.nationality = sponsor.nationality
            duplicate_sponsor.other_nationalities = sponsor.other_nationalities
            duplicate_sponsor.flag_unsuitable = sponsor.flag_unsuitable
            duplicate_sponsor.family_situation = sponsor.family_situation
            duplicate_sponsor.hosting_duration = sponsor.hosting_duration
            duplicate_sponsor.save()

            # Dupe accoms are sometimes linked to the same sponsor, but sometimes
            # are linked to completely different ones. Randomly decide whether to
            # link to the same and/or a different sponsor.
            if original_sponsor_accoms.exists() and random.random() < 0.4:
                add_accommodation_to_sponsor(
                    duplicate_sponsor, random.choice(list(original_sponsor_accoms))
                )
            if all_accoms.exists() and random.random() < 0.6:
                add_accommodation_to_sponsor(
                    duplicate_sponsor, random.choice(list(all_accoms))
                )

    print(f"Created duplicates for {ten_percent} sponsors.")


def seed_duplicate_guests_from_existing():
    all_guests = list(MvPerson.objects.all())
    total = len(all_guests)
    ten_percent = math.ceil(total * 0.10)
    selected_for_duplication = random.sample(all_guests, ten_percent)

    for guest in selected_for_duplication:
        # Create either 1 or 2 duplicates of the guest.
        # This mimics number of dupes of a single guest we tend to see in prod.
        for _ in range(random.randint(1, 2)):
            duplicate_guest = MvPerson.objects.create(id=f"person-{uuid.uuid4()}")

            # Common differences seen in dupes names are casing
            duplicate_guest.first_name = (
                random.choice(string_case_transformations)(guest.first_name)
                if guest.first_name
                else None
            )
            duplicate_guest.last_name = (
                random.choice(string_case_transformations)(guest.last_name)
                if guest.last_name
                else None
            )
            duplicate_guest.title = (
                f"{duplicate_guest.first_name} {duplicate_guest.last_name}"
            )

            # Common differences seen in dupes phone numbers are the prefix
            random_phone_from_guest = (
                random.choice(guest.phone)
                if guest.phone and len(guest.phone) > 0
                else None
            )
            duplicate_guest.phone = [
                random.choice(phone_number_prefixes) + random_phone_from_guest[-9:]
                if random_phone_from_guest
                else None
            ]

            # Date of birth and age tend to either be the same or missing between dupes
            duplicate_guest.date_of_birth = random.choice([guest.date_of_birth, None])
            duplicate_guest.age = random.choice([guest.age, None])

            # Visa statuses can differ between duped guests
            duplicate_guest.visa_status = random.choice(guest_visa_status_options)

            # The following properties all tend to be the same or missing between dupes
            duplicate_guest.email = guest.email
            duplicate_guest.is_principal = True
            duplicate_guest.gender = guest.gender
            duplicate_guest.nationality = guest.nationality
            duplicate_guest.passport_id = random.choice([guest.passport_id, None])
            duplicate_guest.upe_visa_status = guest.upe_visa_status
            duplicate_guest.accommodation_request = None
            duplicate_guest.save()

            # Dupe guests are sometimes linked to the same AR, but sometimes
            # are linked to different ARs. Randomly decide whether to
            # link to the same or a different AR, or no AR at all.
            if guest.accommodation_request and random.random() < 0.4:
                add_accommodation_request_to_person(
                    duplicate_guest, guest.accommodation_request
                )
            elif random.random() < 0.6:
                create_new_accommodation_request_for_person(duplicate_guest)

            # Dupe guests are sometimes linked to the same visa application, but
            # sometimes are linked to different visa applications. Randomly decide
            # whether to link to the same,different, or no visa application at all.
            if (
                guest.application_number
                and len(guest.application_number) > 0
                and random.random() < 0.4
            ):
                visa_application = VisaApplication.objects.filter(
                    visa_application_id=random.choice(guest.application_number)
                )
                if visa_application.exists():
                    add_visa_application_to_person(
                        duplicate_guest, visa_application.first()
                    )
            if random.random() < 0.6:
                create_new_visa_application_for_person(duplicate_guest)

    print(f"Created duplicates for {ten_percent} guests.")


def seed_duplicate_accommodations_from_existing():
    # Ignore non-editable accommodations as these are our generated
    # LA accommodations so we don't want to create dupes of them.
    all_accommodations = list(MvAccommodation.objects.filter(is_editable=True))
    total = len(all_accommodations)
    ten_percent = math.ceil(total * 0.10)
    selected_for_duplication = random.sample(all_accommodations, ten_percent)

    all_sponsors = MvVolunteer.objects.filter(is_editable=True)

    for accom in selected_for_duplication:
        original_accom_sponsors = accom.hosts.filter(is_editable=True)

        # Create either 1 or 2 duplicates of the accommodation.
        # This mimics number of dupes of a single accom we tend to see in prod.
        for _ in range(random.randint(1, 2)):
            duplicate_accom = MvAccommodation.objects.create(
                id=f"accommodation-{uuid.uuid4()}", is_editable=True
            )

            # Common differences seen in dupes addresses/postcodes are casing
            duplicate_accom.full_address = (
                random.choice(string_case_transformations)(accom.full_address)
                if accom.full_address
                else None
            )
            if accom.postcode:
                duplicate_postcode = deepcopy(accom.postcode)
                duplicate_postcode.postcode_formatted = (
                    random.choice(string_case_transformations)(
                        accom.postcode.postcode_formatted
                    )
                    if accom.postcode.postcode_formatted
                    else None
                )
                duplicate_postcode.save()
                duplicate_accom.postcode = duplicate_postcode

            # The following properties all tend to be the same or missing between dupes
            duplicate_accom.ltla_name = accom.ltla_name
            duplicate_accom.utla_name = accom.utla_name
            duplicate_accom.country = random.choice([accom.country, None])
            duplicate_accom.is_principal = True
            duplicate_accom.accommodation_type = accom.accommodation_type
            duplicate_accom.is_accommodation = accom.is_accommodation
            duplicate_accom.is_available_for_rematch = accom.is_available_for_rematch
            duplicate_accom.is_eoi = accom.is_eoi
            duplicate_accom.save()

            # Dupe accoms are sometimes linked to the same sponsor, but sometimes
            # are linked to completely different ones. Randomly decide whether to
            # link to the same and/or a different sponsor.
            if original_accom_sponsors.exists() and random.random() < 0.4:
                add_accommodation_to_sponsor(
                    random.choice(list(original_accom_sponsors)), duplicate_accom
                )
            if all_sponsors.exists() and random.random() < 0.6:
                add_accommodation_to_sponsor(
                    random.choice(list(all_sponsors)), duplicate_accom
                )

    print(f"Created duplicates for {ten_percent} accommodations.")


def seed_duplicates():
    seed_duplicate_sponsors_from_existing()
    seed_duplicate_guests_from_existing()
    seed_duplicate_accommodations_from_existing()
