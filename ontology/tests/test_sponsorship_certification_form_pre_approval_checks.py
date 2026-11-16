from django.test import SimpleTestCase, TestCase

from ontology.models import SponsorshipCertificationForm
from ontology.tests.factories import SponsorshipCertificationFormFactory

CheckStatus = SponsorshipCertificationForm.PreApprovalCheckStatus
Status = SponsorshipCertificationForm.PreApprovalStatus

UKVI_CHECK_FIELDS = SponsorshipCertificationForm.UKVI_CHECK_FIELDS
LA_CHECK_FIELDS = SponsorshipCertificationForm.LA_CHECK_FIELDS
PRE_APPROVAL_CHECK_FIELDS = UKVI_CHECK_FIELDS + LA_CHECK_FIELDS

ALL_UKVI_PASSED = dict.fromkeys(UKVI_CHECK_FIELDS, CheckStatus.PASSED)
ALL_LA_PASSED = dict.fromkeys(LA_CHECK_FIELDS, CheckStatus.PASSED)
ALL_NOT_STARTED = dict.fromkeys(PRE_APPROVAL_CHECK_FIELDS, CheckStatus.NOT_STARTED)


def build_uam(code_emailed=False, **check_statuses):
    return SponsorshipCertificationForm(
        sponsor_certification_code_emailed=code_emailed, **check_statuses
    )


# One set of check-field values per PreApprovalStatus branch, used to assert the
# SQL annotation agrees with the Python method.
PRE_APPROVAL_STATE_CASES = {
    Status.STATUS_NOT_RECORDED: {},
    Status.WAITING_FOR_UKVI_CHECKS: {**ALL_NOT_STARTED},
    Status.UKVI_CHECKS_IN_PROGRESS: {
        **ALL_NOT_STARTED,
        "uk_consent_form_status": CheckStatus.PASSED,
    },
    Status.FAILED_UKVI_CHECKS: {
        **ALL_NOT_STARTED,
        "uk_consent_form_status": CheckStatus.FAILED,
    },
    Status.WAITING_FOR_LA_CHECKS: {**ALL_NOT_STARTED, **ALL_UKVI_PASSED},
    Status.LA_CHECKS_IN_PROGRESS: {
        **ALL_NOT_STARTED,
        **ALL_UKVI_PASSED,
        "accommodation_exists_status": CheckStatus.PASSED,
    },
    Status.FAILED_LA_CHECKS: {
        **ALL_NOT_STARTED,
        **ALL_UKVI_PASSED,
        "accommodation_exists_status": CheckStatus.FAILED,
    },
    Status.PASSED_ALL_CHECKS: {
        **ALL_UKVI_PASSED,
        **ALL_LA_PASSED,
        "sponsor_certification_code_emailed": False,
    },
    Status.COMPLETED: {
        **ALL_UKVI_PASSED,
        **ALL_LA_PASSED,
        "sponsor_certification_code_emailed": True,
    },
}


class SponsorshipCertificationFormPreApprovalCheckDefaultTests(TestCase):
    def test_new_application_has_no_checks_recorded(self):
        SponsorshipCertificationFormFactory(reference="SCF001")

        uam = SponsorshipCertificationForm.objects.get(reference="SCF001")

        for field in PRE_APPROVAL_CHECK_FIELDS:
            with self.subTest(field=field):
                self.assertIsNone(getattr(uam, field))

    def test_new_application_defaults_code_sent_to_sponsor_to_false(self):
        SponsorshipCertificationFormFactory(reference="SCF001")

        uam = SponsorshipCertificationForm.objects.get(reference="SCF001")

        self.assertIs(uam.sponsor_certification_code_emailed, False)


class SponsorshipCertificationFormGetPreApprovalStatusTests(SimpleTestCase):
    def test_status_not_recorded_when_no_checks_recorded(self):
        uam = build_uam()

        self.assertEqual(uam.get_pre_approval_status(), Status.STATUS_NOT_RECORDED)

    def test_waiting_for_ukvi_checks_when_all_checks_not_started(self):
        uam = build_uam(**ALL_NOT_STARTED)

        self.assertEqual(uam.get_pre_approval_status(), Status.WAITING_FOR_UKVI_CHECKS)

    def test_ukvi_checks_in_progress_when_some_ukvi_checks_passed(self):
        uam = build_uam(
            **{
                **ALL_NOT_STARTED,
                "uk_consent_form_status": CheckStatus.PASSED,
            }
        )

        self.assertEqual(uam.get_pre_approval_status(), Status.UKVI_CHECKS_IN_PROGRESS)

    def test_failed_ukvi_checks_when_one_ukvi_check_failed_and_others_not_started(
        self,
    ):
        uam = build_uam(
            **{
                **ALL_NOT_STARTED,
                "uk_consent_form_status": CheckStatus.FAILED,
            }
        )

        self.assertEqual(uam.get_pre_approval_status(), Status.FAILED_UKVI_CHECKS)

    def test_failed_ukvi_checks_when_all_ukvi_checks_recorded_and_one_failed(self):
        uam = build_uam(
            **{
                **ALL_NOT_STARTED,
                **ALL_UKVI_PASSED,
                "sponsor_immigration_eligibility_status": CheckStatus.FAILED,
            }
        )

        self.assertEqual(uam.get_pre_approval_status(), Status.FAILED_UKVI_CHECKS)

    def test_waiting_for_la_checks_when_all_ukvi_checks_passed(self):
        uam = build_uam(**{**ALL_NOT_STARTED, **ALL_UKVI_PASSED})

        self.assertEqual(uam.get_pre_approval_status(), Status.WAITING_FOR_LA_CHECKS)

    def test_la_checks_in_progress_when_some_la_checks_passed(self):
        uam = build_uam(
            **{
                **ALL_NOT_STARTED,
                **ALL_UKVI_PASSED,
                "accommodation_exists_status": CheckStatus.PASSED,
            }
        )

        self.assertEqual(uam.get_pre_approval_status(), Status.LA_CHECKS_IN_PROGRESS)

    def test_failed_la_checks_when_one_la_check_failed_and_others_not_started(self):
        uam = build_uam(
            **{
                **ALL_NOT_STARTED,
                **ALL_UKVI_PASSED,
                "accommodation_exists_status": CheckStatus.FAILED,
            }
        )

        self.assertEqual(uam.get_pre_approval_status(), Status.FAILED_LA_CHECKS)

    def test_failed_la_checks_when_all_la_checks_recorded_and_one_failed(self):
        uam = build_uam(
            **{
                **ALL_UKVI_PASSED,
                **ALL_LA_PASSED,
                "accommodation_suitable_status": CheckStatus.FAILED,
            }
        )

        self.assertEqual(uam.get_pre_approval_status(), Status.FAILED_LA_CHECKS)

    def test_passed_all_checks_when_all_checks_passed_and_code_not_sent(self):
        uam = build_uam(**{**ALL_UKVI_PASSED, **ALL_LA_PASSED})

        self.assertEqual(uam.get_pre_approval_status(), Status.PASSED_ALL_CHECKS)

    def test_completed_when_all_checks_passed_and_code_sent(self):
        uam = build_uam(code_emailed=True, **{**ALL_UKVI_PASSED, **ALL_LA_PASSED})

        self.assertEqual(uam.get_pre_approval_status(), Status.COMPLETED)

    def test_failed_ukvi_checks_takes_priority_over_la_checks(self):
        uam = build_uam(
            **{
                **ALL_UKVI_PASSED,
                **ALL_LA_PASSED,
                "uk_consent_form_status": CheckStatus.FAILED,
            }
        )

        self.assertEqual(uam.get_pre_approval_status(), Status.FAILED_UKVI_CHECKS)


class SponsorshipCertificationFormWithPreApprovalStatusTests(TestCase):
    """
    The SQL annotation ``with_pre_approval_status`` must stay in lockstep with
    the Python ``get_pre_approval_status``.
    """

    def _annotated(self, pk):
        return SponsorshipCertificationForm.objects.with_pre_approval_status().get(
            pk=pk
        )

    def test_annotation_produces_expected_status(self):
        for expected_status, check_kwargs in PRE_APPROVAL_STATE_CASES.items():
            with self.subTest(status=expected_status):
                uam = SponsorshipCertificationFormFactory(**check_kwargs)

                self.assertEqual(
                    self._annotated(uam.pk).pre_approval_status, expected_status
                )

    def test_annotation_matches_python_method(self):
        for expected_status, check_kwargs in PRE_APPROVAL_STATE_CASES.items():
            with self.subTest(status=expected_status):
                uam = SponsorshipCertificationFormFactory(**check_kwargs)
                annotated = self._annotated(uam.pk)

                self.assertEqual(
                    annotated.pre_approval_status,
                    annotated.get_pre_approval_status(),
                )

    def test_annotation_is_idempotent(self):
        SponsorshipCertificationFormFactory(**ALL_NOT_STARTED)

        queryset = (
            SponsorshipCertificationForm.objects.with_pre_approval_status()
            .with_pre_approval_status()
            .filter(pre_approval_status=Status.WAITING_FOR_UKVI_CHECKS)
        )

        self.assertEqual(queryset.count(), 1)
