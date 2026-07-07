from django.test import TestCase
from django.utils.dateparse import parse_datetime

from ontology.admin_actions import (
    process_single_accommodation_exists_check,
    process_single_accommodation_suitable_check,
    process_single_sponsor_check,
)
from ontology.models import CheckType, DevCheckV2, SafeguardingReferral
from ontology.tests.factories import (
    AccommodationMasterRecordFactory,
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
    SponsorMasterRecordFactory,
)


class ProcessSingleSponsorCheckTest(TestCase):
    def test_it_wont_process_incorrect_date(self):
        sponsor = MvVolunteerFactory(is_principal=False)
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            create_at=None,
        )
        check.sponsor.add(sponsor)

        messages = process_single_sponsor_check(check)

        self.assertEqual(f"[{check.id}]: Missing create_at date", messages[-1])

    def test_it_wont_process_pre_live_checks(self):
        sponsor = MvVolunteerFactory(is_principal=False)
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            create_at=parse_datetime("2025-08-14T23:59:59Z"),
        )
        check.sponsor.add(sponsor)

        messages = process_single_sponsor_check(check)

        self.assertEqual(
            f"[{check.id}]: Created before share 'Go Live' date", messages[-1]
        )

    def test_it_wont_process_pre_live_checks_even_if_only_a_second_before(self):
        sponsor = MvVolunteerFactory(is_principal=False)
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            create_at=parse_datetime("2025-09-14T23:59:59Z"),
        )
        check.sponsor.add(sponsor)

        messages = process_single_sponsor_check(check)

        self.assertEqual(
            f"[{check.id}]: Created before share 'Go Live' date", messages[-1]
        )

    def test_it_wont_process_check_without_master_record(self):
        sponsor = MvVolunteerFactory(is_principal=False)
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            create_at=parse_datetime("2025-10-15T12:00:00Z"),
        )
        check.sponsor.add(sponsor)

        messages = process_single_sponsor_check(check)

        expected_message = (
            f"[{check.id}]:Sponsor with id={sponsor.id} marked with "
            "is_principal=False but is missing a SponsorMasterRecord"
        )

        self.assertEqual(expected_message, messages[-1])

    def test_it_wont_process_check_with_broken_master_records(self):
        sponsor_1 = MvVolunteerFactory(is_principal=False)
        sponsor_2 = MvVolunteerFactory(is_principal=False)
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            create_at=parse_datetime("2025-10-15T12:00:00Z"),
        )
        check.sponsor.add(sponsor_1)

        master_record = SponsorMasterRecordFactory(principal_record_id=None)
        master_record.sponsors.set([sponsor_1, sponsor_2])

        messages = process_single_sponsor_check(check)

        expected_message = (
            f"[{check.id}]: SponsorMasterRecord with id="
            f"{master_record.record_id} has no principal sponsor"
        )

        self.assertEqual(expected_message, messages[-1])

    def test_process_single_sponsor_check_for_passed_check(self):
        # Passed check scenario
        sponsor_1 = MvVolunteerFactory(is_principal=False)
        sponsor_2 = MvVolunteerFactory(is_principal=False)
        sponsor_3 = MvVolunteerFactory(is_principal=True)
        master_record = SponsorMasterRecordFactory(principal_record_id=sponsor_3.id)
        master_record.sponsors.set([sponsor_1, sponsor_2])

        # Passed check
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.PASSED,
            create_at=parse_datetime("2025-10-01T12:00:00Z"),
        )
        check.sponsor.add(sponsor_1)

        self.assertEqual(sponsor_1.checks.count(), 1)
        self.assertEqual(sponsor_3.checks.count(), 0)

        messages = process_single_sponsor_check(check)

        # duplicate record still has the check
        self.assertEqual(sponsor_1.checks.count(), 1)
        # principal record has now a check too
        self.assertEqual(sponsor_3.checks.count(), 1)

        id = check.id
        self.assertEqual(
            f"[{id}]: Start - Solving check on duplicate record", messages[0]
        )
        self.assertEqual(
            f"[{id}]: End - Solving check on duplicate record", messages[-1]
        )

    def test_it_wont_raise_escalation_if_missing_ar_link(self):
        sponsor_1 = MvVolunteerFactory(is_principal=False)
        sponsor_2 = MvVolunteerFactory(is_principal=False)
        sponsor_3 = MvVolunteerFactory(is_principal=True)
        master_record = SponsorMasterRecordFactory(principal_record_id=sponsor_3.id)
        master_record.sponsors.set([sponsor_1, sponsor_2])

        # Failed check
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.FAILED,
            create_at=parse_datetime("2025-10-01T12:00:00Z"),
        )
        check.sponsor.add(sponsor_1)

        person = MvPersonFactory(accommodation_request=None)
        # Unlinked AR
        MvAccommodationRequestFactory(person_id=[person.id])

        self.assertEqual(sponsor_1.checks.count(), 1)
        self.assertEqual(sponsor_3.checks.count(), 0)
        self.assertEqual(SafeguardingReferral.objects.count(), 0)

        messages = process_single_sponsor_check(check)

        # duplicate record still has the check
        self.assertEqual(sponsor_1.checks.count(), 1)
        # principal record has now a check too
        self.assertEqual(sponsor_3.checks.count(), 1)
        # Escalation created
        self.assertEqual(SafeguardingReferral.objects.count(), 0)

        new_check = sponsor_3.checks.first()
        expected_message = (
            f"[{check.id}]: Escalation not raised for new failed "
            f"check with id={new_check.id} linked against principal"
            f" sponsor with id={sponsor_3.id}. Principal "
            "sponsor not attached to any ARs"
        )

        self.assertEqual(expected_message, messages[-1])

    def test_process_single_sponsor_check_for_failed_check(self):
        sponsor_1 = MvVolunteerFactory(is_principal=False)
        sponsor_2 = MvVolunteerFactory(is_principal=False)
        sponsor_3 = MvVolunteerFactory(is_principal=True)
        master_record = SponsorMasterRecordFactory(principal_record_id=sponsor_3.id)
        master_record.sponsors.set([sponsor_1, sponsor_2])

        # Failed check
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.FAILED,
            create_at=parse_datetime("2025-10-01T12:00:00Z"),
        )
        check.sponsor.add(sponsor_1)

        person = MvPersonFactory(accommodation_request=None)
        MvAccommodationRequestFactory(primary_sponsor=sponsor_3, person_id=[person.id])

        self.assertEqual(sponsor_1.checks.count(), 1)
        self.assertEqual(sponsor_3.checks.count(), 0)
        self.assertEqual(SafeguardingReferral.objects.count(), 0)

        messages = process_single_sponsor_check(check)

        # duplicate record still has the check
        self.assertEqual(sponsor_1.checks.count(), 1)
        # principal record has now a check too
        self.assertEqual(sponsor_3.checks.count(), 1)
        # Escalation created
        self.assertEqual(SafeguardingReferral.objects.count(), 1)
        # Escalated check is against the right person
        escalated_check = SafeguardingReferral.objects.first()
        self.assertEqual(escalated_check.person.id, person.id)

        id = check.id
        self.assertEqual(
            f"[{id}]: Start - Solving check on duplicate record", messages[0]
        )
        self.assertEqual(
            f"[{id}]: End - Solving check on duplicate record", messages[-1]
        )

    def test_process_single_sponsor_check_wont_duplicate_check_if_exists_already(self):
        sponsor_1 = MvVolunteerFactory(is_principal=False)
        sponsor_2 = MvVolunteerFactory(is_principal=False)
        sponsor_3 = MvVolunteerFactory(is_principal=True)
        master_record = SponsorMasterRecordFactory(principal_record_id=sponsor_3.id)
        master_record.sponsors.set([sponsor_1, sponsor_2])

        self.devcheck_7 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.PASSED,
            create_at=parse_datetime("2025-10-01T12:00:00Z"),
        )
        self.devcheck_7.sponsor.add(sponsor_1)

        self.devcheck_8 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
        )
        self.devcheck_8.sponsor.add(sponsor_3)

        self.assertEqual(sponsor_1.checks.count(), 1)
        self.assertEqual(sponsor_3.checks.count(), 1)

        messages = process_single_sponsor_check(self.devcheck_7)

        # duplicate record still has the check
        self.assertEqual(sponsor_1.checks.count(), 1)
        # principal record has name number of checks still
        self.assertEqual(sponsor_3.checks.count(), 1)

        id = self.devcheck_7.id
        self.assertIn(f"[{id}]: Start - Solving check on duplicate record", messages)

        expected_message = (
            f"[{id}]: Principal sponsor with id="
            f"{sponsor_3.id} already has a check of "
            "this type, not duplicating"
        )

        self.assertEqual(expected_message, messages[-1])


class ProcessSingleAccommodationExistsCheckTest(TestCase):
    def test_it_wont_process_incorrect_check_type(self):
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
        )

        messages = process_single_accommodation_exists_check(check)

        self.assertEqual(
            f"[{check.id}]: Is not an Accommodation exists type check", messages[-1]
        )

    def test_it_wont_process_incorrect_date(self):
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            create_at=None,
        )

        messages = process_single_accommodation_exists_check(check)

        self.assertEqual(f"[{check.id}]: Missing create_at date", messages[-1])

    def test_it_wont_process_pre_live_checks(self):
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            create_at=parse_datetime("2025-09-14T23:59:59Z"),
        )

        messages = process_single_accommodation_exists_check(check)

        self.assertEqual(
            f"[{check.id}]: Created before share 'Go Live' date", messages[-1]
        )

    def test_it_wont_process_if_missing_linked_dup_record(self):
        accommodation = MvAccommodationFactory(is_principal=True)
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            create_at=parse_datetime("2025-10-15T12:00:00Z"),
        )
        check.accommodation.add(accommodation)

        messages = process_single_accommodation_exists_check(check)

        expected_message = (
            f"[{check.id}]: Is not linked to duplicate accommodation record"
        )

        self.assertEqual(expected_message, messages[-1])

    def test_it_wont_process_check_without_master_record(self):
        accommodation = MvAccommodationFactory(full_address="", is_principal=False)
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            create_at=parse_datetime("2025-10-15T12:00:00Z"),
        )
        check.accommodation.add(accommodation)

        messages = process_single_accommodation_exists_check(check)

        expected_message = (
            f"[{check.id}]:Accommodation with id={accommodation.id} marked "
            "with is_principal=False but is missing a AccommodationMasterRecord"
        )

        self.assertEqual(expected_message, messages[-1])

    def test_it_wont_process_check_with_broken_master_records(self):
        accommodation_1 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_2 = MvAccommodationFactory(full_address="", is_principal=False)

        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            create_at=parse_datetime("2025-10-15T12:00:00Z"),
        )
        check.accommodation.add(accommodation_1)

        master_record = AccommodationMasterRecordFactory(principal_record_id=None)
        master_record.accommodations.set([accommodation_1, accommodation_2])

        messages = process_single_accommodation_exists_check(check)

        expected_message = (
            f"[{check.id}]: AccommodationMasterRecord with id="
            f"{master_record.record_id} has no principal accommodation"
        )

        self.assertEqual(expected_message, messages[-1])

    def test_it_wont_process_if_check_already_exists(self):
        accommodation_1 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_2 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_3 = MvAccommodationFactory(full_address="", is_principal=True)
        master_record = AccommodationMasterRecordFactory(
            principal_record_id=accommodation_3.id
        )
        master_record.accommodations.set([accommodation_1, accommodation_2])

        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            create_at=parse_datetime("2025-10-15T12:00:00Z"),
        )
        check.accommodation.add(accommodation_1)

        check_2 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            create_at=parse_datetime("2025-10-15T12:00:00Z"),
        )
        check_2.accommodation.add(accommodation_3)

        master_record = AccommodationMasterRecordFactory()
        master_record.accommodations.set(
            [accommodation_1, accommodation_2, accommodation_3]
        )

        self.assertEqual(accommodation_1.checks.count(), 1)
        self.assertEqual(accommodation_3.checks.count(), 1)

        messages = process_single_accommodation_exists_check(check)

        # duplicate record still has the check
        self.assertEqual(accommodation_1.checks.count(), 1)
        # principal record has now a check too
        self.assertEqual(accommodation_3.checks.count(), 1)

        expected_message = (
            f"[{check.id}]: Principal accommodation with id="
            f"{accommodation_3.id} already has a check of "
            "this type, not duplicating"
        )

        self.assertEqual(expected_message, messages[-1])

    def test_it_duplicates_passed_check(self):
        accommodation_1 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_2 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_3 = MvAccommodationFactory(full_address="", is_principal=True)
        master_record = AccommodationMasterRecordFactory(
            principal_record_id=accommodation_3.id
        )
        master_record.accommodations.set([accommodation_1, accommodation_2])

        passed_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            check_status=DevCheckV2.CheckStatus.PASSED,
            create_at=parse_datetime("2025-10-01T12:00:00Z"),
        )
        passed_check.accommodation.add(accommodation_1)

        self.assertEqual(accommodation_1.checks.count(), 1)
        self.assertEqual(accommodation_3.checks.count(), 0)

        messages = process_single_accommodation_exists_check(passed_check)

        # duplicate record still has the check
        self.assertEqual(accommodation_1.checks.count(), 1)
        # principal record has now a check too
        self.assertEqual(accommodation_3.checks.count(), 1)

        id = passed_check.id
        self.assertEqual(
            f"[{id}]: Start - Solving check on duplicate record", messages[0]
        )
        self.assertEqual(
            f"[{id}]: End - Solving check on duplicate record", messages[-1]
        )

    def test_it_wont_duplicates_failed_check(self):
        accommodation_1 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_2 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_3 = MvAccommodationFactory(full_address="", is_principal=True)
        master_record = AccommodationMasterRecordFactory(
            principal_record_id=accommodation_3.id
        )
        master_record.accommodations.set([accommodation_1, accommodation_2])

        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            check_status=DevCheckV2.CheckStatus.FAILED,
            create_at=parse_datetime("2025-10-01T12:00:00Z"),
        )
        check.accommodation.add(accommodation_1)

        self.assertEqual(accommodation_1.checks.count(), 1)
        self.assertEqual(accommodation_3.checks.count(), 0)
        self.assertEqual(SafeguardingReferral.objects.count(), 0)

        messages = process_single_accommodation_exists_check(check)

        # duplicate record still has the check
        self.assertEqual(accommodation_1.checks.count(), 1)
        # principal record has now a check too
        self.assertEqual(accommodation_3.checks.count(), 1)
        # Escalation not created
        self.assertEqual(SafeguardingReferral.objects.count(), 0)

        new_check = accommodation_3.checks.first()
        expected_message = (
            f"[{check.id}]: Escalation not raised for new failed "
            f"check with id={new_check.id} linked against principal"
            f" accommodation with id={accommodation_3.id}. "
            "Principal accommodation not attached to any ARs"
        )

        self.assertEqual(expected_message, messages[-1])

    def test_it_duplicates_failed_check(self):
        accommodation_1 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_2 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_3 = MvAccommodationFactory(full_address="", is_principal=True)
        master_record = AccommodationMasterRecordFactory(
            principal_record_id=accommodation_3.id
        )
        master_record.accommodations.set([accommodation_1, accommodation_2])

        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            check_status=DevCheckV2.CheckStatus.FAILED,
            create_at=parse_datetime("2025-10-01T12:00:00Z"),
        )
        check.accommodation.add(accommodation_1)

        person = MvPersonFactory(id="person_1", accommodation_request=None)
        MvAccommodationRequestFactory(
            primary_accommodation=accommodation_3,
            person_id=[person.id],
        )

        self.assertEqual(accommodation_1.checks.count(), 1)
        self.assertEqual(accommodation_3.checks.count(), 0)
        self.assertEqual(SafeguardingReferral.objects.count(), 0)

        messages = process_single_accommodation_exists_check(check)

        # duplicate record still has the check
        self.assertEqual(accommodation_1.checks.count(), 1)
        # principal record has now a check too
        self.assertEqual(accommodation_3.checks.count(), 1)
        # Escalation created
        self.assertEqual(SafeguardingReferral.objects.count(), 1)
        # Escalated check is against the right person
        escalated_check = SafeguardingReferral.objects.first()
        self.assertEqual(escalated_check.person.id, person.id)

        id = check.id
        self.assertEqual(
            f"[{id}]: Start - Solving check on duplicate record", messages[0]
        )
        self.assertEqual(
            f"[{id}]: End - Solving check on duplicate record", messages[-1]
        )


class ProcessSingleAccommodationSuitableCheckTest(TestCase):
    def test_it_wont_process_incorrect_check_type(self):
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
        )

        messages = process_single_accommodation_suitable_check(check)

        self.assertEqual(
            f"[{check.id}]: Is not an Accommodation suitable type check", messages[-1]
        )

    def test_it_wont_process_incorrect_date(self):
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            create_at=None,
        )

        messages = process_single_accommodation_suitable_check(check)

        self.assertEqual(f"[{check.id}]: Missing create_at date", messages[-1])

    def test_it_wont_process_pre_live_checks(self):
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            create_at=parse_datetime("2025-09-14T23:59:59Z"),
        )

        messages = process_single_accommodation_suitable_check(check)

        self.assertEqual(
            f"[{check.id}]: Created before share 'Go Live' date", messages[-1]
        )

    def test_it_wont_process_if_missing_linked_dup_record(self):
        accommodation = MvAccommodationFactory(is_principal=True)
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            create_at=parse_datetime("2025-10-15T12:00:00Z"),
        )
        check.accommodation.add(accommodation)

        messages = process_single_accommodation_suitable_check(check)

        expected_message = (
            f"[{check.id}]: Is not linked to duplicate accommodation record"
        )

        self.assertEqual(expected_message, messages[-1])

    def test_it_wont_process_check_without_master_record(self):
        accommodation = MvAccommodationFactory(full_address="", is_principal=False)
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            create_at=parse_datetime("2025-10-15T12:00:00Z"),
        )
        check.accommodation.add(accommodation)

        messages = process_single_accommodation_suitable_check(check)

        expected_message = (
            f"[{check.id}]:Accommodation with id={accommodation.id} marked "
            "with is_principal=False but is missing a AccommodationMasterRecord"
        )

        self.assertEqual(expected_message, messages[-1])

    def test_it_wont_process_check_with_broken_master_records(self):
        accommodation_1 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_2 = MvAccommodationFactory(full_address="", is_principal=False)
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            create_at=parse_datetime("2025-10-15T12:00:00Z"),
        )
        check.accommodation.add(accommodation_1)

        master_record = AccommodationMasterRecordFactory(principal_record_id=None)
        master_record.accommodations.set([accommodation_1, accommodation_2])

        messages = process_single_accommodation_suitable_check(check)

        expected_message = (
            f"[{check.id}]: AccommodationMasterRecord with id="
            f"{master_record.record_id} has no principal accommodation"
        )

        self.assertEqual(expected_message, messages[-1])

    def test_it_wont_process_check_with_missing_ar_link(self):
        accommodation_1 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_2 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_3 = MvAccommodationFactory(full_address="", is_principal=True)
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            create_at=parse_datetime("2025-10-15T12:00:00Z"),
        )
        check.accommodation.add(accommodation_1)

        master_record = AccommodationMasterRecordFactory(
            principal_record_id=accommodation_3.id
        )
        master_record.accommodations.set([accommodation_1, accommodation_2])

        messages = process_single_accommodation_suitable_check(check)

        expected_message = (
            f"[{check.id}]: Escalation not raised. Check with id={check.id} "
            "is not attached to any ARs"
        )

        self.assertEqual(expected_message, messages[-1])

    def test_it_wont_duplicate_check_if_principal_already_has_it(self):
        accommodation_1 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_2 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_3 = MvAccommodationFactory(full_address="", is_principal=True)

        person = MvPersonFactory(accommodation_request=None)
        accommodation_request = MvAccommodationRequestFactory(person_id=[person.id])

        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            create_at=parse_datetime("2025-10-15T12:00:00Z"),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        check.accommodation.add(accommodation_1)
        check.AR.add(accommodation_request)

        check_2 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            create_at=parse_datetime("2025-10-15T12:00:00Z"),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        check_2.accommodation.add(accommodation_3)
        check_2.AR.add(accommodation_request)

        master_record = AccommodationMasterRecordFactory(
            principal_record_id=accommodation_3.id
        )
        master_record.accommodations.set([accommodation_1, accommodation_2])

        self.assertEqual(accommodation_1.checks.count(), 1)
        self.assertEqual(accommodation_3.checks.count(), 1)

        messages = process_single_accommodation_suitable_check(check)

        # duplicate record still has the check
        self.assertEqual(accommodation_1.checks.count(), 1)
        # principal record still has one check
        self.assertEqual(accommodation_3.checks.count(), 1)

        self.assertEqual(
            (
                f"[{check.id}]: Principal accommodation with id="
                f"{accommodation_3.id} already has a check of "
                "this type, not duplicating"
            ),
            messages[-1],
        )

    def test_it_will_duplicate_passing_check(self):
        accommodation_1 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_2 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_3 = MvAccommodationFactory(full_address="", is_principal=True)

        person = MvPersonFactory(accommodation_request=None)
        accommodation_request = MvAccommodationRequestFactory(person_id=[person.id])

        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            create_at=parse_datetime("2025-10-15T12:00:00Z"),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        check.accommodation.add(accommodation_1)
        check.AR.add(accommodation_request)

        master_record = AccommodationMasterRecordFactory(
            principal_record_id=accommodation_3.id
        )
        master_record.accommodations.set([accommodation_1, accommodation_2])

        self.assertEqual(accommodation_1.checks.count(), 1)
        self.assertEqual(accommodation_3.checks.count(), 0)

        messages = process_single_accommodation_suitable_check(check)

        # duplicate record still has the check
        self.assertEqual(accommodation_1.checks.count(), 1)
        # principal record has now a check too
        self.assertEqual(accommodation_3.checks.count(), 1)

        id = check.id
        self.assertEqual(
            f"[{id}]: Start - Solving check on duplicate record", messages[0]
        )
        self.assertEqual(
            f"[{id}]: End - Solving check on duplicate record", messages[-1]
        )

    def test_it_duplicates_failed_check(self):
        accommodation_1 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_2 = MvAccommodationFactory(full_address="", is_principal=False)
        accommodation_3 = MvAccommodationFactory(full_address="", is_principal=True)
        master_record = AccommodationMasterRecordFactory(
            principal_record_id=accommodation_3.id
        )
        master_record.accommodations.set([accommodation_1, accommodation_2])

        person = MvPersonFactory(accommodation_request=None)
        accommodation_request = MvAccommodationRequestFactory(person_id=[person.id])

        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            check_status=DevCheckV2.CheckStatus.FAILED,
            create_at=parse_datetime("2025-10-01T12:00:00Z"),
        )
        check.accommodation.add(accommodation_1)
        check.AR.add(accommodation_request)

        self.assertEqual(accommodation_1.checks.count(), 1)
        self.assertEqual(accommodation_3.checks.count(), 0)
        self.assertEqual(SafeguardingReferral.objects.count(), 0)

        messages = process_single_accommodation_suitable_check(check)

        # duplicate record still has the check
        self.assertEqual(accommodation_1.checks.count(), 1)
        # principal record has now a check too
        self.assertEqual(accommodation_3.checks.count(), 1)
        # Escalation created
        self.assertEqual(SafeguardingReferral.objects.count(), 1)
        # Escalated check is against the right person
        escalated_check = SafeguardingReferral.objects.first()
        self.assertEqual(escalated_check.person.id, person.id)

        id = check.id
        self.assertEqual(
            f"[{id}]: Start - Solving check on duplicate record", messages[0]
        )
        self.assertEqual(
            f"[{id}]: End - Solving check on duplicate record", messages[-1]
        )
