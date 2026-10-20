from datetime import datetime

from ontology.models import (
    MvAccommodation,
    MvUkPostcode,
)


def _get_record_date_of_birth(principle_record):
    if principle_record["date_of_birth"]:
        date_of_birth_str = principle_record["date_of_birth"].split(" (")[0]
        return datetime.strptime(date_of_birth_str, "%d %B %Y").date()

    return None


def _get_record_name(principle_record, use_full_name):
    if use_full_name:
        return {
            "full_name": (
                f"{principle_record['first_name']} {principle_record['last_name']}"
            )
        }
    return {
        "first_name": principle_record["first_name"],
        "last_name": principle_record["last_name"],
    }


def build_principle_guest_record(principle_guest, *, use_full_name=False):
    return {
        **_get_record_name(principle_guest, use_full_name),
        "gender": principle_guest["sex"],
        "date_of_birth": _get_record_date_of_birth(principle_guest),
        "email": principle_guest["email_address"],
        "phone": principle_guest["phone_numbers"],
        "passport_id": principle_guest["passport_number"],
        "visa_status": principle_guest["visa_status"],
        "application_number": principle_guest["application_numbers"],
    }


def build_principle_sponsor_record(principle_sponsor, *, use_full_name=False):
    return {
        **_get_record_name(principle_sponsor, use_full_name),
        "sex": principle_sponsor["sex"],
        "date_of_birth": _get_record_date_of_birth(principle_sponsor),
        "email": principle_sponsor["email_address"],
        "phone_number": principle_sponsor["phone_numbers"],
        "residential_postcodes": principle_sponsor["residential_postcodes"],
        "flag_unsuitable": False,
    }


def build_principle_accommodation_record(principle_accommodation):
    return {
        "full_address": MvAccommodation.objects.only("full_address", "postcode")
        .get(id=principle_accommodation["full_address"])
        .full_address,
        "postcode": (
            MvUkPostcode.objects.get(id=principle_accommodation["postcode"])
            if principle_accommodation["postcode"]
            else None
        ),
        "ltla_name": principle_accommodation["ltla_name"],
        "utla_name": principle_accommodation["utla_name"],
    }
