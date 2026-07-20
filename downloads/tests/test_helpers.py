from datetime import datetime
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from downloads.constants import (
    ACCOMMODATION_FIELDS,
    DOWNLOAD_ALL_COLUMN_ORDERING,
    DOWNLOAD_UAMS_COLUMN_ORDERING,
    REMATCHED_HOST_FIELDS,
    SPONSOR_FIELDS,
)
from downloads.forms import DownloadType
from downloads.helpers import (
    CONTROL_CHARACTERS,
    build_csv_header,
    build_csv_row,
    determine_redacted_fields,
)
from ontology.models import (
    ExportToolObject,
    MvAccommodationRequest,
    MvPerson,
    SponsorshipCertificationForm,
)


class TestBuildCSVHeader(SimpleTestCase):
    def test_build_csv_header_basic(self):
        header = build_csv_header(MvPerson, DownloadType.GUESTS)

        assert "id" in header
        assert "accommodation_request" in header
        assert "first_name" in header
        assert "last_name" in header
        assert "email" in header
        assert "created_at" in header
        assert "created_at_tz" in header

    def test_build_csv_header_all_data(self):
        header = build_csv_header(ExportToolObject, DownloadType.ALL)

        assert header == DOWNLOAD_ALL_COLUMN_ORDERING

    def test_build_csv_header_uams(self):
        header = build_csv_header(SponsorshipCertificationForm, DownloadType.UAMS)

        assert header == DOWNLOAD_UAMS_COLUMN_ORDERING


class TestBuildCSVRow(SimpleTestCase):
    def test_build_csv_row_basic(self):
        person = MvPerson(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
        )

        field_names = ["first_name", "last_name", "email"]

        row = build_csv_row(person, field_names, set())

        assert row == ["John", "Doe", "john.doe@example.com"]

    def test_build_csv_row_basic_with_none_values(self):
        person = MvPerson(
            first_name="John",
            last_name="Doe",
            email=None,
        )

        field_names = ["first_name", "last_name", "email"]

        row = build_csv_row(person, field_names, set())

        assert row == ["John", "Doe", ""]

    def test_build_csv_row_with_datetime_created_at(self):
        created_at = datetime.fromisoformat("2024-01-18 09:57:23.860782+00:00")
        datetime_str = created_at.strftime("%Y-%m-%d %H:%M:%S")

        person = MvPerson(
            first_name="Jane",
            created_at=created_at,
        )

        field_names = ["first_name", "created_at", "created_at_tz"]

        row = build_csv_row(person, field_names, set())

        assert row[0] == "Jane"
        assert row[1] == datetime_str
        assert row[2] == "UTC"

    def test_build_csv_row_with_date_created_at(self):
        datetime_str = "2024-01-18"
        created_at = datetime.fromisoformat(datetime_str)

        person = MvPerson(
            first_name="Jane",
            created_at=created_at,
        )

        field_names = ["first_name", "created_at", "created_at_tz"]

        row = build_csv_row(person, field_names, set())

        assert row[0] == "Jane"
        assert row[1] == "2024-01-18 00:00:00"
        assert row[2] == ""

    def test_build_csv_row_with_foreign_key(self):
        person = MvPerson(
            first_name="Jane",
            accommodation_request=MvAccommodationRequest(id="AR-123-123"),
        )

        field_names = ["first_name", "accommodation_request"]

        row = build_csv_row(person, field_names, set())

        assert row[0] == "Jane"
        assert row[1] == "AR-123-123"

    def test_build_csv_row_escapes_leading_control_characters(self):
        for control_character in CONTROL_CHARACTERS:
            with self.subTest(control_character=control_character):
                person = MvPerson(
                    first_name=f"{control_character}J@ne",
                    last_name="Doe",
                    email="john.doe@example.com",
                )

                field_names = ["first_name", "last_name", "email"]

                row = build_csv_row(person, field_names, set())

                assert row == ["J@ne", "Doe", "john.doe@example.com"]

        for control_character_a, control_character_b in zip(
            CONTROL_CHARACTERS,
            CONTROL_CHARACTERS[3:] + CONTROL_CHARACTERS[:3],
            strict=False,
        ):
            with self.subTest(
                control_character=f"{control_character_a}{control_character_b}"
            ):
                person = MvPerson(
                    first_name=f"{control_character_a}{control_character_b}J@ne",
                    last_name="Doe",
                    email="john.doe@example.com",
                )

                field_names = ["first_name", "last_name", "email"]

                row = build_csv_row(person, field_names, set())

                assert row == ["J@ne", "Doe", "john.doe@example.com"]


ATTR_SPEC = [
    "sponsor_ltla_name",
    "sponsor_utla_name",
    "rematched_host_ltla_name",
    "rematched_host_utla_name",
    "accommodation_ltla_name",
    "accommodation_utla_name",
]


def make_mock(**overrides):
    obj = MagicMock(name="ExportToolObject", spec_set=ATTR_SPEC)

    obj.sponsor_ltla_name = None
    obj.sponsor_utla_name = None
    obj.rematched_host_ltla_name = None
    obj.rematched_host_utla_name = None
    obj.accommodation_ltla_name = None
    obj.accommodation_utla_name = None

    for k, v in overrides.items():
        setattr(obj, k, v)
    return obj


class DetermineRedactedFieldTests(SimpleTestCase):
    def test_returns_empty_set_when_all_sections_match(self):
        obj = make_mock(
            sponsor_ltla_name=["LTLA1"],
            sponsor_utla_name=["UTLA1"],
            rematched_host_ltla_name=["LTLA1"],
            rematched_host_utla_name=["UTLA1"],
            accommodation_ltla_name=["LTLA1"],
            accommodation_utla_name=["UTLA1"],
        )
        got = determine_redacted_fields(obj, {"LTLA1"}, {"UTLA1"})
        self.assertEqual(got, set())

    def test_redacts_sponsor_on_ltla_mismatch(self):
        obj = make_mock(
            sponsor_ltla_name=["OTHER"],
            sponsor_utla_name=None,
        )
        got = determine_redacted_fields(obj, {"LTLA1"}, {"UTLA1"})
        self.assertEqual(got, set(SPONSOR_FIELDS))

    def test_no_redaction_sponsor_on_utla_mismatch_if_ltla_matches(self):
        obj = make_mock(
            sponsor_ltla_name=["LTLA1"],  # matches
            sponsor_utla_name=["OTHER"],  # no match but should not redact
        )
        got = determine_redacted_fields(obj, {"LTLA1"}, {"UTLA1"})
        self.assertEqual(got, set())

    def test_falsy_values_do_not_trigger_redaction(self):
        obj = make_mock(
            accommodation_ltla_name=[],  # empty set is falsy -> ignored
            accommodation_utla_name=None,
        )
        got = determine_redacted_fields(obj, {"LTLA1"}, {"UTLA1"})
        self.assertEqual(got, set())

    def test_redacts_rematched_host_on_utla_mismatch(self):
        obj = make_mock(rematched_host_utla_name=["OTHER"])
        got = determine_redacted_fields(obj, {"LTLA1"}, {"UTLA1"})
        self.assertEqual(got, set(REMATCHED_HOST_FIELDS))

    def test_redacts_accommodation_on_ltla_mismatch(self):
        obj = make_mock(accommodation_ltla_name=["OTHER"])
        got = determine_redacted_fields(obj, {"LTLA1"}, {"UTLA1"})
        self.assertEqual(got, set(ACCOMMODATION_FIELDS))

    def test_multiple_sections_union_of_fields(self):
        obj = make_mock(
            sponsor_ltla_name=["OTHER"],
            accommodation_utla_name=["OTHER2"],
        )
        got = determine_redacted_fields(obj, {"LTLA1"}, {"UTLA1"})
        self.assertEqual(got, set(SPONSOR_FIELDS) | set(ACCOMMODATION_FIELDS))

    def test_empty_user_sets_redacts_all_present_sections(self):
        obj = make_mock(
            sponsor_ltla_name=["LTLA1"],
            rematched_host_utla_name=["UTLA1"],
            accommodation_ltla_name=["LTLA1"],
        )
        got = determine_redacted_fields(obj, set(), set())
        self.assertEqual(
            got,
            set(SPONSOR_FIELDS)
            | set(REMATCHED_HOST_FIELDS)
            | set(ACCOMMODATION_FIELDS),
        )

    def test_sponsor_ltla_only_present_matches_no_redaction(self):
        obj = make_mock(sponsor_ltla_name=["LTLA1"])
        got = determine_redacted_fields(obj, {"LTLA1"}, {"UTLA1"})
        self.assertEqual(got, set())

    def test_sponsor_utla_only_present_matches_no_redaction(self):
        obj = make_mock(sponsor_utla_name=["UTLA1"])
        got = determine_redacted_fields(obj, {"LTLA1"}, {"UTLA1"})
        self.assertEqual(got, set())

    def test_sponsor_multiple_values_partial_overlap_no_redaction(self):
        obj = make_mock(sponsor_ltla_name=["A", "B"])
        got = determine_redacted_fields(obj, {"B", "C"}, {"U"})
        self.assertEqual(got, set())

    def test_no_linked_objects_no_redaction(self):
        obj = make_mock(
            sponsor_ltla_name=[],
            sponsor_utla_name=[],
            rematched_host_ltla_name=[],
            rematched_host_utla_name=[],
            accommodation_ltla_name=[],
            accommodation_utla_name=[],
        )
        got = determine_redacted_fields(obj, {"LTLA1"}, {"UTLA1"})
        self.assertEqual(got, set())
