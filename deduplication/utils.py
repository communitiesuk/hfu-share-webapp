from datetime import datetime

from ontology.models import (
    MvAccommodation,
    MvUkPostcode,
)


def _get_record_date_of_birth(principal_record):
    if principal_record["date_of_birth"]:
        date_of_birth_str = principal_record["date_of_birth"].split(" (")[0]
        return datetime.strptime(date_of_birth_str, "%d %B %Y").date()

    return None


def _get_record_name(principal_record, use_full_name):
    if use_full_name:
        return {
            "full_name": (
                f"{principal_record['first_name']} {principal_record['last_name']}"
            )
        }
    return {
        "first_name": principal_record["first_name"],
        "last_name": principal_record["last_name"],
    }


def build_principal_guest_record(principal_guest, *, use_full_name=False):
    return {
        **_get_record_name(principal_guest, use_full_name),
        "gender": principal_guest["sex"],
        "date_of_birth": _get_record_date_of_birth(principal_guest),
        "email": principal_guest["email_address"],
        "phone": principal_guest["phone_numbers"],
        "passport_id": principal_guest["passport_number"],
        "visa_status": principal_guest["visa_status"],
        "application_number": principal_guest["application_numbers"],
    }


def build_principal_sponsor_record(principal_sponsor, *, use_full_name=False):
    return {
        **_get_record_name(principal_sponsor, use_full_name),
        "sex": principal_sponsor["sex"],
        "date_of_birth": _get_record_date_of_birth(principal_sponsor),
        "email": principal_sponsor["email_address"],
        "phone_number": principal_sponsor["phone_numbers"],
        "residential_postcodes": principal_sponsor["residential_postcodes"],
        "flag_unsuitable": False,
    }


def build_principal_accommodation_record(principal_accommodation):
    return {
        "full_address": MvAccommodation.objects.only("full_address", "postcode")
        .get(id=principal_accommodation["full_address"])
        .full_address,
        "postcode": (
            MvUkPostcode.objects.get(id=principal_accommodation["postcode"])
            if principal_accommodation["postcode"]
            else None
        ),
        "ltla_name": principal_accommodation["ltla_name"],
        "utla_name": principal_accommodation["utla_name"],
    }
