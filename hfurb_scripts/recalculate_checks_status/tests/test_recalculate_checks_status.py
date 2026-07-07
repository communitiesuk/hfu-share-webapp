from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from hfurb_scripts.recalculate_checks_status import run
from ontology.models import CheckType, DevCheckV2, MvAccommodationRequest
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
)
from ontology.tests.factories import (
    MvAccommodationRequestFactory as ARFactory,
)
from user_management.tests.base import get_admin_user


class TestRecalculateChecksStatus(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        # an AR with one check completed, and requires_checks_status_recalculation=True
        self.accommodation_1 = MvAccommodationFactory()
        self.ar_1 = ARFactory(
            title="AR to be recalculated",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_1.id],
            requires_checks_status_recalculation=True,
        )

        self.accomm_suitable_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            check_status=DevCheckV2.CheckStatus.PASSED,
            AR=[self.ar_1],
        )
        self.accomm_suitable_check.accommodation.set([self.accommodation_1])

        # an AR with one check completed, but requires_checks_status_recalculation=False
        self.accommodation_2 = MvAccommodationFactory()
        self.ar_2 = ARFactory(
            title="AR not to be recalculated",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_2.id],
            requires_checks_status_recalculation=False,
        )

        self.accomm_suitable_check_2 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            check_status=DevCheckV2.CheckStatus.PASSED,
            AR=[self.ar_2],
        )
        self.accomm_suitable_check_2.accommodation.set([self.accommodation_2])

        # adding checks above causes signals to automatically recalulate the AR status
        # so manually reset them here
        self.ar_1.checks_status = MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED
        self.ar_2.checks_status = MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED

        self.ar_1.save()
        self.ar_2.save()

    def test_dry_run_function(self):
        run()

        self.ar_1.refresh_from_db()

        self.assertEqual(
            self.ar_1.checks_status, MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED
        )

    def test_that_ar_with_flag_gets_status_recalculated(self):
        self.assertEqual(
            self.ar_1.checks_status, MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED
        )

        run(dry_run=False)

        self.ar_1.refresh_from_db()

        self.assertEqual(
            self.ar_1.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED,
        )

    def test_that_ar_without_flag_gets_ignored(self):
        self.assertEqual(
            self.ar_2.checks_status, MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED
        )

        run(dry_run=False)

        self.ar_2.refresh_from_db()

        self.assertEqual(
            self.ar_2.checks_status, MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED
        )

    def test_audit_log_displays_correctly(self):
        job_username = "recalculate_checks_status_job"

        run(dry_run=False)

        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar_1.pk],
            )
        )

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, "By System")
        self.assertContains(
            response,
            "Checks status changed: was Checks required now Checks partially completed",
        )
        self.assertContains(
            response,
            f"Last modified by added: now {job_username}.",
        )
        self.assertContains(
            response,
            "Requires checks status recalculation changed: was Yes now No.",
        )

    @patch(
        "ontology.models.MvAccommodationRequest.MvAccommodationRequest.reset_and_redetermine_status"
    )
    def test_exception_handling(self, reset_and_redetermine_status):
        reset_and_redetermine_status.side_effect = Exception("This is a test exception")

        with self.assertLogs(
            "hfurb_scripts.recalculate_checks_status", level="ERROR"
        ) as log_capture:
            # test doesn't raise Exception
            run(dry_run=False)

            self.ar_1.refresh_from_db()

            # test AR isn't updated
            self.assertEqual(
                self.ar_1.checks_status,
                MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            )

            # test ERROR is logged
            self.assertEqual(
                log_capture.records[0].message,
                "Exception calling reset_and_redetermine_status for AR: "
                f"{self.ar_1.id}; "
                "error: This is a test exception",
            )
