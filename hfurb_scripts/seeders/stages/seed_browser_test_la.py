import json
import os
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast
from unittest import mock

from django.apps import apps
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import AutoField
from django.utils import timezone
from faker import Faker
from freezegun import freeze_time

from accounts.enums import BROWSER_TEST_LTLA_NAMES
from accounts.models import User
from deduplication.models import (
    GuestDuplicateGroup,
    SponsorDuplicateGroup,
)
from hfurb_scripts.browser_test_seed.loader import (
    USER_EMAIL_PLACEHOLDER,
    USER_FULL_NAME_PLACEHOLDER,
    USER_PK_PLACEHOLDER,
    USER_USERNAME_PLACEHOLDER,
    browser_test_seeding_allowed,
    get_browser_test_author,
)
from hfurb_scripts.browser_test_seed.records import (
    BROWSER_TEST_ID_PREFIX,
    SEED_DATA_DIR,
    collect_browser_test_records,
    wipe_browser_test_la_data,
)
from hfurb_scripts.seeders.helpers import (
    add_accommodation_to_sponsor,
    build_complete_accommodation_scenario,
    create_export_tool_object,
    create_mv_accommodation,
    create_mv_person,
    create_mv_sponsor,
    create_visa_application,
    get_group_info_from_ltla,
    next_serial,
    record_id,
    reset_record_id_counters,
)
from hfurb_scripts.seeders.mutators import (
    mutate_checks,
    mutate_closed_left_programme,
    mutate_rematch_required,
)
from ontology.models import (
    Comment,
    MvAccommodation,
    MvAccommodationRequest,
    MvInteraction,
    MvPerson,
    ReassignmentRequest,
    SafeguardingNotification,
    SafeguardingReferral,
    VisaApplication,
    VisaInformationRequest,
    VisaInformationRequestComments,
)
from ontology.tests.factories import CommentFactory

BROWSER_TEST_SEED = int(os.environ.get("BROWSER_TEST_SEED", 1313))
BROWSER_TEST_REFERENCE_DATETIME = datetime(2025, 1, 1, 12, 0, 0)
MULTI_LA_SECOND_LTLA = "Isles of Scilly"


ChecksStatus = MvAccommodationRequest.ChecksStatus
Status = MvAccommodationRequest.Status
AccommodationType = MvAccommodation.AccommodationType

# one entry per seeded accommodation request; every checks status and AR
# status must appear at least once
AR_SCENARIOS: list[dict] = [
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Arrived"],
        "case_comments": True,
    },
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Arrived", "Issued"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_PARTIALLY_COMPLETED,
        "visa_statuses": ["Confirmed", "Arrived", "Pending"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_COMPLETED,
        "visa_statuses": ["Arrived"],
        "case_comments": True,
    },
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Issued", "Refused"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Arrived", "Confirmed", "Withdrawn"],
    },
    {"checks_status": ChecksStatus.SOME_CHECKS_FAILED, "visa_statuses": ["Arrived"]},
    {
        "checks_status": ChecksStatus.CHECKS_COMPLETED,
        "visa_statuses": ["Pending", "Lapsed"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Arrived", "Arrived", "Arrived"],
    },
    {"checks_status": ChecksStatus.CLOSED_LEFT_PROGRAMME, "visa_statuses": ["Issued"]},
    {
        "checks_status": ChecksStatus.CHECKS_PARTIALLY_COMPLETED,
        "visa_statuses": ["Confirmed", "Arrived"],
        "case_comments": True,
    },
    {
        "checks_status": ChecksStatus.CHECKS_COMPLETED,
        "visa_statuses": ["Pending", "Arrived", "Issued"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Refused"],
        "make_uam": True,
    },
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Arrived", "Confirmed"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_PARTIALLY_COMPLETED,
        "visa_statuses": ["Withdrawn", "Arrived", "Pending"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_COMPLETED,
        "visa_statuses": ["Lapsed"],
        "pending_reassignment": True,
        "label": "pending outbound reassignment",
    },
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Arrived", "Arrived"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Arrived", "Issued", "Confirmed"],
    },
    {"checks_status": ChecksStatus.CLOSED_DUPLICATE, "visa_statuses": ["Arrived"]},
    {
        "checks_status": ChecksStatus.CHECKS_COMPLETED,
        "visa_statuses": ["Pending", "Arrived"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Issued", "Refused", "Arrived"],
        "label": "receives guests from closed empty",
    },
    {
        "checks_status": ChecksStatus.CLOSED_EMPTY,
        "visa_statuses": ["Confirmed"],
        "label": "closed empty",
    },
    {
        "checks_status": ChecksStatus.CHECKS_PARTIALLY_COMPLETED,
        "visa_statuses": ["Withdrawn", "Arrived"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_COMPLETED,
        "visa_statuses": ["Pending", "Lapsed", "Arrived"],
    },
    {"checks_status": ChecksStatus.CANCELLED, "visa_statuses": ["Arrived"]},
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Arrived", "Issued"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_PARTIALLY_COMPLETED,
        "visa_statuses": ["Confirmed", "Arrived", "Pending"],
    },
    {
        "checks_status": ChecksStatus.IN_TEMPORARY_ACCOMMODATION,
        "visa_statuses": ["Arrived"],
        "accommodation_type": AccommodationType.TEMPORARY_ACCOMMODATION,
    },
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Issued", "Refused"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Arrived", "Confirmed", "Withdrawn"],
    },
    {
        "checks_status": ChecksStatus.PRE_ARRIVAL_CHECKS_COMPLETE,
        "visa_statuses": ["Arrived"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_COMPLETED,
        "visa_statuses": ["Pending", "Lapsed"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Arrived", "Arrived", "Arrived"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Issued"],
        "ar_status": Status.MISSING_ACCOMMODATION,
    },
    {
        "checks_status": ChecksStatus.CHECKS_PARTIALLY_COMPLETED,
        "visa_statuses": ["Confirmed", "Arrived"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_COMPLETED,
        "visa_statuses": ["Pending", "Arrived", "Issued"],
    },
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Refused"],
        "ar_status": Status.ARRIVAL_CONFIRMED,
        "make_uam": True,
    },
    {
        "checks_status": ChecksStatus.CHECKS_REQUIRED,
        "visa_statuses": ["Arrived", "Confirmed"],
        "label": "multi-LA sponsor",
    },
    {
        "checks_status": ChecksStatus.CHECKS_PARTIALLY_COMPLETED,
        "visa_statuses": ["Withdrawn", "Arrived", "Pending"],
        "label": "rejected outbound reassignment",
    },
    {
        "checks_status": ChecksStatus.CHECKS_COMPLETED,
        "visa_statuses": ["Lapsed"],
        "label": "multi-LA AR",
    },
]

CASE_COMMENTS = [
    "Called the sponsor to confirm the guests arrived safely.",
    "Property visit booked, sponsor available Tuesday morning.",
    "Guest asked about school places for the youngest child, referred to admissions.",
    "DBS certificate received for the second adult in the household.",
    "Sponsor reported a delay getting the spare room ready, follow up in two weeks.",
    "Spoke with the guest about GP registration, forms sent by email.",
]

# seeded comments must all be dated before 21 September 2025
CASE_COMMENT_DATES = [
    datetime(2025, 6, 12, 10, 30),
    datetime(2025, 7, 3, 14, 5),
    datetime(2025, 7, 24, 9, 15),
    datetime(2025, 8, 14, 16, 40),
    datetime(2025, 9, 2, 11, 20),
    datetime(2025, 9, 19, 15, 55),
]


def _labelled_ar(
    ars: list[MvAccommodationRequest], label: str
) -> MvAccommodationRequest:
    for index, scenario in enumerate(AR_SCENARIOS):
        if scenario.get("label") == label:
            return ars[index]
    raise ValueError(f"no scenario labelled {label!r}")


def _make_multi_la_accommodation_request(ar: MvAccommodationRequest) -> str:
    second_accommodation = create_mv_accommodation(
        MULTI_LA_SECOND_LTLA, id_prefix=BROWSER_TEST_ID_PREFIX
    )
    second_sponsor = create_mv_sponsor(id_prefix=BROWSER_TEST_ID_PREFIX)
    add_accommodation_to_sponsor(second_sponsor, second_accommodation)

    new_uan = f"1313-0000-{next_serial(f'{BROWSER_TEST_ID_PREFIX}-uan'):08d}"
    ar.accommodation_id = ar.accommodation_id + [second_accommodation.id]
    ar.sponsor_id = ar.sponsor_id + [second_sponsor.id]
    ar.ltla_name = ar.ltla_name + [MULTI_LA_SECOND_LTLA]
    if second_accommodation.utla_name:
        ar.utla_name = (ar.utla_name or []) + [second_accommodation.utla_name]
    ar.unique_application_number = ar.unique_application_number + [new_uan]
    ar.save()

    for person in MvPerson.objects.filter(accommodation_request=ar):
        visa_application = create_visa_application(
            person,
            second_sponsor,
            second_accommodation,
            ar,
            visa_status="Pending",
            id_prefix=BROWSER_TEST_ID_PREFIX,
            application_unique_application_number=new_uan,
        )
        person.application_number = (person.application_number or []) + [
            visa_application.application_unique_application_number
        ]
        person.save()

    print(f"multi-LA AR: {ar.id} extended into {MULTI_LA_SECOND_LTLA}")
    return ar.id


def _make_multi_la_sponsor(ar: MvAccommodationRequest) -> str:
    extra_accommodation = create_mv_accommodation(
        MULTI_LA_SECOND_LTLA, id_prefix=BROWSER_TEST_ID_PREFIX
    )
    add_accommodation_to_sponsor(ar.primary_sponsor, extra_accommodation)
    print(
        f"multi-LA sponsor: {ar.primary_sponsor.id} "
        f"owns property in {MULTI_LA_SECOND_LTLA}"
    )
    return ar.primary_sponsor.id


def _make_inbound_reassignment(author: User) -> str:
    ar = build_complete_accommodation_scenario(
        num_guests=1,
        ltla_name=MULTI_LA_SECOND_LTLA,
        checks_status=MvAccommodationRequest.ChecksStatus.REMATCH_REQUIRED,
        id_prefix=BROWSER_TEST_ID_PREFIX,
        make_uam=False,
    )
    mutate_rematch_required(
        ar,
        destination_ltla_name=BROWSER_TEST_LTLA_NAMES[0],
        approve=True,
        author=author,
        reason="Sponsorship placement broke down",
    )
    print(
        f"inbound reassignment: {ar.id} moved from "
        f"{MULTI_LA_SECOND_LTLA} to {BROWSER_TEST_LTLA_NAMES[0]}"
    )
    return ar.id


def _make_rejected_outbound_reassignment(ar: MvAccommodationRequest) -> str:
    destination = get_group_info_from_ltla(MULTI_LA_SECOND_LTLA)
    reassignment_request = ReassignmentRequest(
        id=record_id("rr", BROWSER_TEST_ID_PREFIX),
        accommodation_request=ar,
        outcome=ReassignmentRequest.Outcome.REJECTED,
        reason="Guests unknown to local authority",
        proposed_by_country="England",
        accommodation_request_title=ar.title,
        destination_country=destination.da_name if destination else "England",
        destination_ltla_name=(
            destination.ltla_name if destination else MULTI_LA_SECOND_LTLA
        ),
        destination_utla_code=destination.utla_gss_code if destination else None,
        destination_utla_name=destination.utla_name if destination else None,
        source_ltla_name=ar.ltla_name,
        source_utla_name=ar.utla_name,
    )
    reassignment_request.save()
    reassignment_request.guests.set(ar.get_people())
    print(f"rejected outbound reassignment on {ar.id}")
    return ar.id


def _make_deduplicated_guest_pair(author: User) -> str:
    ar = build_complete_accommodation_scenario(
        num_guests=1,
        ltla_name=BROWSER_TEST_LTLA_NAMES[0],
        id_prefix=BROWSER_TEST_ID_PREFIX,
        make_uam=False,
    )
    original = MvPerson.objects.get(accommodation_request=ar)

    duplicate = create_mv_person(id_prefix=BROWSER_TEST_ID_PREFIX)
    duplicate.first_name = original.first_name
    duplicate.last_name = (original.last_name or "").upper()
    duplicate.date_of_birth = original.date_of_birth
    duplicate.age = original.age
    duplicate.passport_id = original.passport_id
    duplicate.save()

    group = GuestDuplicateGroup.objects.create()
    group.guests.set([original, duplicate])
    group.deduplicate(
        {
            "first_name": original.first_name,
            "last_name": original.last_name,
            "email": original.email,
            "phone": original.phone,
            "gender": original.gender,
            "age": original.age,
            "date_of_birth": original.date_of_birth,
            "passport_id": original.passport_id,
            "visa_status": original.visa_status,
            "upe_visa_status": original.upe_visa_status,
            "accommodation_request": ar,
        },
        user=author,
    )
    print(f"deduplicated guest pair on {ar.id}")
    return ar.id


def _make_deduplicated_sponsor_pair(author: User) -> str:
    ar = build_complete_accommodation_scenario(
        num_guests=1,
        ltla_name=BROWSER_TEST_LTLA_NAMES[0],
        id_prefix=BROWSER_TEST_ID_PREFIX,
        make_uam=False,
    )
    original = ar.primary_sponsor

    duplicate = create_mv_sponsor(id_prefix=BROWSER_TEST_ID_PREFIX)
    duplicate.first_name = original.first_name
    duplicate.last_name = (original.last_name or "").lower()
    duplicate.full_name = f"{duplicate.first_name} {duplicate.last_name}"
    duplicate.email = original.email
    duplicate.date_of_birth = original.date_of_birth
    duplicate.age = original.age
    duplicate.save()

    group = SponsorDuplicateGroup.objects.create()
    group.sponsors.set([original, duplicate])
    group.deduplicate(
        {
            "first_name": original.first_name,
            "last_name": original.last_name,
            "full_name": original.full_name,
            "email": original.email,
            "phone_number": original.phone_number,
            "sex": original.sex,
            "age": original.age,
            "date_of_birth": original.date_of_birth,
            "sponsor_type": original.sponsor_type,
        },
        user=author,
    )
    print(f"deduplicated sponsor pair on {ar.id}")
    return ar.id


def _make_visa_information_requests(author: User) -> dict[str, str]:
    ltla_name = BROWSER_TEST_LTLA_NAMES[0]
    visa_applications = list(
        VisaApplication.objects.filter(ltla_name=ltla_name).order_by(
            "visa_application_id"
        )[:3]
    )

    conversations = [
        (
            "VIR awaiting LA",
            VisaInformationRequest.RequestStatus.AWAITING_LA,
            [
                (
                    "UKVI",
                    "Please confirm whether this guest is still residing at "
                    "the sponsor's address.",
                ),
            ],
        ),
        (
            "VIR awaiting UKVI",
            VisaInformationRequest.RequestStatus.AWAITING_UKVI,
            [
                (
                    "UKVI",
                    "Please confirm the guest's arrival date for this application.",
                ),
                (
                    ltla_name,
                    "Guest arrived on the date recorded, confirmed with the sponsor.",
                ),
            ],
        ),
        (
            "VIR closed",
            VisaInformationRequest.RequestStatus.CLOSED,
            [
                (
                    "UKVI",
                    "Please confirm whether the guests are known to your authority.",
                ),
                (
                    ltla_name,
                    "Guests are known and receiving support from our team.",
                ),
                ("UKVI", "Thank you, closing this request."),
            ],
        ),
    ]

    examples = {}
    for index, (label, final_status, messages) in enumerate(conversations):
        visa_application = visa_applications[index]
        created_at = timezone.make_aware(datetime(2026, 7, 6 + index, 9, 0))

        vir = VisaInformationRequest.objects.create(
            visa_information_request_id=record_id("vir", BROWSER_TEST_ID_PREFIX),
            visa_application=visa_application,
            ltla_name=ltla_name,
            request_type=VisaInformationRequest.RequestType.GENERAL,
            request_title=(
                f"Visa information request for {visa_application.Q44g_full_name}"
            ),
            request_details=messages[0][1],
            request_status=VisaInformationRequest.RequestStatus.AWAITING_LA,
            created_at=created_at,
            requested_at=created_at,
            created_by="browser-test-ukvi",
        )

        status = VisaInformationRequest.RequestStatus.AWAITING_LA
        for message_index, (sender, text) in enumerate(messages):
            previous_status = status
            if sender == "UKVI":
                status = VisaInformationRequest.RequestStatus.AWAITING_LA
                created_by_uid = "browser-test-ukvi"
            else:
                status = VisaInformationRequest.RequestStatus.AWAITING_UKVI
                created_by_uid = author.username

            VisaInformationRequestComments.objects.create(
                id=record_id("vir-comment", BROWSER_TEST_ID_PREFIX),
                visa_information_request=vir,
                comment=text,
                created_at=created_at + timedelta(hours=message_index + 1),
                created_by_uid=created_by_uid,
                display_name="UKVI" if sender == "UKVI" else ltla_name,
                previous_status=previous_status,
                current_status=status,
            )

        vir.request_status = final_status
        if final_status == VisaInformationRequest.RequestStatus.CLOSED:
            vir.closed_at = created_at + timedelta(hours=len(messages) + 1)
        vir.save()

        examples[label] = vir.visa_information_request_id

    print("visa information request conversations created")
    return examples


def _add_case_comments(ars: list[MvAccommodationRequest], author: User) -> None:
    commented_ars = [
        ars[index]
        for index, scenario in enumerate(AR_SCENARIOS)
        if scenario.get("case_comments")
    ]
    comment_index = 0
    for ar in commented_ars:
        for _ in range(2):
            created_at = timezone.make_aware(
                CASE_COMMENT_DATES[comment_index % len(CASE_COMMENT_DATES)]
            )
            comment = cast(
                Comment,
                CommentFactory(
                    id=record_id("comment", BROWSER_TEST_ID_PREFIX),
                    attached_accommodation_request_id=ar,
                    created_by=author.email,
                    content=CASE_COMMENTS[comment_index % len(CASE_COMMENTS)],
                ),
            )
            Comment.objects.filter(pk=comment.pk).update(
                created_at=created_at, modified_date=created_at
            )
            comment_index += 1

    print(f"case comments added to {len(commented_ars)} accommodation requests")


def _move_guests_off_closed_empty_ar(
    ar: MvAccommodationRequest, receiving_ar: MvAccommodationRequest
) -> None:
    for person in MvPerson.objects.filter(accommodation_request=ar):
        person.accommodation_request = receiving_ar
        person.save()
        receiving_ar.person_id = (receiving_ar.person_id or []) + [person.id]

    receiving_ar.number_of_people = len(receiving_ar.person_id)
    receiving_ar.save()

    ar.person_id = []
    ar.number_of_people = 0
    ar.save()
    print(f"closed empty: guests moved from {ar.id} to {receiving_ar.id}")


def seed_browser_test_la() -> None:
    if not browser_test_seeding_allowed():
        raise RuntimeError(
            "seed_browser_test_la only runs in dev or local environments"
        )

    ltla_name = BROWSER_TEST_LTLA_NAMES[0]

    with freeze_time(BROWSER_TEST_REFERENCE_DATETIME), transaction.atomic():
        wipe_browser_test_la_data()

        print(f"Using {BROWSER_TEST_SEED=}")
        random.seed(BROWSER_TEST_SEED)
        Faker.seed(BROWSER_TEST_SEED)
        reset_record_id_counters()
        author = get_browser_test_author()

        ars = []
        examples: dict[str, str] = {}
        for index, scenario in enumerate(AR_SCENARIOS):
            ar = build_complete_accommodation_scenario(
                num_guests=len(scenario["visa_statuses"]),
                ltla_name=ltla_name,
                accommodation_type=scenario.get("accommodation_type"),
                checks_status=scenario["checks_status"],
                visa_statuses=scenario["visa_statuses"],
                id_prefix=BROWSER_TEST_ID_PREFIX,
                status=scenario.get("ar_status"),
                make_uam=scenario.get("make_uam"),
            )
            ars.append(ar)

            match ar.checks_status:
                case ChecksStatus.CLOSED_LEFT_PROGRAMME:
                    mutate_closed_left_programme(ar)
                case (
                    ChecksStatus.CHECKS_PARTIALLY_COMPLETED
                    | ChecksStatus.CHECKS_COMPLETED
                    | ChecksStatus.SOME_CHECKS_FAILED
                ):
                    mutate_checks(ar, BROWSER_TEST_ID_PREFIX, author=author)

            if scenario.get("pending_reassignment"):
                mutate_rematch_required(
                    ar,
                    destination_ltla_name=MULTI_LA_SECOND_LTLA,
                    approve=False,
                    author=author,
                    reason="Guest has moved in with new partner",
                )

            for person in MvPerson.objects.filter(accommodation_request=ar):
                create_export_tool_object(
                    person,
                    ar.primary_sponsor,
                    ar.primary_accommodation,
                    ar,
                    id_prefix=BROWSER_TEST_ID_PREFIX,
                )

            examples.setdefault(f"checks status: {ar.checks_status}", ar.id)
            if scenario.get("ar_status"):
                examples.setdefault(f"AR status: {ar.status}", ar.id)
            if scenario.get("make_uam"):
                examples.setdefault("UAM (Flow Visa Pending)", ar.id)

            print(f"{index}: BrowserTest AccommodationRequests[{ar.checks_status}]")

        _move_guests_off_closed_empty_ar(
            _labelled_ar(ars, "closed empty"),
            _labelled_ar(ars, "receives guests from closed empty"),
        )
        _add_case_comments(ars, author)
        examples["case comments"] = next(
            ars[index].id
            for index, scenario in enumerate(AR_SCENARIOS)
            if scenario.get("case_comments")
        )
        examples.update(_make_visa_information_requests(author))

        examples["multi-LA AR"] = _make_multi_la_accommodation_request(
            _labelled_ar(ars, "multi-LA AR")
        )
        examples["multi-LA sponsor"] = _make_multi_la_sponsor(
            _labelled_ar(ars, "multi-LA sponsor")
        )
        examples["inbound accepted reassignment"] = _make_inbound_reassignment(author)
        examples["rejected outbound reassignment"] = (
            _make_rejected_outbound_reassignment(
                _labelled_ar(ars, "rejected outbound reassignment")
            )
        )
        examples["deduplicated guest pair"] = _make_deduplicated_guest_pair(author)
        examples["deduplicated sponsor pair"] = _make_deduplicated_sponsor_pair(author)
        examples["pending outbound reassignment"] = _labelled_ar(
            ars, "pending outbound reassignment"
        ).id

    print(
        f"\nSuccessfully reset {len(AR_SCENARIOS)} browser test "
        f"AccommodationRequest objects in {ltla_name}.\n"
    )
    print("Example records per scenario:")
    for label, example_id in sorted(examples.items()):
        print(f"  {label}: {example_id}")


def _replace_author_strings(value, author: User):
    replacements = {
        author.email: USER_EMAIL_PLACEHOLDER,
        author.username: USER_USERNAME_PLACEHOLDER,
        author.get_full_name(): USER_FULL_NAME_PLACEHOLDER,
    }
    if isinstance(value, str):
        return replacements.get(value, value)
    if isinstance(value, list):
        return [_replace_author_strings(item, author) for item in value]
    return value


def _rename_pk(model, old_pk: str, new_pk: str) -> None:
    for relation in model._meta.get_fields(include_hidden=True):
        if not relation.auto_created or relation.concrete:
            continue
        related_model = relation.related_model
        field_name = relation.field.name
        related_model._base_manager.filter(**{field_name: old_pk}).update(
            **{field_name: new_pk}
        )
    model._base_manager.filter(pk=old_pk).update(**{model._meta.pk.name: new_pk})


def _content_key(obj) -> str:
    fields = serializers.serialize("python", [obj])[0]["fields"]
    return json.dumps(fields, cls=DjangoJSONEncoder, sort_keys=True)


def _slug_app_generated_ids() -> None:
    renames = [
        (MvInteraction, "interaction"),
        (ReassignmentRequest, "rr"),
        (SafeguardingNotification, "safeguarding-notification"),
        (SafeguardingReferral, "safeguarding-referral"),
    ]
    collected = {
        queryset.model: queryset for _label, queryset in collect_browser_test_records()
    }
    for model, kind in renames:
        unprefixed = [
            obj
            for obj in collected[model]
            if not str(obj.pk).startswith(f"{BROWSER_TEST_ID_PREFIX}-")
        ]
        for obj in sorted(unprefixed, key=_content_key):
            _rename_pk(model, obj.pk, record_id(kind, BROWSER_TEST_ID_PREFIX))


def _serialise_browser_test_records(author: User) -> list[dict]:
    records: list[dict] = []
    for _label, queryset in collect_browser_test_records():
        records.extend(serializers.serialize("python", queryset.order_by("pk")))

    for record in records:
        model = apps.get_model(record["model"])
        fields = record["fields"]
        for name, value in list(fields.items()):
            field = model._meta.get_field(name)
            if field.is_relation and field.related_model is User and value:
                fields[name] = (
                    [USER_PK_PLACEHOLDER for _ in value]
                    if field.many_to_many
                    else USER_PK_PLACEHOLDER
                )
            elif field.many_to_many:
                fields[name] = sorted(value, key=str)
            else:
                fields[name] = _replace_author_strings(value, author)

        if isinstance(model._meta.pk, AutoField):
            record["pk"] = None

    records.sort(
        key=lambda record: (
            record["model"],
            str(record["pk"]),
            json.dumps(record["fields"], cls=DjangoJSONEncoder, sort_keys=True),
        )
    )
    return records


def _seeded_uuid4_factory():
    rng = random.Random(BROWSER_TEST_SEED)

    def seeded_uuid4():
        return uuid.UUID(int=rng.getrandbits(128), version=4)

    return seeded_uuid4


def generate_browser_test_seed_data(
    directory: Path = SEED_DATA_DIR,
) -> tuple[Path, int]:
    with mock.patch("uuid.uuid4", _seeded_uuid4_factory()), transaction.atomic():
        seed_browser_test_la()
        _slug_app_generated_ids()
        records = _serialise_browser_test_records(get_browser_test_author())
        transaction.set_rollback(True)

    directory.mkdir(parents=True, exist_ok=True)
    for stale in directory.glob("*.json"):
        stale.unlink()
    by_model: dict[str, list[dict]] = {}
    for record in records:
        by_model.setdefault(record["model"], []).append(record)
    for model, model_records in by_model.items():
        (directory / f"{model}.json").write_text(
            json.dumps(model_records, cls=DjangoJSONEncoder, indent=2, sort_keys=True)
            + "\n"
        )
    return directory, len(records)
