"""Render ``browser_tests/seed_scenarios.md`` from the seeded browser test data.

The document is a catalogue of every record created by
``python manage.py seed_browser_test_la``. It used to be written by hand (with an
AI), which drifted out of sync whenever the seeder or the models changed. This
module regenerates it deterministically: the scenario catalogue comes from the
seeder's own ``AR_SCENARIOS`` constant, and the record tables come from querying
the browser-test records in the database the seeder just produced.

Run it through the ``generate_browser_test_docs`` management command, which seeds
the browser test LA and then calls :func:`render_browser_test_scenario_doc`.
"""

from collections.abc import Sequence
from pathlib import Path

from accounts.enums import (
    BROWSER_TEST_FIRST_LA_GROUP_NAME,
    BROWSER_TEST_LTLA_NAMES,
    BROWSER_TEST_SECOND_LA_GROUP_NAME,
)
from hfurb_scripts.seeders.stages.seed_browser_test_la import (
    AR_SCENARIOS,
    BROWSER_TEST_ID_PREFIX,
    CASE_COMMENT_DATES,
    CASE_COMMENTS,
    MULTI_LA_SECOND_LTLA,
)
from ontology.models import (
    DevCheckV2,
    MvAccommodation,
    MvAccommodationRequest,
    MvGroup,
    MvPerson,
    MvVolunteer,
    ReassignmentRequest,
    SafeguardingNotification,
    VisaApplication,
    VisaInformationRequest,
)

ChecksStatus = MvAccommodationRequest.ChecksStatus
Status = MvAccommodationRequest.Status

PREFIX = f"{BROWSER_TEST_ID_PREFIX}-"

#: shown in place of the safeguarding notification's random (non-seeded) UUID id
SAFEGUARDING_ID_PLACEHOLDER = "(random UUID, varies per seed run)"

#: default location of the generated document, relative to the repo root
DEFAULT_OUTPUT_PATH = (
    Path(__file__).resolve().parents[2] / "browser_tests" / "seed_scenarios.md"
)

_MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def _ar_id(index: int) -> str:
    """Deterministic AR id for the scenario at ``index`` (creation order)."""
    return f"{BROWSER_TEST_ID_PREFIX}-ar-{index + 1:05d}"


def _scenario_number(label: str) -> int:
    """1-based position of the scenario carrying ``label`` in ``AR_SCENARIOS``."""
    for index, scenario in enumerate(AR_SCENARIOS):
        if scenario.get("label") == label:
            return index + 1
    raise ValueError(f"no scenario labelled {label!r}")


def _scenario_extras(scenario: dict) -> str:  # noqa: C901
    """The free-text "Extras" cell for a scenario, composed from its flags.

    The wording lives here so it stays consistent and is defined once.
    """
    parts: list[str] = []

    checks_status = scenario["checks_status"]
    if checks_status == ChecksStatus.CHECKS_PARTIALLY_COMPLETED:
        parts.append("1 passed check")
    elif checks_status == ChecksStatus.CHECKS_COMPLETED:
        parts.append("4 passed checks")
    elif checks_status == ChecksStatus.SOME_CHECKS_FAILED:
        parts.append(
            "1 failed check, escalated when the failed check is an "
            "accommodation or sponsor check"
        )
    elif checks_status == ChecksStatus.CLOSED_LEFT_PROGRAMME:
        parts.append('leaving programme interaction ("Return to Ukraine")')

    if scenario.get("ar_status"):
        parts.append(f"AR status: {Status(scenario['ar_status']).label}")

    if scenario.get("make_uam"):
        parts.append("unaccompanied minor (UAM, Flow Visa Pending)")

    if scenario.get("accommodation_type"):
        parts.append("accommodation type is temporary accommodation")

    if scenario.get("case_comments"):
        parts.append("2 case comments")

    label = scenario.get("label")
    if label == "pending outbound reassignment":
        parts.append(f"pending outbound reassignment to {MULTI_LA_SECOND_LTLA}")
    elif label == "rejected outbound reassignment":
        parts.append(f"rejected outbound reassignment to {MULTI_LA_SECOND_LTLA}")
    elif label == "multi-LA sponsor":
        parts.append(
            f"multi-LA sponsor: the sponsor also owns a property in "
            f"{MULTI_LA_SECOND_LTLA}"
        )
    elif label == "multi-LA AR":
        parts.append(
            "multi-LA AR: extended with a second accommodation, sponsor and "
            f"unique application number in {MULTI_LA_SECOND_LTLA}, plus a "
            "Pending visa application per guest, so it spans two LAs"
        )
    elif label == "receives guests from closed empty":
        parts.append(
            "receives the guest moved off the closed empty AR "
            f"(#{_scenario_number('closed empty')})"
        )
    elif label == "closed empty":
        parts.append(
            "its guest is moved to AR "
            f"#{_scenario_number('receives guests from closed empty')}, "
            "leaving it with no people"
        )

    return ", ".join(parts)


def _cell(value) -> str:
    """Make a value safe for a single markdown table cell.

    Collapses the newlines that appear in truncated addresses (``full_address``
    spans two lines) to spaces, and escapes pipes so columns are not broken.
    """
    text = "" if value is None else str(value)
    return text.replace("\r\n", " ").replace("\n", " ").replace("|", "\\|").strip()


def _table(header: Sequence[str], rows: Sequence[Sequence[object]]) -> list[str]:
    """Render a markdown table as a list of lines."""
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * len(header)) + " |",
    ]
    lines += ["| " + " | ".join(_cell(cell) for cell in row) + " |" for row in rows]
    return lines


# --------------------------------------------------------------------------- #
# Section builders. Each returns a list of lines (no trailing blank line).
# --------------------------------------------------------------------------- #


def _header_section() -> list[str]:
    seeder_path = "hfurb_scripts/seeders/stages/seed_browser_test_la.py"
    return [
        "# Browser test seed scenarios",
        "",
        (
            "Catalog of every record scenario created by "
            "`python manage.py seed_browser_test_la`. The seeder wipes and "
            "recreates all data in the browser test local authority (LA) "
            f'"{BROWSER_TEST_LTLA_NAMES[0]}", so this state is the baseline at '
            "the start of every browser test run."
        ),
        "",
        (
            f"This file is generated by `python manage.py "
            f"generate_browser_test_docs`, which seeds the browser test LA and "
            f"then dumps it. Do not edit it by hand; re-run that command "
            f"instead. Source of truth: `{seeder_path}` (`AR_SCENARIOS` table "
            f"and the special scenario builders)."
        ),
    ]


def _fixed_values_section() -> list[str]:
    rows = [
        ["Test LA", BROWSER_TEST_LTLA_NAMES[0]],
        ["Test LA group", f"`{BROWSER_TEST_FIRST_LA_GROUP_NAME}`"],
        [
            "Second LA (multi-LA and reassignment scenarios)",
            BROWSER_TEST_LTLA_NAMES[1],
        ],
        ["Second LA group", f"`{BROWSER_TEST_SECOND_LA_GROUP_NAME}`"],
        ["Record id prefix", f"`{BROWSER_TEST_ID_PREFIX}`"],
        ["Random seed", "`BROWSER_TEST_SEED` env var, default 1313"],
    ]
    return [
        "## Fixed values",
        "",
        *_table(["Constant", "Value"], rows),
        "",
        (
            "Record ids are deterministic: counters reset each run, so ids "
            "follow creation order, for example "
            f"`{BROWSER_TEST_ID_PREFIX}-ar-00001`, "
            f"`{BROWSER_TEST_ID_PREFIX}-person-00003`, "
            f"`{BROWSER_TEST_ID_PREFIX}-check-00002`. Guests, sponsors, "
            "accommodations, groups, visa applications and export tool objects "
            "hang off each accommodation request with the same prefix scheme "
            "(`person`, `sponsor`, `accommodation`, `group`, `visa`, `export`)."
        ),
    ]


def _ar_scenarios_section(ars_by_id: dict[str, MvAccommodationRequest]) -> list[str]:
    rows = []
    for index, scenario in enumerate(AR_SCENARIOS):
        ar_id = _ar_id(index)
        ar = ars_by_id.get(ar_id)
        rows.append(
            [
                str(index + 1),
                ar_id,
                ar.title if ar else "",
                ChecksStatus(scenario["checks_status"]).label,
                ", ".join(scenario["visa_statuses"]),
                _scenario_extras(scenario),
            ]
        )
    return [
        "## Accommodation request scenarios",
        "",
        (
            "One accommodation request (AR) per row, created in this order. "
            "Guest count equals the number of visa statuses. Every checks "
            "status and AR status value appears at least once."
        ),
        "",
        *_table(
            [
                "#",
                "AR id",
                "Title",
                "Checks status",
                "Guest visa statuses",
                "Extras",
            ],
            rows,
        ),
    ]


def _special_scenarios_section(
    ars_by_id: dict[str, MvAccommodationRequest],
) -> list[str]:
    base = len(AR_SCENARIOS)
    inbound_id = _ar_id(base)
    guest_dup_id = _ar_id(base + 1)
    sponsor_dup_id = _ar_id(base + 2)

    def title(ar_id: str) -> str:
        ar = ars_by_id.get(ar_id)
        return ar.title if ar else ""

    rows = [
        [
            "Inbound accepted reassignment",
            inbound_id,
            title(inbound_id),
            (
                f"Built in {MULTI_LA_SECOND_LTLA} with checks status Rematch "
                "required, then reassigned into the test LA with an accepted "
                'reassignment request ("Sponsorship placement broke down"), a '
                "rematch interaction, accommodation removed and hosts unlinked "
                "(which is why the title has no address)"
            ),
        ],
        [
            "Deduplicated guest pair",
            guest_dup_id,
            title(guest_dup_id),
            (
                "One guest plus a near-duplicate (same name, date of birth and "
                "passport, surname uppercased), merged through a "
                "GuestDuplicateGroup by the browser test user"
            ),
        ],
        [
            "Deduplicated sponsor pair",
            sponsor_dup_id,
            title(sponsor_dup_id),
            (
                "One sponsor plus a near-duplicate (same email and date of "
                "birth, surname lowercased), merged through a "
                "SponsorDuplicateGroup by the browser test user"
            ),
        ],
    ]
    return [
        "## Special scenarios created after the table",
        "",
        *_table(["Scenario", "AR id", "Title", "Detail"], rows),
    ]


def _visa_information_requests_section() -> list[str]:
    rows = [
        [
            "VIR awaiting LA",
            VisaInformationRequest.RequestStatus.AWAITING_LA.label,
            (
                "1 UKVI message asking whether the guest still resides at the "
                "sponsor's address"
            ),
        ],
        [
            "VIR awaiting UKVI",
            VisaInformationRequest.RequestStatus.AWAITING_UKVI.label,
            "UKVI asks for the arrival date, the LA replies confirming it",
        ],
        [
            "VIR closed",
            VisaInformationRequest.RequestStatus.CLOSED.label,
            (
                "UKVI asks whether guests are known, the LA confirms, UKVI "
                "closes the request"
            ),
        ],
    ]
    return [
        "## Visa information requests",
        "",
        (
            "Three conversations attached to the first three visa applications "
            "in the test LA (ordered by visa application id):"
        ),
        "",
        *_table(["Label", "Status", "Conversation"], rows),
        "",
        (
            "UK Visas and Immigration (UKVI) messages are authored as "
            "`browser-test-ukvi`; LA replies are authored as the browser test "
            "user."
        ),
    ]


def _checks_statuses_section() -> list[str]:
    rows = [
        [ChecksStatus.CHECKS_REQUIRED.label, "none"],
        [
            ChecksStatus.CHECKS_PARTIALLY_COMPLETED.label,
            (
                "1 passed check (random type from: accommodation suitable, "
                "accommodation exists, sponsor DBS, group arrived)"
            ),
        ],
        [ChecksStatus.CHECKS_COMPLETED.label, "all 4 check types passed"],
        [
            ChecksStatus.SOME_CHECKS_FAILED.label,
            (
                "1 failed check with a failure reason; when it is an "
                "accommodation or sponsor check, an escalated safeguarding "
                "check is raised through the real form"
            ),
        ],
        [
            ChecksStatus.CLOSED_LEFT_PROGRAMME.label,
            'a "Return to Ukraine" leaving programme interaction',
        ],
    ]
    return [
        "## Checks statuses and what they seed",
        "",
        *_table(["Checks status", "Seeded checks"], rows),
    ]


def _case_comments_section() -> list[str]:
    commented = [
        f"#{index + 1}"
        for index, scenario in enumerate(AR_SCENARIOS)
        if scenario.get("case_comments")
    ]
    months = sorted({date.month for date in CASE_COMMENT_DATES})
    first_month = _MONTHS[months[0] - 1]
    last_month = _MONTHS[months[-1] - 1]
    year = CASE_COMMENT_DATES[0].year
    return [
        "## Case comments",
        "",
        (
            f"Accommodation requests flagged with case comments "
            f"({', '.join(commented)}) each get 2 comments, drawn in order from "
            f"a fixed list of {len(CASE_COMMENTS)} comment texts with fixed "
            f"dates between {first_month} and {last_month} {year}, authored by "
            f"the browser test user."
        ),
    ]


def _all_records_section(ars: list[MvAccommodationRequest]) -> list[str]:
    # map each accommodation / sponsor id to the ARs that reference it
    accommodation_to_ars: dict[str, list[str]] = {}
    sponsor_to_ars: dict[str, list[str]] = {}
    for ar in ars:
        for accommodation_id in ar.accommodation_id or []:
            accommodation_to_ars.setdefault(accommodation_id, []).append(ar.id)
        for sponsor_id in ar.sponsor_id or []:
            sponsor_to_ars.setdefault(sponsor_id, []).append(ar.id)

    lines = ["## All seeded records", ""]
    lines += [
        (
            "Every record the seeder creates, grouped by model, in creation "
            "order. Generated from the seeded local database with the default "
            "seed."
        ),
        "",
    ]

    # Guests
    guest_rows = [
        [
            person.id,
            person.get_full_name(),
            person.visa_status or "",
            person.accommodation_request_id or "",
        ]
        for person in MvPerson.objects.filter(id__startswith=PREFIX).order_by("id")
    ]
    lines += ["### Guests (MvPerson)", ""]
    lines += _table(["Id", "Name", "Visa status", "AR"], guest_rows)
    lines += [""]

    # Sponsors
    sponsor_rows = [
        [
            sponsor.id,
            sponsor.get_full_name(),
            ", ".join(sorted(sponsor_to_ars.get(sponsor.id, []))),
        ]
        for sponsor in MvVolunteer.objects.filter(id__startswith=PREFIX).order_by("id")
    ]
    lines += ["### Sponsors (MvVolunteer)", ""]
    lines += _table(["Id", "Name", "AR(s)"], sponsor_rows)
    lines += [""]

    # Accommodations
    accommodation_rows = [
        [
            accommodation.id,
            accommodation.full_address or "",
            accommodation.ltla_name or "",
            ", ".join(sorted(accommodation_to_ars.get(accommodation.id, []))),
        ]
        for accommodation in MvAccommodation.objects.filter(
            id__startswith=PREFIX
        ).order_by("id")
    ]
    lines += ["### Accommodations (MvAccommodation)", ""]
    lines += _table(["Id", "Address", "LA", "AR(s)"], accommodation_rows)
    lines += [""]

    # Groups
    group_rows = [
        [group.id, group.title or ""]
        for group in MvGroup.objects.filter(id__startswith=PREFIX).order_by("id")
    ]
    lines += ["### Groups (MvGroup)", ""]
    lines += _table(["Id", "Title"], group_rows)
    lines += [""]

    # Visa applications
    visa_rows = [
        [
            visa.visa_application_id,
            visa.Q44g_full_name or "",
            visa.visa_status or "",
            visa.application_unique_application_number or "",
        ]
        for visa in VisaApplication.objects.filter(
            visa_application_id__startswith=PREFIX
        ).order_by("visa_application_id")
    ]
    lines += ["### Visa applications", ""]
    lines += _table(
        ["Id", "Applicant", "Visa status", "Unique application number"], visa_rows
    )
    lines += [""]

    # Checks
    check_rows = []
    for check in (
        DevCheckV2.objects.filter(id__startswith=PREFIX)
        .order_by("id")
        .prefetch_related("AR", "check_type")
    ):
        ar_ids = sorted(check.AR.values_list("id", flat=True))
        check_rows.append(
            [
                check.id,
                str(check.check_type) if check.check_type else "",
                check.check_status or "",
                check.check_subtype or "",
                ", ".join(ar_ids),
            ]
        )
    lines += ["### Checks (DevCheckV2)", ""]
    lines += _table(["Id", "Type", "Status", "Failure reason", "AR(s)"], check_rows)
    lines += [""]

    # Safeguarding notifications. The id is a random UUID assigned by the real
    # safeguarding form (not seeded from BROWSER_TEST_SEED), so it changes every
    # run; mask it to keep this document deterministic. The AR and check it
    # points at are the stable references.
    safeguarding_rows = [
        [SAFEGUARDING_ID_PLACEHOLDER, ar_id or "", check_id or ""]
        for ar_id, check_id in SafeguardingNotification.objects.filter(
            ar__id__startswith=PREFIX
        )
        .order_by("id")
        .values_list("ar", "dev_check_v2")
    ]
    lines += ["### Safeguarding notifications", ""]
    lines += _table(["Id", "AR", "Check"], safeguarding_rows)
    lines += [""]

    # Reassignment requests
    reassignment_rows = [
        [
            request.id,
            request.outcome or "",
            request.destination_ltla_name or "",
            request.accommodation_request_id or "",
        ]
        for request in ReassignmentRequest.objects.filter(
            accommodation_request__id__startswith=PREFIX
        ).order_by("id")
    ]
    lines += ["### Reassignment requests", ""]
    lines += _table(["Id", "Outcome", "Destination LA", "AR"], reassignment_rows)
    lines += [""]

    # Visa information requests
    vir_rows = [
        [
            vir.visa_information_request_id,
            vir.request_status or "",
            vir.visa_application_id or "",
            vir.request_title or "",
        ]
        for vir in VisaInformationRequest.objects.filter(
            visa_information_request_id__startswith=PREFIX
        ).order_by("visa_information_request_id")
    ]
    lines += ["### Visa information request records", ""]
    lines += _table(["Id", "Status", "Visa application", "Title"], vir_rows)

    return lines


def render_browser_test_scenario_doc() -> str:
    """Render the full ``seed_scenarios.md`` from the seeded database."""
    ars = list(
        MvAccommodationRequest.objects.filter(id__startswith=PREFIX).order_by("id")
    )
    ars_by_id = {ar.id: ar for ar in ars}

    sections = [
        _header_section(),
        _fixed_values_section(),
        _ar_scenarios_section(ars_by_id),
        _special_scenarios_section(ars_by_id),
        _visa_information_requests_section(),
        _checks_statuses_section(),
        _case_comments_section(),
        _all_records_section(ars),
    ]

    body = "\n\n".join("\n".join(section) for section in sections)
    return body + "\n"
