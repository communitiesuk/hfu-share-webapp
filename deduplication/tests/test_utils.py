from datetime import date

from deduplication.utils import (
    build_principal_accommodation_record,
    build_principal_guest_record,
    build_principal_sponsor_record,
)
from ontology.tests.factories import MvAccommodationFactory, MvUkPostcodeFactory
from test_utils.base import BaseTestCase


class BuildPrincipalGuestRecordTestCase(BaseTestCase):
    def _guest(self, **overrides):
        return {
            "first_name": "Jane",
            "last_name": "Doe",
            "sex": "Female",
            "date_of_birth": "1 January 1990",
            "email_address": "jane@example.com",
            "phone_numbers": "01234567890",
            "passport_number": "123456789",
            "visa_status": "Leave to remain",
            "application_numbers": "APP123",
            **overrides,
        }

    def test_builds_record_with_first_and_last_name(self):
        record = build_principal_guest_record(self._guest())

        self.assertEqual(
            record,
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "gender": "Female",
                "date_of_birth": date(1990, 1, 1),
                "email": "jane@example.com",
                "phone": "01234567890",
                "passport_id": "123456789",
                "visa_status": "Leave to remain",
                "application_number": "APP123",
            },
        )

    def test_builds_record_with_full_name_when_flag_set(self):
        record = build_principal_guest_record(self._guest(), use_full_name=True)

        self.assertEqual(record["full_name"], "Jane Doe")
        self.assertNotIn("first_name", record)
        self.assertNotIn("last_name", record)

    def test_date_of_birth_with_trailing_note_is_stripped(self):
        record = build_principal_guest_record(
            self._guest(date_of_birth="1 January 1990 (approx)")
        )

        self.assertEqual(record["date_of_birth"], date(1990, 1, 1))

    def test_date_of_birth_none_when_absent(self):
        record = build_principal_guest_record(self._guest(date_of_birth=None))

        self.assertIsNone(record["date_of_birth"])


class BuildPrincipalSponsorRecordTestCase(BaseTestCase):
    def _sponsor(self, **overrides):
        return {
            "first_name": "John",
            "last_name": "Smith",
            "sex": "Male",
            "date_of_birth": "2 February 1985",
            "email_address": "john@example.com",
            "phone_numbers": "09876543210",
            "residential_postcodes": ["AB1 2CD"],
            **overrides,
        }

    def test_builds_record_with_first_and_last_name(self):
        record = build_principal_sponsor_record(self._sponsor())

        self.assertEqual(
            record,
            {
                "first_name": "John",
                "last_name": "Smith",
                "sex": "Male",
                "date_of_birth": date(1985, 2, 2),
                "email": "john@example.com",
                "phone_number": "09876543210",
                "residential_postcodes": ["AB1 2CD"],
                "flag_unsuitable": False,
            },
        )

    def test_builds_record_with_full_name_when_flag_set(self):
        record = build_principal_sponsor_record(self._sponsor(), use_full_name=True)

        self.assertEqual(record["full_name"], "John Smith")
        self.assertNotIn("first_name", record)
        self.assertNotIn("last_name", record)

    def test_date_of_birth_none_when_absent(self):
        record = build_principal_sponsor_record(self._sponsor(date_of_birth=None))

        self.assertIsNone(record["date_of_birth"])


class BuildPrincipalAccommodationRecordTestCase(BaseTestCase):
    def test_builds_record_with_postcode(self):
        postcode = MvUkPostcodeFactory()
        accommodation = MvAccommodationFactory(postcode=postcode)

        record = build_principal_accommodation_record(
            {
                "full_address": accommodation.id,
                "postcode": postcode.id,
                "ltla_name": "Some District",
                "utla_name": "Some County",
            }
        )

        self.assertEqual(record["full_address"], accommodation.full_address)
        self.assertEqual(record["postcode"], postcode)
        self.assertEqual(record["ltla_name"], "Some District")
        self.assertEqual(record["utla_name"], "Some County")

    def test_builds_record_with_no_postcode(self):
        accommodation = MvAccommodationFactory(postcode=None)

        record = build_principal_accommodation_record(
            {
                "full_address": accommodation.id,
                "postcode": None,
                "ltla_name": "Some District",
                "utla_name": "Some County",
            }
        )

        self.assertEqual(record["full_address"], accommodation.full_address)
        self.assertIsNone(record["postcode"])
