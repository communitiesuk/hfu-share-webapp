from unittest import mock

from django.db import DatabaseError

from accounts.tests.base import TestSessionTokenMixin
from hfurb_scripts.fix_guest_records_pointing_to_wrong_ars import run
from ontology.models import MvAccommodationRequest, MvPerson
from ontology.tests.factories import MvAccommodationRequestFactory, MvPersonFactory
from test_utils.base import BaseTestCase


@mock.patch("hfurb_scripts.fix_guest_records_pointing_to_wrong_ars.logger")
class TestFixGuestRecordsPointingToWrongARs(TestSessionTokenMixin, BaseTestCase):
    def setUp(self):
        super().setUp()

        # Scenario 0 - Records are linked correctly
        self.guest_correct = MvPersonFactory()
        self.ar_correct = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED
        )
        self.guest_correct.accommodation_request_id = self.ar_correct.id
        self.ar_correct.person_id = [self.guest_correct.id]

        self.guest_correct.save()
        self.ar_correct.save()

        # Scenario 1 - AR is linked to the guest and guest is linked to AR
        # which is not linked to the guest
        self.guest_scenario_1 = MvPersonFactory()
        self.ar_scenario_1_correct_ar = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )
        self.ar_scenario_1_wrong_ar = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED
        )
        self.guest_scenario_1.accommodation_request_id = self.ar_scenario_1_wrong_ar.id
        self.ar_scenario_1_correct_ar.person_id = [self.guest_scenario_1.id]

        self.guest_scenario_1.save()
        self.ar_scenario_1_correct_ar.save()

        # Scenario 2 - AR is linked to guest and guest is linked to closed AR
        self.guest_scenario_2 = MvPersonFactory()
        self.ar_scenario_2_open_ar = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED
        )
        self.ar_scenario_2_closed_ar = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CANCELLED
        )

        self.guest_scenario_2.accommodation_request_id = self.ar_scenario_2_closed_ar.id
        self.ar_scenario_2_open_ar.person_id = [self.guest_scenario_2.id]
        self.ar_scenario_2_closed_ar.person_id = [self.guest_scenario_2.id]

        self.guest_scenario_2.save()
        self.ar_scenario_2_open_ar.save()
        self.ar_scenario_2_closed_ar.save()

        # Scenario 3 - Open AR is linked to guest, closed AR is linked to guest and
        # guest is linked to some other AR
        self.guest_scenario_3 = MvPersonFactory()
        self.ar_scenario_3_open_ar = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )
        self.ar_scenario_3_closed_ar = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CANCELLED
        )
        self.ar_scenario_3_other_ar = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )

        self.guest_scenario_3.accommodation_request_id = self.ar_scenario_3_other_ar.id
        self.ar_scenario_3_open_ar.person_id = [self.guest_scenario_3.id]
        self.ar_scenario_3_closed_ar.person_id = [self.guest_scenario_3.id]

        self.guest_scenario_3.save()
        self.ar_scenario_3_open_ar.save()
        self.ar_scenario_3_closed_ar.save()

        # Scenario 4 - 2 open ARs are linked to guest and guest is linked to one AR
        self.guest_scenario_4 = MvPersonFactory()
        self.ar_scenario_4_open_ar_1 = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED
        )
        self.ar_scenario_4_open_ar_2 = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED
        )

        self.guest_scenario_4.accommodation_request_id = self.ar_scenario_4_open_ar_2.id
        self.ar_scenario_4_open_ar_1.person_id = [self.guest_scenario_4.id]
        self.ar_scenario_4_open_ar_2.person_id = [self.guest_scenario_4.id]

        self.guest_scenario_4.save()
        self.ar_scenario_4_open_ar_1.save()
        self.ar_scenario_4_open_ar_2.save()

        # Scenario 5 - 2 closed ARs are linked to guest and guest is linked to one AR
        self.guest_scenario_5 = MvPersonFactory()
        self.ar_scenario_5_closed_ar_1 = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE
        )
        self.ar_scenario_5_closed_ar_2 = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY
        )

        self.guest_scenario_5.accommodation_request_id = (
            self.ar_scenario_5_closed_ar_2.id
        )
        self.ar_scenario_5_closed_ar_1.person_id = [self.guest_scenario_5.id]
        self.ar_scenario_5_closed_ar_2.person_id = [self.guest_scenario_5.id]

        self.guest_scenario_5.save()
        self.ar_scenario_5_closed_ar_1.save()
        self.ar_scenario_5_closed_ar_2.save()

    def assert_no_change_for_correct_guest(self):
        self.guest_correct.refresh_from_db()
        self.ar_correct.refresh_from_db()

        self.assertEqual(
            self.guest_correct.accommodation_request_id, self.ar_correct.id
        )
        self.assertEqual(self.ar_correct.person_id, [self.guest_correct.id])

    def assert_no_change_for_scenario_1(self):
        self.guest_scenario_1.refresh_from_db()
        self.ar_scenario_1_correct_ar.refresh_from_db()
        self.ar_scenario_1_wrong_ar.refresh_from_db()

        self.assertEqual(
            self.guest_scenario_1.accommodation_request_id,
            self.ar_scenario_1_wrong_ar.id,
        )
        self.assertEqual(
            self.ar_scenario_1_correct_ar.person_id, [self.guest_scenario_1.id]
        )
        self.assertIsNone(self.ar_scenario_1_wrong_ar.person_id)

    def assert_changes_for_scenario_1(self):
        self.guest_scenario_1.refresh_from_db()
        self.ar_scenario_1_correct_ar.refresh_from_db()
        self.ar_scenario_1_wrong_ar.refresh_from_db()

        self.assertEqual(
            self.guest_scenario_1.accommodation_request_id,
            self.ar_scenario_1_correct_ar.id,
        )
        self.assertEqual(
            self.ar_scenario_1_correct_ar.person_id, [self.guest_scenario_1.id]
        )
        self.assertIsNone(self.ar_scenario_1_wrong_ar.person_id)

    def assert_no_change_for_scenario_2(self):
        self.guest_scenario_2.refresh_from_db()
        self.ar_scenario_2_open_ar.refresh_from_db()
        self.ar_scenario_2_closed_ar.refresh_from_db()

        self.assertEqual(
            self.guest_scenario_2.accommodation_request_id,
            self.ar_scenario_2_closed_ar.id,
        )
        self.assertEqual(
            self.ar_scenario_2_open_ar.person_id, [self.guest_scenario_2.id]
        )
        self.assertEqual(
            self.ar_scenario_2_closed_ar.person_id, [self.guest_scenario_2.id]
        )

    def assert_changes_for_scenario_2(self):
        self.guest_scenario_2.refresh_from_db()
        self.ar_scenario_2_open_ar.refresh_from_db()
        self.ar_scenario_2_closed_ar.refresh_from_db()

        self.assertEqual(
            self.guest_scenario_2.accommodation_request_id,
            self.ar_scenario_2_open_ar.id,
        )
        self.assertEqual(
            self.ar_scenario_2_open_ar.person_id, [self.guest_scenario_2.id]
        )
        self.assertEqual(
            self.ar_scenario_2_closed_ar.person_id, [self.guest_scenario_2.id]
        )

    def assert_no_change_for_scenario_3(self):
        self.guest_scenario_3.refresh_from_db()
        self.ar_scenario_3_open_ar.refresh_from_db()
        self.ar_scenario_3_closed_ar.refresh_from_db()
        self.ar_scenario_3_other_ar.refresh_from_db()

        self.assertEqual(
            self.guest_scenario_3.accommodation_request_id,
            self.ar_scenario_3_other_ar.id,
        )
        self.assertEqual(
            self.ar_scenario_3_open_ar.person_id, [self.guest_scenario_3.id]
        )
        self.assertEqual(
            self.ar_scenario_3_closed_ar.person_id, [self.guest_scenario_3.id]
        )
        self.assertIsNone(self.ar_scenario_3_other_ar.person_id)

    def assert_changes_for_scenario_3(self):
        self.guest_scenario_3.refresh_from_db()
        self.ar_scenario_3_open_ar.refresh_from_db()
        self.ar_scenario_3_closed_ar.refresh_from_db()
        self.ar_scenario_3_other_ar.refresh_from_db()

        self.assertEqual(
            self.guest_scenario_3.accommodation_request_id,
            self.ar_scenario_3_open_ar.id,
        )
        self.assertEqual(
            self.ar_scenario_3_open_ar.person_id, [self.guest_scenario_3.id]
        )
        self.assertEqual(
            self.ar_scenario_3_closed_ar.person_id, [self.guest_scenario_3.id]
        )
        self.assertIsNone(self.ar_scenario_3_other_ar.person_id)

    def assert_no_change_for_scenario_4(self):
        self.guest_scenario_4.refresh_from_db()
        self.ar_scenario_4_open_ar_1.refresh_from_db()
        self.ar_scenario_4_open_ar_2.refresh_from_db()

        self.assertEqual(
            self.guest_scenario_4.accommodation_request_id,
            self.ar_scenario_4_open_ar_2.id,
        )
        self.assertEqual(
            self.ar_scenario_4_open_ar_1.person_id, [self.guest_scenario_4.id]
        )
        self.assertEqual(
            self.ar_scenario_4_open_ar_2.person_id, [self.guest_scenario_4.id]
        )

    def assert_no_change_for_scenario_5(self):
        self.guest_scenario_5.refresh_from_db()
        self.ar_scenario_5_closed_ar_1.refresh_from_db()
        self.ar_scenario_5_closed_ar_2.refresh_from_db()

        self.assertEqual(
            self.guest_scenario_5.accommodation_request_id,
            self.ar_scenario_5_closed_ar_2.id,
        )
        self.assertEqual(
            self.ar_scenario_5_closed_ar_1.person_id, [self.guest_scenario_5.id]
        )
        self.assertEqual(
            self.ar_scenario_5_closed_ar_2.person_id, [self.guest_scenario_5.id]
        )

    def test_dry_run_function_does_not_change_anything(self, mock_logger):
        run()

        self.assert_no_change_for_correct_guest()
        self.assert_no_change_for_scenario_1()
        self.assert_no_change_for_scenario_2()
        self.assert_no_change_for_scenario_3()
        self.assert_no_change_for_scenario_4()
        self.assert_no_change_for_scenario_5()

        self.assertCountEqual(
            mock_logger.info.call_args_list,
            [
                mock.call(
                    "Start fix_guest_records_pointing_to_wrong_ars with dry_run=%s",
                    True,
                ),
                mock.call(
                    "Processed AR: %s and Guest: %s for scenario %s",
                    self.ar_scenario_1_correct_ar.id,
                    self.guest_scenario_1.id,
                    1,
                ),
                mock.call(
                    "Processed AR: %s and Guest: %s for scenario %s",
                    self.ar_scenario_2_open_ar.id,
                    self.guest_scenario_2.id,
                    2,
                ),
                mock.call(
                    "Processed AR: %s and Guest: %s for scenario %s",
                    self.ar_scenario_3_open_ar.id,
                    self.guest_scenario_3.id,
                    2,
                ),
                mock.call(
                    "Skipping processing AR: %s and Guest: %s for unfixable scenario",
                    self.ar_scenario_4_open_ar_1.id,
                    self.guest_scenario_4.id,
                ),
                mock.call(
                    "End fix_guest_records_pointing_to_wrong_ars with dry_run=%s", True
                ),
                mock.call("Inspected %s records", 4),
                mock.call(
                    "Scenario %s: %s succeeded (%.1f%%), %s failed (%.1f%%)",
                    1,
                    1,
                    100.0,
                    0,
                    0.0,
                ),
                mock.call(
                    "Scenario %s: %s succeeded (%.1f%%), %s failed (%.1f%%)",
                    2,
                    2,
                    100.0,
                    0,
                    0.0,
                ),
                mock.call("Other scenarios: %s skipped", 1),
            ],
        )
        self.assertCountEqual(mock_logger.exception.call_args_list, [])

    def test_runing_function_updates_for_scenario_1_2_and_3(self, mock_logger):
        run(dry_run=False)

        self.assert_no_change_for_correct_guest()
        self.assert_changes_for_scenario_1()
        self.assert_changes_for_scenario_2()
        self.assert_changes_for_scenario_3()
        self.assert_no_change_for_scenario_4()
        self.assert_no_change_for_scenario_5()

        self.assertCountEqual(
            mock_logger.info.call_args_list,
            [
                mock.call(
                    "Start fix_guest_records_pointing_to_wrong_ars with dry_run=%s",
                    False,
                ),
                mock.call(
                    "Processed AR: %s and Guest: %s for scenario %s",
                    self.ar_scenario_1_correct_ar.id,
                    self.guest_scenario_1.id,
                    1,
                ),
                mock.call(
                    "Processed AR: %s and Guest: %s for scenario %s",
                    self.ar_scenario_2_open_ar.id,
                    self.guest_scenario_2.id,
                    2,
                ),
                mock.call(
                    "Processed AR: %s and Guest: %s for scenario %s",
                    self.ar_scenario_3_open_ar.id,
                    self.guest_scenario_3.id,
                    2,
                ),
                mock.call(
                    "Skipping processing AR: %s and Guest: %s for unfixable scenario",
                    self.ar_scenario_4_open_ar_1.id,
                    self.guest_scenario_4.id,
                ),
                mock.call(
                    "End fix_guest_records_pointing_to_wrong_ars with dry_run=%s", False
                ),
                mock.call("Inspected %s records", 4),
                mock.call(
                    "Scenario %s: %s succeeded (%.1f%%), %s failed (%.1f%%)",
                    1,
                    1,
                    100.0,
                    0,
                    0.0,
                ),
                mock.call(
                    "Scenario %s: %s succeeded (%.1f%%), %s failed (%.1f%%)",
                    2,
                    2,
                    100.0,
                    0,
                    0.0,
                ),
                mock.call("Other scenarios: %s skipped", 1),
            ],
        )
        self.assertCountEqual(mock_logger.exception.call_args_list, [])

    @mock.patch.object(MvPerson, "save")
    def test_runing_function_handles_exception(self, mock_save, mock_logger):
        database_error = DatabaseError("Database down")
        mock_save.side_effect = database_error

        run(dry_run=False)

        self.assert_no_change_for_correct_guest()
        self.assert_no_change_for_scenario_1()
        self.assert_no_change_for_scenario_2()
        self.assert_no_change_for_scenario_3()
        self.assert_no_change_for_scenario_4()
        self.assert_no_change_for_scenario_5()

        self.assertCountEqual(
            mock_logger.info.call_args_list,
            [
                mock.call(
                    "Start fix_guest_records_pointing_to_wrong_ars with dry_run=%s",
                    False,
                ),
                mock.call(
                    "Skipping processing AR: %s and Guest: %s for unfixable scenario",
                    self.ar_scenario_4_open_ar_1.id,
                    self.guest_scenario_4.id,
                ),
                mock.call(
                    "End fix_guest_records_pointing_to_wrong_ars with dry_run=%s", False
                ),
                mock.call("Inspected %s records", 4),
                mock.call(
                    "Scenario %s: %s succeeded (%.1f%%), %s failed (%.1f%%)",
                    1,
                    0,
                    0.0,
                    1,
                    100.0,
                ),
                mock.call(
                    "Scenario %s: %s succeeded (%.1f%%), %s failed (%.1f%%)",
                    2,
                    0,
                    0.0,
                    2,
                    100.0,
                ),
                mock.call("Other scenarios: %s skipped", 1),
            ],
        )

        self.assertCountEqual(
            mock_logger.exception.call_args_list,
            [
                mock.call(
                    "Exception processing AR: %s and Guest: %s for scenario %s; "
                    "error: %s",
                    self.ar_scenario_1_correct_ar.id,
                    self.guest_scenario_1.id,
                    1,
                    database_error,
                ),
                mock.call(
                    "Exception processing AR: %s and Guest: %s for scenario %s; "
                    "error: %s",
                    self.ar_scenario_2_open_ar.id,
                    self.guest_scenario_2.id,
                    2,
                    database_error,
                ),
                mock.call(
                    "Exception processing AR: %s and Guest: %s for scenario %s; "
                    "error: %s",
                    self.ar_scenario_3_open_ar.id,
                    self.guest_scenario_3.id,
                    2,
                    database_error,
                ),
            ],
        )
