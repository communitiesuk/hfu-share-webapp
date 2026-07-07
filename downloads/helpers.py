import datetime
from typing import Iterable, Type

from django.db import models

from downloads.constants import (
    ACCOMMODATION_FIELDS,
    DOWNLOAD_ALL_COLUMN_ORDERING,
    DOWNLOAD_UAMS_COLUMN_ORDERING,
    REMATCHED_HOST_FIELDS,
    SPONSOR_FIELDS,
)
from downloads.forms import DownloadType


def build_csv_header(
    export_model: Type[models.Model],
    download_type: DownloadType,
) -> list[str]:
    field_names = []

    model_fields = export_model._meta.fields
    for field in model_fields:
        field_names.append(field.name)

        if field.name == "created_at":
            # `created_at` field adds an extra column for timezone
            field_names.append("created_at_tz")

    column_order = None
    match download_type:
        case DownloadType.ALL:
            column_order = DOWNLOAD_ALL_COLUMN_ORDERING
        case DownloadType.UAMS:
            column_order = DOWNLOAD_UAMS_COLUMN_ORDERING

    if column_order is not None:
        field_names_available = set(field_names)
        field_names = []
        for ordered_field in column_order:
            if ordered_field in field_names_available:
                field_names.append(ordered_field)

    return field_names


def build_csv_row(
    model_object: Type[models.Model],
    field_names: list[str],
    redacted_fields: set[str] | None,
) -> list[str]:
    row = []
    for field in field_names:
        if field == "created_at_tz":
            # Skip timezone column will be set by `created_at`
            continue

        model_field = model_object._meta.get_field(field)

        if redacted_fields and field in redacted_fields:
            row.append("")
        elif isinstance(model_field, models.ForeignKey):
            # For FK fields, this is how we get around making an extra query
            fk_field = getattr(model_object, f"{field}_id")
            row.append(fk_field if fk_field is not None else "")
        else:
            value = getattr(model_object, field)

            if field == "created_at":
                # `created_at` field adds an extra column for timezone
                if isinstance(value, datetime.datetime):
                    row.append(value.strftime("%Y-%m-%d %H:%M:%S"))
                    row.append(value.tzname() or "")
                else:
                    row.append("")
                    row.append("")
                continue

            row.append(str(value) if value is not None else "")

    return row


def does_user_la_match_record(user_las: set[str], record_las: Iterable[str]):
    """
    Return True if the user's local-authority names overlap the record's names.

    Args:
        user_las: The user's LTLA/UTLA names as a set of strings.
        record_las: An iterable of LTLA/UTLA names on the record.

    Returns:
        bool: True if at least one element is common to both; otherwise False.
    """
    return bool(user_las.intersection(record_las)) if record_las else False


def can_user_view_record(
    user_ltlas: set[str],
    user_utlas: set[str],
    record_ltlas: Iterable[str],
    record_utlas: Iterable[str],
):
    """
    Decide if a user may view a record based on LA overlap.

    A user can view the record if ANY of the following holds:
      1) Their LTLA set matches at least one of the record's LTLAs, OR
      2) Their UTLA set matches at least one of the record's UTLAs, OR
      3) The record has neither LTLAs nor UTLAs

    Args:
        user_ltlas: User's LTLA names.
        user_utlas: User's UTLA names.
        record_ltlas: Record's LTLA names
        record_utlas: Record's UTLA names

    Returns:
        bool: True if the user can view per the above rule; otherwise False.
    """
    return any(
        [
            does_user_la_match_record(user_ltlas, record_ltlas),
            does_user_la_match_record(user_utlas, record_utlas),
            (not record_ltlas and not record_utlas),
        ]
    )


def determine_redacted_fields(
    model_object,
    ltla_names: set[str],
    utla_names: set[str],
):
    """
    Compute which field groups must be redacted for a record.

    For each section (Sponsor, Rematched Host, Accommodation), if the user
    cannot view that section per `can_user_view_record(...)`, add the
    corresponding constant to the redaction set.

    Args:
        model_object: An object exposing the following attributes:
            - sponsor_ltla_name, sponsor_utla_name
            - rematched_host_ltla_name, rematched_host_utla_name
            - accommodation_ltla_name, accommodation_utla_name
          Each is expected to be an iterable of strings (or falsy if absent).
        ltla_names: The user's LTLA names.
        utla_names: The user's UTLA names.

    Returns:
        set[str]: Union of fields to redact, drawn from:
            - SPONSOR_FIELDS
            - REMATCHED_HOST_FIELDS
            - ACCOMMODATION_FIELDS
    """
    redacted_fields = set()

    if not can_user_view_record(
        ltla_names,
        utla_names,
        model_object.sponsor_ltla_name,
        model_object.sponsor_utla_name,
    ):
        redacted_fields.update(SPONSOR_FIELDS)

    if not can_user_view_record(
        ltla_names,
        utla_names,
        model_object.rematched_host_ltla_name,
        model_object.rematched_host_utla_name,
    ):
        redacted_fields.update(REMATCHED_HOST_FIELDS)

    if not can_user_view_record(
        ltla_names,
        utla_names,
        model_object.accommodation_ltla_name,
        model_object.accommodation_utla_name,
    ):
        redacted_fields.update(ACCOMMODATION_FIELDS)

    return redacted_fields
