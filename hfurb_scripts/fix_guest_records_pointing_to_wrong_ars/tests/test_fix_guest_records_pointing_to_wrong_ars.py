from unittest import mock

from django.db import DatabaseError
from django.test import TestCase

from accounts.tests.base import TestSessionTokenMixin
from hfurb_scripts.fix_guest_records_pointing_to_wrong_ars import run
from ontology.models import MvAccommodationRequest
from ontology.tests.factories import MvAccommodationRequestFactory, MvPersonFactory


@mock.patch("hfurb_scripts.fix_guest_records_pointing_to_wrong_ars.logger")
class TestFixGuestRecordsPointingToWrongARs(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        # Scenario 0 - Records are linked correctly
        self.guest_correct = MvPersonFactory()
        self.ar_correct = MvAccommodationRequestFactory(
            status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED
        )
        self.guest_correct.accommodation_request_id = self.ar_correct.id
        self.ar_correct.person_id = [self.guest_correct.id]

        self.guest_correct.save()
        self.ar_correct.save()

        # Scenario 1 - AR is linked to the guest and guest is linked to AR
        # which is not linked to the guest
        self.guest_scenario_1 = MvPersonFactory()
        self.ar_scenario_1_correct_ar = MvAccommodationRequestFactory(
            status=MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )
        self.ar_scenario_1_wrong_ar = MvAccommodationRequestFactory(
            status=MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED
        )
        self.guest_scenario_1.accommodation_request_id = self.ar_scenario_1_wrong_ar.id
        self.ar_scenario_1_correct_ar.person_id = [self.guest_scenario_1.id]

        self.guest_scenario_1.save()
        self.ar_scenario_1_correct_ar.save()

        # Scenario 2 - AR is linked to guest and guest is linked to closed AR
        self.guest_scenario_2 = MvPersonFactory()
        self.ar_scenario_2_open_ar = MvAccommodationRequestFactory(
            status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED
        )
        self.ar_scenario_2_closed_ar = MvAccommodationRequestFactory(
            status=MvAccommodationRequest.ChecksStatus.CANCELLED
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
            status=MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )
        self.ar_scenario_3_closed_ar = MvAccommodationRequestFactory(
            status=MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME
        )
        self.ar_scenario_3_other_ar = MvAccommodationRequestFactory(
            status=MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
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
            status=MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED
        )
        self.ar_scenario_4_open_ar_2 = MvAccommodationRequestFactory(
            status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED
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
            status=MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE
        )
        self.ar_scenario_5_closed_ar_2 = MvAccommodationRequestFactory(
            status=MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY
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
        self.assertEqual(self.ar_scenario_2_closed_ar.person_id, [])

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
        self.assertEqual(self.ar_scenario_3_closed_ar.person_id, [])
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

        self.assertEqual(
            mock_logger.info.call_args_list,
            [
                mock.call(
                    "Start fix_guest_records_pointing_to_wrong_ars with dry_run=%s",
                    True,
                ),
                mock.call(
                    "AR: %s meets conditions for scenario 1",
                    self.ar_scenario_1_correct_ar.id,
                ),
                mock.call(
                    "Started processing %s for scenario %s",
                    f"AR: {self.ar_scenario_1_correct_ar.id}; "
                    f"Guest: {self.guest_scenario_1.id};",
                    1,
                ),
                mock.call(
                    "Finished processing %s for scenario %s",
                    f"AR: {self.ar_scenario_1_correct_ar.id}; "
                    f"Guest: {self.guest_scenario_1.id};",
                    1,
                ),
                mock.call(
                    "AR: %s meets conditions for scenario 2",
                    self.ar_scenario_2_open_ar.id,
                ),
                mock.call(
                    "Started processing %s for scenario %s",
                    f"AR: {self.ar_scenario_2_open_ar.id}; "
                    f"Guest: {self.guest_scenario_2.id}; "
                    f"Closed AR: {self.ar_scenario_2_closed_ar.id};",
                    2,
                ),
                mock.call(
                    "Finished processing %s for scenario %s",
                    f"AR: {self.ar_scenario_2_open_ar.id}; "
                    f"Guest: {self.guest_scenario_2.id}; "
                    f"Closed AR: {self.ar_scenario_2_closed_ar.id};",
                    2,
                ),
                mock.call(
                    "AR: %s meets conditions for scenario 2",
                    self.ar_scenario_3_open_ar.id,
                ),
                mock.call(
                    "Started processing %s for scenario %s",
                    f"AR: {self.ar_scenario_3_open_ar.id}; "
                    f"Guest: {self.guest_scenario_3.id}; "
                    f"Closed AR: {self.ar_scenario_3_closed_ar.id};",
                    2,
                ),
                mock.call(
                    "Finished processing %s for scenario %s",
                    f"AR: {self.ar_scenario_3_open_ar.id}; "
                    f"Guest: {self.guest_scenario_3.id}; "
                    f"Closed AR: {self.ar_scenario_3_closed_ar.id};",
                    2,
                ),
                mock.call(
                    "AR: %s does not meet the conditions for a fixable scenario",
                    self.ar_scenario_4_open_ar_1.id,
                ),
                mock.call(
                    "Skipping processing AR: %s; Guest: %s; for unfixable scenario",
                    self.ar_scenario_4_open_ar_1.id,
                    self.guest_scenario_4.id,
                ),
                mock.call(
                    "End fix_guest_records_pointing_to_wrong_ars with dry_run=%s", True
                ),
                mock.call("Scenario 1: %s succeeded, %s failed", 1, 0),
                mock.call("Scenario 2: %s succeeded, %s failed", 2, 0),
                mock.call("Other scenarios: %s skipped", 1),
            ],
        )
        self.assertEqual(mock_logger.exception.call_args_list, [])

    def test_runing_function_updateds_for_scenario_1_2_and_3(self, mock_logger):
        run(dry_run=False)

        self.assert_no_change_for_correct_guest()
        self.assert_changes_for_scenario_1()
        self.assert_changes_for_scenario_2()
        self.assert_changes_for_scenario_3()
        self.assert_no_change_for_scenario_4()
        self.assert_no_change_for_scenario_5()

        self.assertEqual(
            mock_logger.info.call_args_list,
            [
                mock.call(
                    "Start fix_guest_records_pointing_to_wrong_ars with dry_run=%s",
                    False,
                ),
                mock.call(
                    "AR: %s meets conditions for scenario 1",
                    self.ar_scenario_1_correct_ar.id,
                ),
                mock.call(
                    "Started processing %s for scenario %s",
                    f"AR: {self.ar_scenario_1_correct_ar.id}; "
                    f"Guest: {self.guest_scenario_1.id};",
                    1,
                ),
                mock.call(
                    "Finished processing %s for scenario %s",
                    f"AR: {self.ar_scenario_1_correct_ar.id}; "
                    f"Guest: {self.guest_scenario_1.id};",
                    1,
                ),
                mock.call(
                    "AR: %s meets conditions for scenario 2",
                    self.ar_scenario_2_open_ar.id,
                ),
                mock.call(
                    "Started processing %s for scenario %s",
                    f"AR: {self.ar_scenario_2_open_ar.id}; "
                    f"Guest: {self.guest_scenario_2.id}; "
                    f"Closed AR: {self.ar_scenario_2_closed_ar.id};",
                    2,
                ),
                mock.call(
                    "Finished processing %s for scenario %s",
                    f"AR: {self.ar_scenario_2_open_ar.id}; "
                    f"Guest: {self.guest_scenario_2.id}; "
                    f"Closed AR: {self.ar_scenario_2_closed_ar.id};",
                    2,
                ),
                mock.call(
                    "AR: %s meets conditions for scenario 2",
                    self.ar_scenario_3_open_ar.id,
                ),
                mock.call(
                    "Started processing %s for scenario %s",
                    f"AR: {self.ar_scenario_3_open_ar.id}; "
                    f"Guest: {self.guest_scenario_3.id}; "
                    f"Closed AR: {self.ar_scenario_3_closed_ar.id};",
                    2,
                ),
                mock.call(
                    "Finished processing %s for scenario %s",
                    f"AR: {self.ar_scenario_3_open_ar.id}; "
                    f"Guest: {self.guest_scenario_3.id}; "
                    f"Closed AR: {self.ar_scenario_3_closed_ar.id};",
                    2,
                ),
                mock.call(
                    "AR: %s does not meet the conditions for a fixable scenario",
                    self.ar_scenario_4_open_ar_1.id,
                ),
                mock.call(
                    "Skipping processing AR: %s; Guest: %s; for unfixable scenario",
                    self.ar_scenario_4_open_ar_1.id,
                    self.guest_scenario_4.id,
                ),
                mock.call(
                    "End fix_guest_records_pointing_to_wrong_ars with dry_run=%s", False
                ),
                mock.call("Scenario 1: %s succeeded, %s failed", 1, 0),
                mock.call("Scenario 2: %s succeeded, %s failed", 2, 0),
                mock.call("Other scenarios: %s skipped", 1),
            ],
        )
        self.assertEqual(mock_logger.exception.call_args_list, [])

    @mock.patch.object(MvAccommodationRequest, "save")
    def test_runing_function_handles_exception(self, mock_save, mock_logger):
        database_error = DatabaseError("Database down")
        mock_save.side_effect = database_error

        run(dry_run=False)

        self.assert_no_change_for_correct_guest()
        self.assert_changes_for_scenario_1()
        self.assert_no_change_for_scenario_2()
        self.assert_no_change_for_scenario_3()
        self.assert_no_change_for_scenario_4()
        self.assert_no_change_for_scenario_5()

        self.assertEqual(
            mock_logger.info.call_args_list,
            [
                mock.call(
                    "Start fix_guest_records_pointing_to_wrong_ars with dry_run=%s",
                    False,
                ),
                mock.call(
                    "AR: %s meets conditions for scenario 1",
                    self.ar_scenario_1_correct_ar.id,
                ),
                mock.call(
                    "Started processing %s for scenario %s",
                    f"AR: {self.ar_scenario_1_correct_ar.id}; "
                    f"Guest: {self.guest_scenario_1.id};",
                    1,
                ),
                mock.call(
                    "Finished processing %s for scenario %s",
                    f"AR: {self.ar_scenario_1_correct_ar.id}; "
                    f"Guest: {self.guest_scenario_1.id};",
                    1,
                ),
                mock.call(
                    "AR: %s meets conditions for scenario 2",
                    self.ar_scenario_2_open_ar.id,
                ),
                mock.call(
                    "Started processing %s for scenario %s",
                    f"AR: {self.ar_scenario_2_open_ar.id}; "
                    f"Guest: {self.guest_scenario_2.id}; "
                    f"Closed AR: {self.ar_scenario_2_closed_ar.id};",
                    2,
                ),
                mock.call(
                    "AR: %s meets conditions for scenario 2",
                    self.ar_scenario_3_open_ar.id,
                ),
                mock.call(
                    "Started processing %s for scenario %s",
                    f"AR: {self.ar_scenario_3_open_ar.id}; "
                    f"Guest: {self.guest_scenario_3.id}; "
                    f"Closed AR: {self.ar_scenario_3_closed_ar.id};",
                    2,
                ),
                mock.call(
                    "AR: %s does not meet the conditions for a fixable scenario",
                    self.ar_scenario_4_open_ar_1.id,
                ),
                mock.call(
                    "Skipping processing AR: %s; Guest: %s; for unfixable scenario",
                    self.ar_scenario_4_open_ar_1.id,
                    self.guest_scenario_4.id,
                ),
                mock.call(
                    "End fix_guest_records_pointing_to_wrong_ars with dry_run=%s", False
                ),
                mock.call("Scenario 1: %s succeeded, %s failed", 1, 0),
                mock.call("Scenario 2: %s succeeded, %s failed", 0, 2),
                mock.call("Other scenarios: %s skipped", 1),
            ],
        )

        self.assertEqual(
            mock_logger.exception.call_args_list,
            [
                mock.call(
                    "Exception processing %s for scenario %s; error: %s",
                    f"AR: {self.ar_scenario_2_open_ar.id}; "
                    f"Guest: {self.guest_scenario_2.id}; "
                    f"Closed AR: {self.ar_scenario_2_closed_ar.id};",
                    2,
                    database_error,
                ),
                mock.call(
                    "Exception processing %s for scenario %s; error: %s",
                    f"AR: {self.ar_scenario_3_open_ar.id}; "
                    f"Guest: {self.guest_scenario_3.id}; "
                    f"Closed AR: {self.ar_scenario_3_closed_ar.id};",
                    2,
                    database_error,
                ),
            ],
        )
