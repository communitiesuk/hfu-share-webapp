from django.test import TestCase

from ontology.models import CheckType, DevCheckV2
from ontology.tests.factories import DevCheckV2Factory, MvVolunteerFactory


class MvVolunteerDetermineDBSCheckStatusTest(TestCase):
    def setUp(self):
        super().setUp()
        self.sponsor = MvVolunteerFactory(
            first_name="Test",
            last_name="Sponsor",
            date_of_birth="2002-06-03",
            sex="Female",
            email="test@example.com",
            phone_number=["0123456789"],
            family_situation="Single",
            passport_details=["123456"],
            is_eoi=True,
            is_sponsor=False,
        )

        self.dbs_check_failed = DevCheckV2Factory(
            active=True,
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        self.dbs_check_in_progress = DevCheckV2Factory(
            active=True,
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.IN_PROGRESS,
        )
        self.dbs_check_no_longer_needed = DevCheckV2Factory(
            active=True,
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.NO_LONGER_NEEDED,
        )
        self.dbs_check_passed = DevCheckV2Factory(
            active=True,
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        self.dbs_check_not_started = DevCheckV2Factory(
            active=True,
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.NOT_STARTED,
        )

    def test_returns_not_started_if_no_recorded_checks(self):
        self.dbs_check_failed.sponsor.set([])
        self.dbs_check_in_progress.sponsor.set([])
        self.dbs_check_no_longer_needed.sponsor.set([])
        self.dbs_check_passed.sponsor.set([])
        self.dbs_check_not_started.sponsor.set([])

        self.assertEqual(
            self.sponsor.determine_dbs_check_status(),
            DevCheckV2.CheckStatus.NOT_STARTED,
        )

    def test_returns_failed_if_any_failed_checks(self):
        self.dbs_check_failed.sponsor.set([self.sponsor])
        self.dbs_check_in_progress.sponsor.set([self.sponsor])
        self.dbs_check_no_longer_needed.sponsor.set([self.sponsor])
        self.dbs_check_passed.sponsor.set([self.sponsor])
        self.dbs_check_not_started.sponsor.set([self.sponsor])

        self.assertEqual(
            self.sponsor.determine_dbs_check_status(), DevCheckV2.CheckStatus.FAILED
        )

    def test_returns_in_progress_if_any_in_progress_and_no_failed_checks(self):
        self.dbs_check_failed.sponsor.set([])
        self.dbs_check_in_progress.sponsor.set([self.sponsor])
        self.dbs_check_no_longer_needed.sponsor.set([self.sponsor])
        self.dbs_check_passed.sponsor.set([self.sponsor])
        self.dbs_check_not_started.sponsor.set([self.sponsor])

        self.assertEqual(
            self.sponsor.determine_dbs_check_status(),
            DevCheckV2.CheckStatus.IN_PROGRESS,
        )

    def test_returns_no_longer_needed_if_no_higher_priority_checks(self):
        self.dbs_check_failed.sponsor.set([])
        self.dbs_check_in_progress.sponsor.set([])
        self.dbs_check_no_longer_needed.sponsor.set([self.sponsor])
        self.dbs_check_passed.sponsor.set([self.sponsor])
        self.dbs_check_not_started.sponsor.set([self.sponsor])

        self.assertEqual(
            self.sponsor.determine_dbs_check_status(),
            DevCheckV2.CheckStatus.NO_LONGER_NEEDED,
        )

    def test_returns_passed_if_any_passed_checks_and_no_higher_priority_checks(self):
        self.dbs_check_failed.sponsor.set([])
        self.dbs_check_in_progress.sponsor.set([])
        self.dbs_check_no_longer_needed.sponsor.set([])
        self.dbs_check_passed.sponsor.set([self.sponsor])
        self.dbs_check_not_started.sponsor.set([self.sponsor])

        self.assertEqual(
            self.sponsor.determine_dbs_check_status(), DevCheckV2.CheckStatus.PASSED
        )

    def test_returns_not_started_if_no_other_checks_recorded(self):
        self.dbs_check_failed.sponsor.set([])
        self.dbs_check_in_progress.sponsor.set([])
        self.dbs_check_no_longer_needed.sponsor.set([])
        self.dbs_check_passed.sponsor.set([])
        self.dbs_check_not_started.sponsor.set([self.sponsor])

        self.assertEqual(
            self.sponsor.determine_dbs_check_status(),
            DevCheckV2.CheckStatus.NOT_STARTED,
        )

    def test_handles_sentence_case_status_value(self):
        self.dbs_check_passed.check_status = "Passed"
        self.dbs_check_in_progress.save()

        self.dbs_check_passed.sponsor.set([self.sponsor])

        self.assertEqual(
            self.sponsor.determine_dbs_check_status(), DevCheckV2.CheckStatus.PASSED
        )

    def test_handles_all_caps_status_value(self):
        self.dbs_check_passed.check_status = "PASSED"
        self.dbs_check_in_progress.save()

        self.dbs_check_passed.sponsor.set([self.sponsor])

        self.assertEqual(
            self.sponsor.determine_dbs_check_status(), DevCheckV2.CheckStatus.PASSED
        )

    def test_handles_multi_word_status_value(self):
        self.dbs_check_in_progress.check_status = "In progress"
        self.dbs_check_in_progress.save()

        self.dbs_check_in_progress.sponsor.set([self.sponsor])

        self.assertEqual(
            self.sponsor.determine_dbs_check_status(),
            DevCheckV2.CheckStatus.IN_PROGRESS,
        )

    def test_handles_underscore_status_value(self):
        self.dbs_check_in_progress.check_status = "IN_PROGRESS"
        self.dbs_check_in_progress.save()

        self.dbs_check_in_progress.sponsor.set([self.sponsor])

        self.assertEqual(
            self.sponsor.determine_dbs_check_status(),
            DevCheckV2.CheckStatus.IN_PROGRESS,
        )

    def test_handles_no_longer_required_case(self):
        self.dbs_check_in_progress.check_status = "No longer required"
        self.dbs_check_in_progress.save()

        self.dbs_check_in_progress.sponsor.set([self.sponsor])

        self.assertEqual(
            self.sponsor.determine_dbs_check_status(),
            DevCheckV2.CheckStatus.NO_LONGER_NEEDED,
        )

    def test_handles_unexpected_status_value(self):
        self.dbs_check_in_progress.check_status = "Unexpected status"
        self.dbs_check_in_progress.save()

        self.dbs_check_in_progress.sponsor.set([self.sponsor])

        self.assertEqual(
            self.sponsor.determine_dbs_check_status(),
            DevCheckV2.CheckStatus.UNAVAILABLE,
        )
