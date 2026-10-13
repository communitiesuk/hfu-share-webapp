from typing import List
from unittest import mock

from django.db import DatabaseError

from hfurb_scripts.fix_null_array_for_las import run
from hfurb_scripts.tests.base import BaseScriptTestCaseWithSession
from ontology.models import MvAccommodationRequest
from ontology.tests.factories import MvAccommodationRequestFactory


@mock.patch("hfurb_scripts.fix_null_array_for_las.logger")
class TestFixNullArrayForLas(BaseScriptTestCaseWithSession):
    def setUp(self):
        super().setUp()

        self.ars = [
            MvAccommodationRequestFactory(
                ltla_name=["ltla_test"],
                utla_name=["utla_test"],
            ),
            MvAccommodationRequestFactory(
                ltla_name=None,
                utla_name=None,
            ),
            MvAccommodationRequestFactory(
                ltla_name=[],
                utla_name=[],
            ),
            MvAccommodationRequestFactory(
                ltla_name=[None],
                utla_name=[None],
            ),
            MvAccommodationRequestFactory(
                ltla_name=[None],
                utla_name=None,
            ),
            MvAccommodationRequestFactory(
                ltla_name=[],
                utla_name=[None],
            ),
        ]

        for ar in self.ars:
            ar.save()

    def _refresh_ars(self):
        for ar in self.ars:
            ar.refresh_from_db()

    def assert_ltla_and_utla_values(
        self,
        ar: MvAccommodationRequest,
        expected_ltla: List[str],
        expected_utla: List[str],
    ):
        ar.refresh_from_db()
        self.assertEqual(ar.ltla_name, expected_ltla)
        self.assertEqual(ar.utla_name, expected_utla)

    def assert_no_change_for_okay_ars(self):
        self.assert_ltla_and_utla_values(
            self.ars[0],
            ["ltla_test"],
            ["utla_test"],
        )
        self.assert_ltla_and_utla_values(
            self.ars[1],
            None,
            None,
        )
        self.assert_ltla_and_utla_values(
            self.ars[2],
            [],
            [],
        )

    def test_dry_run_function_does_not_change_anything(self, mock_logger):
        run()

        self.assert_no_change_for_okay_ars()
        self.assert_ltla_and_utla_values(
            self.ars[3],
            [None],
            [None],
        )
        self.assert_ltla_and_utla_values(
            self.ars[4],
            [None],
            None,
        )
        self.assert_ltla_and_utla_values(
            self.ars[5],
            [],
            [None],
        )

        self.assertCountEqual(
            mock_logger.info.call_args_list,
            [
                mock.call(
                    "Start fix_null_array_for_las with dry_run=%s",
                    True,
                ),
                mock.call(
                    "Processed AR: %s",
                    self.ars[3].id,
                ),
                mock.call(
                    "Processed AR: %s",
                    self.ars[4].id,
                ),
                mock.call(
                    "Processed AR: %s",
                    self.ars[5].id,
                ),
                mock.call("End fix_null_array_for_las with dry_run=%s", True),
                mock.call(
                    "%s succeeded (%.1f%%), %s failed (%.1f%%)", 3, 100.0, 0, 0.0
                ),
            ],
        )
        self.assertCountEqual(mock_logger.exception.call_args_list, [])

    def test_runing_function_updates_for_ars_3_4_and_5(self, mock_logger):
        run(dry_run=False)

        self.assert_no_change_for_okay_ars()
        self.assert_ltla_and_utla_values(
            self.ars[3],
            [],
            [],
        )
        self.assert_ltla_and_utla_values(
            self.ars[4],
            [],
            None,
        )
        self.assert_ltla_and_utla_values(
            self.ars[5],
            [],
            [],
        )

        self.assertCountEqual(
            mock_logger.info.call_args_list,
            [
                mock.call(
                    "Start fix_null_array_for_las with dry_run=%s",
                    False,
                ),
                mock.call(
                    "Processed AR: %s",
                    self.ars[3].id,
                ),
                mock.call(
                    "Processed AR: %s",
                    self.ars[4].id,
                ),
                mock.call(
                    "Processed AR: %s",
                    self.ars[5].id,
                ),
                mock.call("End fix_null_array_for_las with dry_run=%s", False),
                mock.call(
                    "%s succeeded (%.1f%%), %s failed (%.1f%%)", 3, 100.0, 0, 0.0
                ),
            ],
        )
        self.assertCountEqual(mock_logger.exception.call_args_list, [])

    @mock.patch.object(MvAccommodationRequest, "save")
    def test_runing_function_handles_exception(self, mock_save, mock_logger):
        database_error = DatabaseError("Database down")
        mock_save.side_effect = database_error

        run(dry_run=False)

        self.assert_no_change_for_okay_ars()
        self.assert_ltla_and_utla_values(
            self.ars[3],
            [None],
            [None],
        )
        self.assert_ltla_and_utla_values(
            self.ars[4],
            [None],
            None,
        )
        self.assert_ltla_and_utla_values(
            self.ars[5],
            [],
            [None],
        )

        self.assertCountEqual(
            mock_logger.info.call_args_list,
            [
                mock.call(
                    "Start fix_null_array_for_las with dry_run=%s",
                    False,
                ),
                mock.call("End fix_null_array_for_las with dry_run=%s", False),
                mock.call("%s succeeded (%.1f%%), %s failed (%.1f%%)", 0, 0, 3, 100.0),
            ],
        )
        self.assertCountEqual(
            mock_logger.exception.call_args_list,
            [
                mock.call(
                    "Exception processing AR: %s; error: %s",
                    self.ars[3].id,
                    database_error,
                ),
                mock.call(
                    "Exception processing AR: %s; error: %s",
                    self.ars[4].id,
                    database_error,
                ),
                mock.call(
                    "Exception processing AR: %s; error: %s",
                    self.ars[5].id,
                    database_error,
                ),
            ],
        )
