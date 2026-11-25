import os
from unittest import mock

import boto3
from django.conf import settings
from moto import mock_aws

from accounts.enums import GroupType
from accounts.models import GroupInfo
from accounts.tests.factories import GroupInfoFactory
from hfurb_scripts.fix_incorrectly_assigned_las import (
    ALREADY_CORRECT,
    AMBIGUOUS_LOCAL_AUTHORITY_GROUP,
    CHANGED_SINCE_EXPORT,
    DUPLICATE_IN_FILE,
    NO_LOCAL_AUTHORITY_GROUP,
    NO_TARGET,
    NOT_EDITABLE,
    NOT_FOUND,
    UTLA_DOES_NOT_MATCH_GROUP,
    AccommodationFix,
    VisaApplicationFix,
    fix_incorrectly_assigned_las,
    get_accommodations_to_process,
    get_visa_applications_to_process,
)
from hfurb_scripts.tests.base import BaseScriptTestCaseWithSession
from ontology.models import MvAccommodation
from ontology.tests.factories import MvAccommodationFactory, VisaApplicationFactory

LOGGER_NAME = "hfurb_scripts.fix_incorrectly_assigned_las"


def local_authority_group(ltla_name: str) -> GroupInfo:
    return GroupInfo.objects.get(
        ltla_name=ltla_name,
        is_utla=False,
        group_type=GroupType.LOCAL_AUTHORITY,
    )


class FixIncorrectlyAssignedLasTestCase(BaseScriptTestCaseWithSession):
    def setUp(self):
        super().setUp()

        self.accommodation_fixes = []
        self.visa_application_fixes = []

        accommodations_patcher = mock.patch(
            "hfurb_scripts.fix_incorrectly_assigned_las.get_accommodations_to_process"
        )
        self.addCleanup(accommodations_patcher.stop)
        self.accommodations_loader = accommodations_patcher.start()
        self.accommodations_loader.side_effect = lambda: self.accommodation_fixes

        visa_patcher = mock.patch(
            "hfurb_scripts.fix_incorrectly_assigned_las.get_visa_applications_to_process"
        )
        self.addCleanup(visa_patcher.stop)
        self.visa_applications_loader = visa_patcher.start()
        self.visa_applications_loader.side_effect = lambda: self.visa_application_fixes

    def run_script(self, dry_run=False) -> list[str]:
        with self.assertLogs(LOGGER_NAME, level="INFO") as logs:
            fix_incorrectly_assigned_las(dry_run=dry_run)
        return logs.output

    def assert_skipped(self, output, record_type, record_id, reason):
        expected = f"Not reverting {record_type} {record_id} as {reason}"
        self.assertTrue(any(expected in line for line in output), "\n".join(output))

    def reloaded(self, record):
        record.refresh_from_db()
        return record


class TestLocalAuthorityFixtures(FixIncorrectlyAssignedLasTestCase):
    def test_two_tier_group_has_an_upper_tier_la(self):
        havant = local_authority_group("Havant")

        self.assertEqual(havant.utla_name, "Hampshire")
        self.assertEqual(havant.da_name, "England")

    def test_scottish_group_has_no_upper_tier_la(self):
        highland = local_authority_group("Highland")

        self.assertIsNone(highland.utla_name)
        self.assertEqual(highland.da_name, "Scotland")


class TestFixAccommodations(FixIncorrectlyAssignedLasTestCase):
    def setUp(self):
        super().setUp()

        self.accommodation = MvAccommodationFactory(
            ltla_name="Highland", utla_name=None
        )
        self.untouched = MvAccommodationFactory(
            ltla_name="Swansea", utla_name="Swansea"
        )

    def fix_for(self, accommodation, **overrides):
        values = {
            "accommodation_id": accommodation.id,
            "ltla_should_have": "Havant",
            "ltla_changed_to": "Highland",
            "utla_should_have": "Hampshire",
            "utla_changed_to": None,
            **overrides,
        }
        return AccommodationFix(**values)

    def assert_accommodation_skipped(self, output, accommodation_id, reason):
        self.assert_skipped(output, "Accommodation", accommodation_id, reason)

    def test_reverts_both_local_authority_fields(self):
        self.accommodation_fixes = [self.fix_for(self.accommodation)]

        self.run_script()

        self.assertEqual(self.reloaded(self.accommodation).ltla_name, "Havant")
        self.assertEqual(self.accommodation.utla_name, "Hampshire")

    def test_reverts_the_upper_tier_la_to_none_for_a_single_tier_la(self):
        accommodation = MvAccommodationFactory(ltla_name="Swansea", utla_name="Swansea")
        self.accommodation_fixes = [
            self.fix_for(
                accommodation,
                ltla_should_have="Highland",
                ltla_changed_to="Swansea",
                utla_should_have=None,
                utla_changed_to="Swansea",
            )
        ]

        self.run_script()

        self.assertEqual(self.reloaded(accommodation).ltla_name, "Highland")
        self.assertIsNone(accommodation.utla_name)

    def test_reverts_an_archived_accommodation(self):
        MvAccommodation.objects_including_archived.filter(
            id=self.accommodation.id
        ).update(is_archived=True)
        self.accommodation_fixes = [self.fix_for(self.accommodation)]

        self.run_script()

        self.assertEqual(self.reloaded(self.accommodation).ltla_name, "Havant")
        self.assertEqual(self.accommodation.utla_name, "Hampshire")

    def test_leaves_records_not_in_the_file_alone(self):
        self.accommodation_fixes = [self.fix_for(self.accommodation)]

        self.run_script()

        self.assertEqual(self.reloaded(self.untouched).ltla_name, "Swansea")

    def test_skips_a_record_whose_la_changed_since_the_export(self):
        self.accommodation.ltla_name = "Doncaster"
        self.accommodation.utla_name = "Doncaster"
        self.accommodation.save()
        self.accommodation_fixes = [self.fix_for(self.accommodation)]

        output = self.run_script()

        self.assert_accommodation_skipped(
            output, self.accommodation.id, CHANGED_SINCE_EXPORT
        )
        self.assertEqual(self.reloaded(self.accommodation).ltla_name, "Doncaster")

    def test_skips_a_record_whose_upper_tier_la_alone_changed_since_the_export(self):
        self.accommodation.utla_name = "Hampshire"
        self.accommodation.save()
        self.accommodation_fixes = [self.fix_for(self.accommodation)]

        output = self.run_script()

        self.assert_accommodation_skipped(
            output, self.accommodation.id, CHANGED_SINCE_EXPORT
        )
        self.assertEqual(self.reloaded(self.accommodation).ltla_name, "Highland")

    def test_skips_a_record_that_is_already_correct(self):
        accommodation = MvAccommodationFactory(
            ltla_name="Havant", utla_name="Hampshire"
        )
        self.accommodation_fixes = [self.fix_for(accommodation)]

        output = self.run_script()

        self.assert_accommodation_skipped(output, accommodation.id, ALREADY_CORRECT)

    def test_skips_a_record_that_is_not_editable(self):
        MvAccommodation.objects.filter(id=self.accommodation.id).update(
            is_editable=False
        )
        self.accommodation_fixes = [self.fix_for(self.accommodation)]

        output = self.run_script()

        self.assert_accommodation_skipped(output, self.accommodation.id, NOT_EDITABLE)
        self.assertEqual(self.reloaded(self.accommodation).ltla_name, "Highland")

    def test_skips_a_row_with_no_target_local_authority(self):
        self.accommodation_fixes = [
            self.fix_for(self.accommodation, ltla_should_have=None)
        ]

        output = self.run_script()

        self.assert_accommodation_skipped(output, self.accommodation.id, NO_TARGET)
        self.assertEqual(self.reloaded(self.accommodation).ltla_name, "Highland")

    def test_skips_a_target_la_with_no_group(self):
        self.accommodation_fixes = [
            self.fix_for(self.accommodation, ltla_should_have="Atlantis")
        ]

        output = self.run_script()

        self.assert_accommodation_skipped(
            output, self.accommodation.id, NO_LOCAL_AUTHORITY_GROUP
        )
        self.assertEqual(self.reloaded(self.accommodation).ltla_name, "Highland")

    def test_skips_a_target_whose_upper_tier_la_does_not_match_its_group(self):
        self.accommodation_fixes = [
            self.fix_for(self.accommodation, utla_should_have=None)
        ]

        output = self.run_script()

        self.assert_accommodation_skipped(
            output, self.accommodation.id, UTLA_DOES_NOT_MATCH_GROUP
        )
        self.assertEqual(self.reloaded(self.accommodation).ltla_name, "Highland")

    def test_skips_a_target_la_that_matches_more_than_one_group(self):
        GroupInfoFactory(
            ltla_name="Havant",
            utla_name="Hampshire",
            da_name="England",
            is_utla=False,
            group_type=GroupType.LOCAL_AUTHORITY,
        )
        self.accommodation_fixes = [self.fix_for(self.accommodation)]

        output = self.run_script()

        self.assert_accommodation_skipped(
            output, self.accommodation.id, AMBIGUOUS_LOCAL_AUTHORITY_GROUP
        )
        self.assertEqual(self.reloaded(self.accommodation).ltla_name, "Highland")

    def test_skips_an_id_that_appears_more_than_once_in_the_file(self):
        self.accommodation_fixes = [
            self.fix_for(self.accommodation),
            self.fix_for(
                self.accommodation,
                ltla_should_have="Doncaster",
                utla_should_have="Doncaster",
            ),
        ]

        output = self.run_script()

        self.assert_accommodation_skipped(
            output, self.accommodation.id, DUPLICATE_IN_FILE
        )
        self.assertEqual(self.reloaded(self.accommodation).ltla_name, "Highland")

    def test_skips_an_id_that_no_longer_exists(self):
        self.accommodation_fixes = [
            AccommodationFix(
                accommodation_id="accommodation-gone",
                ltla_should_have="Havant",
                ltla_changed_to="Highland",
                utla_should_have="Hampshire",
                utla_changed_to=None,
            )
        ]

        output = self.run_script()

        self.assert_accommodation_skipped(output, "accommodation-gone", NOT_FOUND)

    def test_dry_run_writes_nothing_and_says_so(self):
        self.accommodation_fixes = [self.fix_for(self.accommodation)]

        output = self.run_script(dry_run=True)

        self.assertTrue(
            any(
                f"Would revert Accommodation {self.accommodation.id}" in line
                for line in output
            ),
            "\n".join(output),
        )
        self.assertEqual(self.reloaded(self.accommodation).ltla_name, "Highland")
        self.assertIsNone(self.accommodation.utla_name)


class TestFixVisaApplications(FixIncorrectlyAssignedLasTestCase):
    def setUp(self):
        super().setUp()

        self.visa_application = VisaApplicationFactory(
            ltla_name="Swansea", utla_name="Swansea", country="Wales"
        )

    def fix_for(self, visa_application, **overrides):
        values = {
            "visa_application_id": visa_application.visa_application_id,
            "ltla_should_have": "Havant",
            "ltla_changed_to": "Swansea",
            "utla_should_have": "Hampshire",
            "utla_changed_to": "Swansea",
            "country_changed_to": "Wales",
            **overrides,
        }
        return VisaApplicationFix(**values)

    def assert_visa_application_skipped(self, output, visa_application_id, reason):
        self.assert_skipped(output, "VisaApplication", visa_application_id, reason)

    def test_reverts_the_la_and_derives_the_upper_tier_and_country(self):
        self.visa_application_fixes = [self.fix_for(self.visa_application)]

        output = self.run_script()

        self.assertEqual(self.reloaded(self.visa_application).ltla_name, "Havant")
        self.assertEqual(self.visa_application.utla_name, "Hampshire")
        self.assertEqual(self.visa_application.country, "England")
        self.assertTrue(
            any(
                f"Reverted VisaApplication {self.visa_application.visa_application_id}"
                " to Havant, Hampshire, England" in line
                for line in output
            ),
            "\n".join(output),
        )

    def test_writes_a_null_upper_tier_la_for_a_single_tier_la(self):
        self.visa_application_fixes = [
            self.fix_for(
                self.visa_application,
                ltla_should_have="Highland",
                utla_should_have=None,
            )
        ]

        self.run_script()

        self.assertEqual(self.reloaded(self.visa_application).ltla_name, "Highland")
        self.assertIsNone(self.visa_application.utla_name)
        self.assertEqual(self.visa_application.country, "Scotland")

    def test_skips_a_row_with_no_target_local_authority(self):
        self.visa_application_fixes = [
            self.fix_for(self.visa_application, ltla_should_have=None)
        ]

        output = self.run_script()

        self.assert_visa_application_skipped(
            output, self.visa_application.visa_application_id, NO_TARGET
        )
        self.assertEqual(self.reloaded(self.visa_application).ltla_name, "Swansea")

    def test_skips_a_target_la_with_no_group(self):
        self.visa_application_fixes = [
            self.fix_for(self.visa_application, ltla_should_have="Atlantis")
        ]

        output = self.run_script()

        self.assert_visa_application_skipped(
            output,
            self.visa_application.visa_application_id,
            NO_LOCAL_AUTHORITY_GROUP,
        )
        self.assertEqual(self.reloaded(self.visa_application).country, "Wales")

    def test_skips_a_record_where_the_group_disagrees_with_the_file(self):
        self.visa_application_fixes = [
            self.fix_for(self.visa_application, utla_should_have="Lincolnshire")
        ]

        output = self.run_script()

        self.assert_visa_application_skipped(
            output,
            self.visa_application.visa_application_id,
            UTLA_DOES_NOT_MATCH_GROUP,
        )
        self.assertEqual(self.reloaded(self.visa_application).utla_name, "Swansea")

    def test_skips_a_record_whose_country_changed_since_the_export(self):
        self.visa_application_fixes = [
            self.fix_for(self.visa_application, country_changed_to="Scotland")
        ]

        output = self.run_script()

        self.assert_visa_application_skipped(
            output,
            self.visa_application.visa_application_id,
            CHANGED_SINCE_EXPORT,
        )
        self.assertEqual(self.reloaded(self.visa_application).country, "Wales")

    def test_skips_a_record_that_is_already_correct(self):
        visa_application = VisaApplicationFactory(
            ltla_name="Havant", utla_name="Hampshire", country="England"
        )
        self.visa_application_fixes = [self.fix_for(visa_application)]

        output = self.run_script()

        self.assert_visa_application_skipped(
            output, visa_application.visa_application_id, ALREADY_CORRECT
        )

    def test_skips_an_id_that_appears_more_than_once_in_the_file(self):
        self.visa_application_fixes = [
            self.fix_for(self.visa_application),
            self.fix_for(self.visa_application),
        ]

        output = self.run_script()

        self.assert_visa_application_skipped(
            output, self.visa_application.visa_application_id, DUPLICATE_IN_FILE
        )
        self.assertEqual(self.reloaded(self.visa_application).ltla_name, "Swansea")

    def test_skips_an_id_that_no_longer_exists(self):
        self.visa_application_fixes = [
            VisaApplicationFix(
                visa_application_id="gone",
                ltla_should_have="Havant",
                ltla_changed_to="Swansea",
                utla_should_have="Hampshire",
                utla_changed_to="Swansea",
                country_changed_to="Wales",
            )
        ]

        output = self.run_script()

        self.assert_visa_application_skipped(output, "gone", NOT_FOUND)

    def test_dry_run_writes_nothing(self):
        self.visa_application_fixes = [self.fix_for(self.visa_application)]

        self.run_script(dry_run=True)

        self.assertEqual(self.reloaded(self.visa_application).ltla_name, "Swansea")
        self.assertEqual(self.visa_application.country, "Wales")


class TestReadsBothFilesFirst(FixIncorrectlyAssignedLasTestCase):
    def test_writes_nothing_when_the_second_file_cannot_be_read(self):
        accommodation = MvAccommodationFactory(ltla_name="Highland", utla_name=None)
        self.accommodation_fixes = [
            AccommodationFix(
                accommodation_id=accommodation.id,
                ltla_should_have="Havant",
                ltla_changed_to="Highland",
                utla_should_have="Hampshire",
                utla_changed_to=None,
            )
        ]
        self.visa_applications_loader.side_effect = KeyError("ltla_should_have")

        with self.assertRaises(KeyError):
            fix_incorrectly_assigned_las(dry_run=False)

        self.assertEqual(self.reloaded(accommodation).ltla_name, "Highland")


class TestGetRecordsToProcess(BaseScriptTestCaseWithSession):
    def put_file(self, key: str, body: str):
        s3 = boto3.client("s3", region_name="eu-west-2")
        s3.create_bucket(
            Bucket=settings.MANUAL_DATA_IMPORTS_S3_BUCKET_NAME,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )
        s3.put_object(
            Bucket=settings.MANUAL_DATA_IMPORTS_S3_BUCKET_NAME, Key=key, Body=body
        )

    @mock.patch(
        "hfurb_scripts.fix_incorrectly_assigned_las.ACCOMMODATIONS_FILE_KEY",
        "accommodations.csv",
    )
    @mock.patch.dict(
        os.environ, {"AWS_ENDPOINT_URL": "https://s3.eu-west-2.amazonaws.com"}
    )
    @mock_aws
    def test_reads_the_accommodation_file_and_treats_none_as_null(self):
        self.put_file(
            "accommodations.csv",
            "accommodation_id,utla_should_have,utla_changed_to,ltla_should_have,"
            "ltla_changed_to,ar_id,ar_assigned_to,assigned_at,user_id\n"
            "accommodation-1,Hampshire,None,Havant,Highland,"
            "accommodation_request-1,['Highland'],2026-09-03T08:57:38.138079Z,875\n",
        )

        self.assertEqual(
            get_accommodations_to_process(),
            [
                AccommodationFix(
                    accommodation_id="accommodation-1",
                    ltla_should_have="Havant",
                    ltla_changed_to="Highland",
                    utla_should_have="Hampshire",
                    utla_changed_to=None,
                )
            ],
        )

    @mock.patch(
        "hfurb_scripts.fix_incorrectly_assigned_las.ACCOMMODATIONS_FILE_KEY",
        "accommodations.csv",
    )
    @mock.patch.dict(
        os.environ, {"AWS_ENDPOINT_URL": "https://s3.eu-west-2.amazonaws.com"}
    )
    @mock_aws
    def test_reads_a_file_saved_by_a_spreadsheet(self):
        self.put_file(
            "accommodations.csv",
            "﻿"
            "accommodation_id,utla_should_have,utla_changed_to,ltla_should_have,"
            "ltla_changed_to,ar_id,ar_assigned_to,assigned_at,user_id\r\n"
            "accommodation-1,Hampshire,None,Havant,Highland,"
            "accommodation_request-1,['Highland'],2026-09-03T08:57:38.138079Z,875\r\n",
        )

        self.assertEqual(
            get_accommodations_to_process(),
            [
                AccommodationFix(
                    accommodation_id="accommodation-1",
                    ltla_should_have="Havant",
                    ltla_changed_to="Highland",
                    utla_should_have="Hampshire",
                    utla_changed_to=None,
                )
            ],
        )

    @mock.patch(
        "hfurb_scripts.fix_incorrectly_assigned_las.VISA_APPLICATIONS_FILE_KEY",
        "visa_applications.csv",
    )
    @mock.patch.dict(
        os.environ, {"AWS_ENDPOINT_URL": "https://s3.eu-west-2.amazonaws.com"}
    )
    @mock_aws
    def test_reads_the_visa_application_file_and_treats_null_as_null(self):
        self.put_file(
            "visa_applications.csv",
            "visa_application_id,title_ending,utla_should_have,utla_changed_to,"
            "ltla_should_have,ltla_changed_to,country_changed_to,"
            "databricks_country_reference,ar_id,assigned_at\n"
            "visa-1,....to Hampshire,Hampshire,null,Havant,Highland,Scotland,"
            "England,accommodation_request-1,2026-09-03T08:57:38\n",
        )

        self.assertEqual(
            get_visa_applications_to_process(),
            [
                VisaApplicationFix(
                    visa_application_id="visa-1",
                    ltla_should_have="Havant",
                    ltla_changed_to="Highland",
                    utla_should_have="Hampshire",
                    utla_changed_to=None,
                    country_changed_to="Scotland",
                )
            ],
        )
