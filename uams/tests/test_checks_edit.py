import http.client

from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import SponsorshipCertificationForm
from ontology.tests.base import UamsBaseTestCase
from ontology.tests.factories import SponsorshipCertificationFormFactory
from uams.views import UamsChecksEditView
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
    get_user_with_no_access,
)

# Granted access currently hits the placeholder handler, which returns 418.
GRANTED = http.client.IM_A_TEAPOT  # 418

UKVI_SLUGS = [check.value for check in UamsChecksEditView.UKVIChecks]
LA_SLUGS = [check.value for check in UamsChecksEditView.LAChecks]

A_UKVI_SLUG = UamsChecksEditView.UKVIChecks.UK_CONSENT_FORM_STATUS.value
A_LA_SLUG = UamsChecksEditView.LAChecks.SPONSOR_HOUSEHOLD_ENHANCED_DBS_STATUS.value

UKVI_ALL_PASSED = {
    field: "Passed" for field in SponsorshipCertificationForm.UKVI_CHECK_FIELDS
}


class UamChecksEditViewAccessTests(TestSessionTokenMixin, UamsBaseTestCase):
    def setUp(self):
        super().setUp()

        self.ready_uam = SponsorshipCertificationFormFactory(
            reference="SPON-EDIT-READY",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            **UKVI_ALL_PASSED,
        )
        self.ready_uam_da = SponsorshipCertificationFormFactory(
            reference="SPON-EDIT-READY-DA",
            ltla_name=["Aberdeenshire"],
            utla_name=["Aberdeenshire"],
            **UKVI_ALL_PASSED,
        )
        self.not_ready_uam = self.ltla_one_a_uam

    def edit_url(self, uam, slug):
        return reverse("uams:checks-edit", kwargs={"pk": uam.pk, "check": slug})

    def test_user_without_group_access_is_denied(self):
        self.client.force_login(get_user_with_no_access())
        response = self.client.get(self.edit_url(self.ready_uam, A_UKVI_SLUG))

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_user_without_access_to_requested_uam_is_denied(self):
        self.client.force_login(self.ltla_two_a_user)
        response = self.client.get(self.edit_url(self.ready_uam, A_UKVI_SLUG))

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_unknown_check_returns_404(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(self.edit_url(self.ready_uam, "not-a-real-check"))

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_ukvi_user_can_edit_ukvi_check(self):
        self.client.force_login(get_ukvi_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_UKVI_SLUG))

        self.assertEqual(response.status_code, GRANTED)

    def test_dev_user_can_edit_ukvi_check(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_UKVI_SLUG))

        self.assertEqual(response.status_code, GRANTED)

    def test_la_user_cannot_edit_ukvi_check(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.edit_url(self.ready_uam, A_UKVI_SLUG))

        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_mhclg_user_can_edit_ukvi_check(self):
        self.client.force_login(get_mhclg_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_UKVI_SLUG))

        self.assertEqual(response.status_code, GRANTED)

    def test_service_support_user_cannot_edit_ukvi_check(self):
        self.client.force_login(get_service_support_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_UKVI_SLUG))

        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_da_user_cannot_edit_ukvi_check(self):
        self.client.force_login(get_da_user())
        response = self.client.get(self.edit_url(self.ready_uam_da, A_UKVI_SLUG))

        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_la_user_can_edit_la_check_when_status_ready(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.edit_url(self.ready_uam, A_LA_SLUG))

        self.assertEqual(response.status_code, GRANTED)

    def test_la_user_cannot_edit_la_check_when_status_not_ready(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.edit_url(self.not_ready_uam, A_LA_SLUG))

        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_dev_user_can_edit_la_check_when_status_ready(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_LA_SLUG))

        self.assertEqual(response.status_code, GRANTED)

    def test_da_user_can_edit_la_check_when_status_ready(self):
        self.client.force_login(get_da_user())
        response = self.client.get(self.edit_url(self.ready_uam_da, A_LA_SLUG))

        self.assertEqual(response.status_code, GRANTED)

    def test_ukvi_user_cannot_edit_la_check(self):
        self.client.force_login(get_ukvi_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_LA_SLUG))

        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_mhclg_user_can_edit_la_check(self):
        self.client.force_login(get_mhclg_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_LA_SLUG))

        self.assertEqual(response.status_code, GRANTED)

    def test_all_known_checks_are_editable_by_dev_when_ready(self):
        self.client.force_login(get_admin_user())
        for slug in UKVI_SLUGS + LA_SLUGS:
            with self.subTest(slug=slug):
                response = self.client.get(self.edit_url(self.ready_uam, slug))
                self.assertEqual(response.status_code, GRANTED)
