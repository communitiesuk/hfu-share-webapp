from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone
from freezegun import freeze_time

from deduplication.tests.factories import SponsorDuplicateGroupFactory
from ontology.models import CheckType, DevCheckV2, MvAccommodationRequest, MvVolunteer
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import get_admin_user


class SponsorDuplicateGroupUndoDeduplicationTestCase(TestCase):
    def test_should_set_is_principal_true_to_all_undo_deduplicated_sponsors(self):
        self.sponsor_one = MvVolunteerFactory(is_principal=True)
        self.sponsor_two = MvVolunteerFactory(is_principal=True)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.duplicate_group.undo_deduplication(user=get_admin_user())

        self.sponsor_one.refresh_from_db()
        self.sponsor_two.refresh_from_db()

        self.assertTrue(self.sponsor_one.is_principal, True)
        self.assertTrue(self.sponsor_two.is_principal, True)

    def test_should_remove_principal_from_safeguarding_checks(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        sponsor_one_safeguarding_check = DevCheckV2Factory(
            active=True,
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        sponsor_one_safeguarding_check.sponsor.set([sponsor_one])

        sponsor_two = MvVolunteerFactory(is_principal=True)
        sponsor_two_safeguarding_check = DevCheckV2Factory(
            active=True,
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        sponsor_two_safeguarding_check.sponsor.set([sponsor_two])

        duplicate_group = SponsorDuplicateGroupFactory()

        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        sponsor_one_safeguarding_check.refresh_from_db()
        sponsor_two_safeguarding_check.refresh_from_db()

        duplicate_group.undo_deduplication(user=get_admin_user())

        self.assertEqual(len(sponsor_one_safeguarding_check.sponsor.all()), 1)
        self.assertIn(
            sponsor_one,
            sponsor_one_safeguarding_check.sponsor.all(),
        )
        self.assertEqual(len(sponsor_two_safeguarding_check.sponsor.all()), 1)
        self.assertIn(
            sponsor_two,
            sponsor_two_safeguarding_check.sponsor.all(),
        )

    def test_should_link_accommodation_back_to_original_sponsor_removing_principal(
        self,
    ):
        self.accommodation_one = MvAccommodationFactory()
        self.sponsor_one = MvVolunteerFactory(first_name="test1", is_principal=True)
        self.sponsor_one.accommodations.add(self.accommodation_one)

        self.accommodation_two = MvAccommodationFactory()
        self.accommodation_three = MvAccommodationFactory()
        self.sponsor_two = MvVolunteerFactory(first_name="test2", is_principal=True)
        self.sponsor_two.accommodations.add(self.accommodation_two)
        self.sponsor_two.accommodations.add(self.accommodation_three)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.duplicate_group.undo_deduplication(user=get_admin_user())

        self.accommodation_one.refresh_from_db()
        self.accommodation_two.refresh_from_db()
        self.accommodation_three.refresh_from_db()

        self.assertEqual(self.accommodation_one.volunteer, self.sponsor_one)
        self.assertEqual(self.accommodation_two.volunteer, self.sponsor_two)
        self.assertEqual(self.accommodation_three.volunteer, self.sponsor_two)

    def test_should_link_constituents_back_to_relevant_ars(self):
        sponsor_one = MvVolunteerFactory(first_name="test1", is_principal=True)
        accommodation_request_one = MvAccommodationRequestFactory(
            active_host=sponsor_one,
            sponsor_id=[sponsor_one.pk],
            primary_sponsor=sponsor_one,
        )

        sponsor_two = MvVolunteerFactory(first_name="test1", is_principal=True)
        accommodation_request_two = MvAccommodationRequestFactory(
            active_host=sponsor_two,
            sponsor_id=[sponsor_two.pk],
            primary_sponsor=sponsor_two,
        )

        duplicate_group = SponsorDuplicateGroupFactory()

        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )
        duplicate_group.undo_deduplication(user=get_admin_user())

        accommodation_request_one.refresh_from_db()
        accommodation_request_two.refresh_from_db()

        self.assertEqual(accommodation_request_one.sponsor_id, [sponsor_one.pk])
        self.assertEqual(accommodation_request_two.sponsor_id, [sponsor_two.pk])

        self.assertEqual(accommodation_request_one.primary_sponsor, sponsor_one)
        self.assertEqual(accommodation_request_two.primary_sponsor, sponsor_two)

        self.assertEqual(accommodation_request_one.active_host, sponsor_one)
        self.assertEqual(accommodation_request_two.active_host, sponsor_two)

    @freeze_time("2026-02-25 12:00:00")
    def test_should_set_principal_record_to_archived(self):
        self.sponsor_one = MvVolunteerFactory(is_principal=True)
        self.sponsor_two = MvVolunteerFactory(is_principal=True)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.principal_record = MvVolunteer.objects.filter(
            pk=self.duplicate_group.principal_record.id
        ).first()

        self.duplicate_group.undo_deduplication(user=get_admin_user())

        self.principal_record.refresh_from_db()
        self.duplicate_group.refresh_from_db()

        self.assertFalse(self.principal_record.is_principal)
        self.assertTrue(self.principal_record.is_archived)
        self.assertEqual(self.principal_record.archived_at, timezone.now())
        self.assertEqual(self.duplicate_group.archived_at, timezone.now())
        self.assertTrue(self.duplicate_group.is_archived)
        self.assertIsNotNone(self.duplicate_group.principal_record)

    def test_undo_handles_null_sponsor_id_returned_via_primary_sponsor(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        sponsor_two = MvVolunteerFactory(is_principal=True)
        ar = MvAccommodationRequestFactory(
            primary_sponsor=sponsor_one,
            sponsor_id=[sponsor_one.pk],
        )

        duplicate_group = SponsorDuplicateGroupFactory()
        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"},
            user=get_admin_user(),
        )

        ar.refresh_from_db()
        ar.sponsor_id = None
        ar.save()

        # Should not raise error
        duplicate_group.undo_deduplication(user=get_admin_user())

        ar.refresh_from_db()
        self.assertEqual(ar.primary_sponsor, sponsor_one)
        self.assertIn(sponsor_one.pk, ar.sponsor_id or [])

    def test_undo_restores_all_constituent_sponsors_on_shared_ar(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        sponsor_two = MvVolunteerFactory(is_principal=True)
        ar = MvAccommodationRequestFactory(
            sponsor_id=[sponsor_one.pk, sponsor_two.pk],
        )

        duplicate_group = SponsorDuplicateGroupFactory()
        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"},
            user=get_admin_user(),
        )
        duplicate_group.undo_deduplication(user=get_admin_user())

        ar.refresh_from_db()
        self.assertIn(sponsor_one.pk, ar.sponsor_id or [])
        self.assertIn(sponsor_two.pk, ar.sponsor_id or [])

    def test_undedupe_recalculates_checks_on_linked_ars_failed_checks(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        sponsor_two = MvVolunteerFactory(is_principal=True)
        ar = MvAccommodationRequestFactory(
            sponsor_id=[sponsor_one.pk, sponsor_two.pk],
        )

        duplicate_group = SponsorDuplicateGroupFactory()
        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        sponsor_dbs_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
        )
        sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.FAILED

        sponsor_dbs_check.sponsor.set([sponsor_one])

        sponsor_dbs_check.save()

        ar.checks_status = ar.determine_checks_status_from_linked_objects()

        self.assertEqual(
            ar.checks_status,
            MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED,
        )

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"},
            user=get_admin_user(),
        )

        ar.refresh_from_db()
        self.assertEqual(
            ar.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

        duplicate_group.undo_deduplication(user=get_admin_user())
        ar.refresh_from_db()

        self.assertEqual(
            ar.checks_status,
            MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED,
        )

    def test_undedupe_recalculates_checks_on_linked_ars_passed_checks(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        sponsor_two = MvVolunteerFactory(is_principal=True)
        ar = MvAccommodationRequestFactory(
            sponsor_id=[sponsor_one.pk, sponsor_two.pk],
        )

        duplicate_group = SponsorDuplicateGroupFactory()
        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        sponsor_dbs_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
        )
        sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED

        sponsor_dbs_check.sponsor.set([sponsor_one])

        sponsor_dbs_check.save()

        ar.checks_status = ar.determine_checks_status_from_linked_objects()

        self.assertEqual(
            ar.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED,
        )

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"},
            user=get_admin_user(),
        )

        ar.refresh_from_db()
        self.assertEqual(
            ar.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

        duplicate_group.undo_deduplication(user=get_admin_user())
        ar.refresh_from_db()

        self.assertEqual(
            ar.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED,
        )

    @override_settings(ENHANCED_DEDUPLICATION_LOGGING=True)
    def test_undo_emits_started_and_finished_sentry_logs(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        sponsor_two = MvVolunteerFactory(is_principal=True)
        duplicate_group = SponsorDuplicateGroupFactory()
        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()
        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"},
            user=get_admin_user(),
        )

        with patch("sentry_sdk.logger.info") as info:
            duplicate_group.undo_deduplication(user=get_admin_user())

        messages = [call.args[0] for call in info.call_args_list]
        self.assertIn("SponsorDuplicateGroup.undo_deduplication: started", messages)
        self.assertIn("SponsorDuplicateGroup.undo_deduplication: finished", messages)

    def test_undo_emits_completed_sentry_metric(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        sponsor_two = MvVolunteerFactory(is_principal=True)
        duplicate_group = SponsorDuplicateGroupFactory()
        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()
        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"},
            user=get_admin_user(),
        )

        with patch("sentry_sdk.metrics.count") as count:
            duplicate_group.undo_deduplication(user=get_admin_user())

        count.assert_called_once_with(
            "undo_deduplication.completed",
            1,
            attributes={"record_type": "sponsor"},
        )
