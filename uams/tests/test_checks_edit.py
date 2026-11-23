import http.client
from unittest.mock import patch

from bs4 import BeautifulSoup
from django.contrib.messages import get_messages
from django.db import DatabaseError
from django.test import override_settings
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import SponsorshipCertificationForm
from ontology.tests.base import UamsBaseTestCase
from ontology.tests.factories import SponsorshipCertificationFormFactory
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
    get_user_with_no_access,
)
from webapp.templatetags.pre_approval_status_extras import (
    pre_approval_check_status_to_title,
)

PreApprovalCheckField = SponsorshipCertificationForm.PreApprovalCheckField


UKVI_SLUGS = [check.value for check in SponsorshipCertificationForm.UKVI_CHECK_FIELDS]
LA_CHECK_SLUGS = [check.value for check in SponsorshipCertificationForm.LA_CHECK_FIELDS]
CODE_EMAILED_SLUG = PreApprovalCheckField.SPONSOR_CERTIFICATION_CODE_EMAILED.value
LA_SLUGS = LA_CHECK_SLUGS + [CODE_EMAILED_SLUG]

A_UKVI_SLUG = PreApprovalCheckField.UK_CONSENT_FORM_STATUS.value
A_LA_SLUG = PreApprovalCheckField.SPONSOR_HOUSEHOLD_ENHANCED_DBS_STATUS.value
SECURITY_SLUG = PreApprovalCheckField.SPONSOR_HOUSEHOLD_SECURITY_CHECKS_STATUS.value
ARRANGEMENTS_SLUG = PreApprovalCheckField.SPONSOR_ARRANGEMENTS_SUITABLE_STATUS.value

NOT_STARTED = "Not started"
IN_PROGRESS = "In progress"
PASSED = "Passed"
FAILED = "Failed"

UKVI_ALL_PASSED = {
    field.value: "Passed" for field in SponsorshipCertificationForm.UKVI_CHECK_FIELDS
}
ALL_CHECKS_PASSED = {
    field.value: "Passed"
    for field in SponsorshipCertificationForm.UKVI_CHECK_FIELDS
    + SponsorshipCertificationForm.LA_CHECK_FIELDS
}

PAGE_CAPTION = "Application to sponsor a child record for"
UKVI_SUB_HEADING = "Update UK Visas and Immigration checks"
LA_SUB_HEADING = "Local authority checks"
CODE_EMAILED_LABEL = "Sponsor certification code emailed to sponsor."
ALL_CHECK_STATUS_LABELS = [
    status.label for status in SponsorshipCertificationForm.PreApprovalCheckStatus
]


def parse(response):
    return BeautifulSoup(response.content.decode("utf-8"), "html.parser")


def _text(element):
    return element.get_text(strip=True) if element else None


def page_caption(soup):
    return _text(soup.select_one("h1.govuk-heading-xl span.govuk-caption-xl"))


def sub_heading(soup):
    return _text(soup.select_one("h2.govuk-heading-l"))


def check_legend(soup):
    return _text(soup.select_one("legend.govuk-fieldset__legend"))


def radio_labels(soup):
    return [
        label.get_text(strip=True) for label in soup.select("label.govuk-radios__label")
    ]


def checkbox_label(soup):
    return _text(soup.select_one("label.govuk-checkboxes__label"))


def error_summary_messages(soup):
    return [
        link.get_text(strip=True)
        for link in soup.select(".govuk-error-summary__list a")
    ]


def field_error_messages(soup):
    messages = []
    for element in soup.select(".govuk-error-message"):
        hidden = element.select_one(".govuk-visually-hidden")
        if hidden:
            hidden.extract()
        messages.append(element.get_text(strip=True))
    return messages


def success_banner_parts(soup):
    """Return the {heading, body, warning} rendered by the success banner."""
    banner = soup.select_one("div.govuk-notification-banner")
    heading = body = None
    if banner:
        heading = _text(banner.select_one(".govuk-notification-banner__heading"))
        body = _text(banner.select_one("p.govuk-body"))

    warning_el = soup.select_one(
        "div.govuk-warning-text strong.govuk-warning-text__text"
    )
    if warning_el:
        hidden = warning_el.select_one(".govuk-visually-hidden")
        if hidden:
            hidden.extract()

    return {"heading": heading, "body": body, "warning": _text(warning_el)}


class UamChecksEditViewBaseTestCase(TestSessionTokenMixin, UamsBaseTestCase):
    def setUp(self):
        super().setUp()

        self.ready_uam = self.make_uam(
            reference="SPON-EDIT-READY",
            **UKVI_ALL_PASSED,
        )
        self.ready_uam_da = SponsorshipCertificationFormFactory(
            reference="SPON-EDIT-READY-DA",
            ltla_name=["Aberdeenshire"],
            utla_name=["Aberdeenshire"],
            **UKVI_ALL_PASSED,
        )
        self.code_ready_uam = self.make_uam(
            reference="SPON-EDIT-CODE-READY",
            **ALL_CHECKS_PASSED,
        )
        self.not_ready_uam = self.ltla_one_a_uam

        self.code_sent_uam = self.make_uam(
            reference="SPON-SUBMIT-CODE-SENT",
            sponsor_certification_code_emailed=True,
            **ALL_CHECKS_PASSED,
        )

    def edit_url(self, uam, slug):
        return reverse("uams:checks-edit", kwargs={"pk": uam.pk, "check": slug})

    def checks_url(self, uam):
        return reverse("uams:detail-checks", kwargs={"pk": uam.pk})

    def submit(self, uam, slug, follow=False, **data):
        return self.client.post(self.edit_url(uam, slug), data=data, follow=follow)

    def make_uam(self, reference, **check_fields):
        return SponsorshipCertificationFormFactory(
            reference=reference,
            certificate_reference=f"CERT-{reference}",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            **check_fields,
        )

    def assertSuccessBanner(self, response, *, heading, body=None, warning=None):
        """Assert the banner parts rendered on the (followed) checks page."""
        parts = success_banner_parts(parse(response))
        self.assertEqual(parts["heading"], heading)
        self.assertEqual(parts["body"], body)
        self.assertEqual(parts["warning"], warning)

    def assertRadioCheckPage(self, response, *, title, sub_heading_text):
        """Assert a status (radio) check edit page renders the expected content."""
        soup = parse(response)
        self.assertEqual(page_caption(soup), PAGE_CAPTION)
        self.assertEqual(sub_heading(soup), sub_heading_text)
        self.assertEqual(check_legend(soup), title)
        self.assertEqual(radio_labels(soup), ALL_CHECK_STATUS_LABELS)

    def assertCheckboxCheckPage(self, response, *, label):
        """Assert the code-emailed (checkbox) check edit page renders correctly."""
        soup = parse(response)
        self.assertEqual(page_caption(soup), PAGE_CAPTION)
        self.assertEqual(sub_heading(soup), LA_SUB_HEADING)
        self.assertEqual(checkbox_label(soup), label)

    def assertErrorShown(self, response, message):
        """Assert a validation error is shown in both the summary and the field."""
        soup = parse(response)
        self.assertIn(message, error_summary_messages(soup))
        self.assertIn(message, field_error_messages(soup))


@override_settings(UAM_CHECKS_ENABLED=True)
class UamChecksEditViewAccessTests(UamChecksEditViewBaseTestCase):
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

        self.assertEqual(response.status_code, http.client.OK)

    def test_dev_user_can_edit_ukvi_check(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_UKVI_SLUG))

        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_cannot_edit_ukvi_check(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.edit_url(self.ready_uam, A_UKVI_SLUG))

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_mhclg_user_can_edit_ukvi_check(self):
        self.client.force_login(get_mhclg_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_UKVI_SLUG))

        self.assertEqual(response.status_code, http.client.OK)

    def test_service_support_user_cannot_edit_ukvi_check(self):
        self.client.force_login(get_service_support_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_UKVI_SLUG))

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_da_user_cannot_edit_ukvi_check(self):
        self.client.force_login(get_da_user())
        response = self.client.get(self.edit_url(self.ready_uam_da, A_UKVI_SLUG))

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_la_user_can_edit_la_check_when_status_ready(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.edit_url(self.ready_uam, A_LA_SLUG))

        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_cannot_edit_la_check_when_status_not_ready(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.edit_url(self.not_ready_uam, A_LA_SLUG))

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_dev_user_can_edit_la_check_when_status_ready(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_LA_SLUG))

        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_can_edit_la_check_when_status_ready(self):
        self.client.force_login(get_da_user())
        response = self.client.get(self.edit_url(self.ready_uam_da, A_LA_SLUG))

        self.assertEqual(response.status_code, http.client.OK)

    def test_ukvi_user_cannot_edit_la_check(self):
        self.client.force_login(get_ukvi_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_LA_SLUG))

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_mhclg_user_can_edit_la_check(self):
        self.client.force_login(get_mhclg_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_LA_SLUG))

        self.assertEqual(response.status_code, http.client.OK)

    def test_all_known_checks_are_editable_by_dev_when_ready(self):
        self.client.force_login(get_admin_user())
        cases = [(slug, self.ready_uam) for slug in UKVI_SLUGS + LA_CHECK_SLUGS]
        cases.append((CODE_EMAILED_SLUG, self.code_ready_uam))
        for slug, uam in cases:
            with self.subTest(slug=slug):
                response = self.client.get(self.edit_url(uam, slug))
                self.assertEqual(response.status_code, http.client.OK)

    def test_code_emailed_blocked_when_code_cannot_be_sent(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(self.edit_url(self.ready_uam, CODE_EMAILED_SLUG))

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_la_user_code_emailed_blocked_when_code_cannot_be_sent(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.edit_url(self.ready_uam, CODE_EMAILED_SLUG))

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_code_emailed_editable_when_all_checks_passed(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(
            self.edit_url(self.code_ready_uam, CODE_EMAILED_SLUG)
        )

        self.assertEqual(response.status_code, http.client.OK)

    @override_settings(UAM_CHECKS_ENABLED=False)
    def test_non_dev_user_denied_when_flag_disabled(self):
        self.client.force_login(get_ukvi_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_UKVI_SLUG))

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    @override_settings(UAM_CHECKS_ENABLED=True)
    def test_non_dev_user_granted_when_flag_enabled(self):
        self.client.force_login(get_ukvi_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_UKVI_SLUG))

        self.assertEqual(response.status_code, http.client.OK)

    @override_settings(UAM_CHECKS_ENABLED=False)
    def test_dev_user_granted_regardless_of_flag(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_UKVI_SLUG))

        self.assertEqual(response.status_code, http.client.OK)


@override_settings(UAM_CHECKS_ENABLED=True)
class UamChecksEditViewSubmitTests(UamChecksEditViewBaseTestCase):
    def test_renders_ukvi_check(self):
        self.client.force_login(get_ukvi_user())
        response = self.client.get(self.edit_url(self.ready_uam, A_UKVI_SLUG))

        self.assertEqual(response.status_code, http.client.OK)
        self.assertRadioCheckPage(
            response,
            title=pre_approval_check_status_to_title(
                PreApprovalCheckField.UK_CONSENT_FORM_STATUS
            ),
            sub_heading_text=UKVI_SUB_HEADING,
        )

    def test_renders_la_check(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.edit_url(self.ready_uam, A_LA_SLUG))

        self.assertEqual(response.status_code, http.client.OK)
        self.assertRadioCheckPage(
            response,
            title=pre_approval_check_status_to_title(
                PreApprovalCheckField.SPONSOR_HOUSEHOLD_ENHANCED_DBS_STATUS
            ),
            sub_heading_text=LA_SUB_HEADING,
        )

    def test_renders_code_emailed_check(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(
            self.edit_url(self.code_ready_uam, CODE_EMAILED_SLUG)
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertCheckboxCheckPage(response, label=CODE_EMAILED_LABEL)

    def test_submit_ukvi_check_redirects_and_updates(self):
        self.client.force_login(get_ukvi_user())
        response = self.submit(
            self.ready_uam,
            A_UKVI_SLUG,
            **{"status": "In progress"},
        )

        self.assertEqual(response.status_code, http.client.FOUND)
        self.assertEqual(response["Location"], self.checks_url(self.ready_uam))

        self.ready_uam.refresh_from_db()
        self.assertEqual(self.ready_uam.uk_consent_form_status, "In progress")

    def test_submit_la_check_redirects_and_updates(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.submit(
            self.ready_uam,
            A_LA_SLUG,
            **{"status": "Passed"},
        )

        self.assertEqual(response.status_code, http.client.FOUND)
        self.assertEqual(response["Location"], self.checks_url(self.ready_uam))

        self.ready_uam.refresh_from_db()
        self.assertEqual(self.ready_uam.sponsor_household_enhanced_dbs_status, "Passed")

    def test_submit_code_emailed_redirects_and_updates(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.submit(
            self.code_ready_uam,
            CODE_EMAILED_SLUG,
            **{"status": "on"},
        )

        self.assertEqual(response.status_code, http.client.FOUND)
        self.assertEqual(response["Location"], self.checks_url(self.code_ready_uam))

        self.code_ready_uam.refresh_from_db()
        self.assertIs(self.code_ready_uam.sponsor_certification_code_emailed, True)

    def test_database_error_shows_error_banner_and_does_not_save(self):
        self.client.force_login(get_ukvi_user())

        with patch.object(
            SponsorshipCertificationForm,
            "update_pre_approval_check_status",
            side_effect=DatabaseError,
        ):
            response = self.submit(
                self.ready_uam,
                A_UKVI_SLUG,
                **{"status": "In progress"},
            )

        self.assertEqual(response.status_code, http.client.FOUND)

        self.ready_uam.refresh_from_db()
        self.assertEqual(self.ready_uam.uk_consent_form_status, "Passed")

        check_title = pre_approval_check_status_to_title(
            PreApprovalCheckField.UK_CONSENT_FORM_STATUS
        )
        banners = list(get_messages(response.wsgi_request))
        self.assertEqual(len(banners), 1)
        self.assertEqual(
            str(banners[0]),
            f"{check_title} update has not been saved. "
            "If the problem continues raise a support ticket.",
        )

    def test_code_emailed_unchecked_when_not_sent_is_rejected(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.submit(
            self.code_ready_uam,
            CODE_EMAILED_SLUG,
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertErrorShown(
            response,
            "Select the check box to confirm you have emailed the sponsor.",
        )

        self.code_ready_uam.refresh_from_db()
        self.assertIs(self.code_ready_uam.sponsor_certification_code_emailed, False)

    def test_code_emailed_can_transition_true_to_false(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.submit(self.code_sent_uam, CODE_EMAILED_SLUG)

        self.assertEqual(response.status_code, http.client.FOUND)
        self.assertEqual(response["Location"], self.checks_url(self.code_sent_uam))

        self.code_sent_uam.refresh_from_db()
        self.assertIs(self.code_sent_uam.sponsor_certification_code_emailed, False)


@override_settings(UAM_CHECKS_ENABLED=True)
class UamChecksEditViewSuccessBannerTests(UamChecksEditViewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(get_admin_user())

    def submit(self, uam, slug, **data):
        return super().submit(uam, slug, follow=True, **data)

    def test_banner_ukvi_within_phase(self):
        uam = self.make_uam(
            "SPON-BANNER-U1",
            uk_consent_form_status=NOT_STARTED,
            ukraine_consent_form_status=NOT_STARTED,
            sponsor_immigration_eligibility_status=NOT_STARTED,
            sponsor_household_security_checks_status=NOT_STARTED,
        )

        for status in [
            IN_PROGRESS,
            PASSED,
            NOT_STARTED,
        ]:
            with self.subTest(status=status):
                response = self.submit(uam, A_UKVI_SLUG, **{"status": status})

                self.assertEqual(response.status_code, http.client.OK)
                self.assertSuccessBanner(
                    response,
                    heading=f"UK consent form: {status.lower()}",
                    body=None,
                    warning=None,
                )

    def test_banner_ukvi_all_passed(self):
        uam = self.make_uam(
            "SPON-BANNER-U2",
            uk_consent_form_status=PASSED,
            ukraine_consent_form_status=PASSED,
            sponsor_immigration_eligibility_status=PASSED,
            sponsor_household_security_checks_status=IN_PROGRESS,
        )
        response = self.submit(uam, SECURITY_SLUG, **{"status": PASSED})

        self.assertEqual(response.status_code, http.client.OK)
        self.assertSuccessBanner(
            response,
            heading="Sponsor and household security checks: passed",
            body=(
                "Sponsor passed all UK Visas and Immigration checks. "
                "test_ltla_one_a will now complete their checks."
            ),
            warning=None,
        )

    def test_banner_ukvi_failed(self):
        uam = self.make_uam(
            "SPON-BANNER-U3",
            uk_consent_form_status=IN_PROGRESS,
            ukraine_consent_form_status=IN_PROGRESS,
            sponsor_immigration_eligibility_status=IN_PROGRESS,
            sponsor_household_security_checks_status=IN_PROGRESS,
        )
        response = self.submit(uam, A_UKVI_SLUG, **{"status": FAILED})

        self.assertEqual(response.status_code, http.client.OK)
        self.assertSuccessBanner(
            response,
            heading="UK consent form: failed",
            body=(
                "Sponsor failed UK Visas and Immigration checks. "
                "The Ministry of Housing, Communities and Local Government (MHCLG) "
                "will contact the sponsor with this decision."
            ),
            warning=None,
        )

    def test_banner_ukvi_reverted_from_passed(self):
        for status in [
            IN_PROGRESS,
            NOT_STARTED,
        ]:
            with self.subTest(status=status):
                uam = self.make_uam(f"SPON-BANNER-U4-{status}", **UKVI_ALL_PASSED)

                response = self.submit(uam, A_UKVI_SLUG, **{"status": status})

                self.assertEqual(response.status_code, http.client.OK)
                self.assertSuccessBanner(
                    response,
                    heading=f"UK consent form: {status.lower()}",
                    body=None,
                    warning=(
                        "You changed UK consent form from passed to "
                        f"{status.lower()}. Raise a support ticket to "
                        "stop any follow-on actions."
                    ),
                )

    def test_banner_ukvi_reverted_from_passed_to_failed(self):
        uam = self.make_uam("SPON-BANNER-U5", **UKVI_ALL_PASSED)

        response = self.submit(uam, A_UKVI_SLUG, **{"status": FAILED})

        self.assertEqual(response.status_code, http.client.OK)
        self.assertSuccessBanner(
            response,
            heading="UK consent form: failed",
            body=(
                "Sponsor failed UK Visas and Immigration checks. "
                "The Ministry of Housing, Communities and Local Government (MHCLG) "
                "will contact the sponsor with this decision."
            ),
            warning=(
                "You changed UK consent form from passed to failed. "
                "Raise a support ticket to stop any follow-on actions."
            ),
        )

    def test_banner_ukvi_reverted_from_failed(self):
        for status in [
            IN_PROGRESS,
            NOT_STARTED,
        ]:
            with self.subTest(status=status):
                uam = self.make_uam(
                    f"SPON-BANNER-U6-{status}",
                    uk_consent_form_status=FAILED,
                    ukraine_consent_form_status=PASSED,
                    sponsor_immigration_eligibility_status=PASSED,
                    sponsor_household_security_checks_status=PASSED,
                )

                response = self.submit(uam, A_UKVI_SLUG, **{"status": status})

                self.assertEqual(response.status_code, http.client.OK)
                self.assertSuccessBanner(
                    response,
                    heading=f"UK consent form: {status.lower()}",
                    body=None,
                    warning=(
                        "You changed UK consent form from failed to "
                        f"{status.lower()}. Raise a support ticket to "
                        "stop any follow-on actions."
                    ),
                )

    def test_banner_ukvi_reverted_from_failed_to_pass(self):
        uam = self.make_uam(
            "SPON-BANNER-U6",
            uk_consent_form_status=FAILED,
            ukraine_consent_form_status=PASSED,
            sponsor_immigration_eligibility_status=PASSED,
            sponsor_household_security_checks_status=PASSED,
        )

        response = self.submit(uam, A_UKVI_SLUG, **{"status": PASSED})

        self.assertEqual(response.status_code, http.client.OK)
        self.assertSuccessBanner(
            response,
            heading="UK consent form: passed",
            body=(
                "Sponsor passed all UK Visas and Immigration checks. "
                "test_ltla_one_a will now complete their checks."
            ),
            warning=(
                "You changed UK consent form from failed to passed. "
                "Raise a support ticket to stop any follow-on actions."
            ),
        )

    def test_banner_la_within_phase(self):
        uam = self.make_uam(
            "SPON-BANNER-L1",
            **UKVI_ALL_PASSED,
            sponsor_household_enhanced_dbs_status=NOT_STARTED,
        )
        for status in [
            IN_PROGRESS,
            PASSED,
            NOT_STARTED,
        ]:
            with self.subTest(status=status):
                response = self.submit(uam, A_LA_SLUG, **{"status": status})

                self.assertEqual(response.status_code, http.client.OK)
                self.assertSuccessBanner(
                    response,
                    heading=(
                        f"Sponsor and household members enhanced DBS: {status.lower()}"
                    ),
                    body=None,
                    warning=None,
                )

    def test_banner_la_passed_all_checks(self):
        uam = self.make_uam(
            "SPON-BANNER-L2",
            **UKVI_ALL_PASSED,
            sponsor_household_enhanced_dbs_status=PASSED,
            accommodation_exists_status=PASSED,
            accommodation_suitable_status=PASSED,
            sponsor_role_and_expectations_status=PASSED,
            sponsor_arrangements_suitable_status=IN_PROGRESS,
        )
        response = self.submit(uam, ARRANGEMENTS_SLUG, **{"status": PASSED})

        self.assertEqual(response.status_code, http.client.OK)
        self.assertSuccessBanner(
            response,
            heading="Sponsor arrangements suitable: passed",
            body="Sponsor passed all suitability checks.",
            warning=(
                "Send the Sponsor Certification code CERT-SPON-BANNER-L2 "
                "to the sponsor."
            ),
        )

    def test_banner_la_failed(self):
        uam = self.make_uam(
            "SPON-BANNER-L3",
            **UKVI_ALL_PASSED,
            sponsor_household_enhanced_dbs_status=IN_PROGRESS,
        )
        response = self.submit(uam, A_LA_SLUG, **{"status": FAILED})

        self.assertEqual(response.status_code, http.client.OK)
        self.assertSuccessBanner(
            response,
            heading="Sponsor and household members enhanced DBS: failed",
            body=(
                "Sponsor failed local authority checks. "
                "The Ministry of Housing, Communities and Local Government (MHCLG) "
                "will contact the sponsor with this decision."
            ),
            warning=None,
        )

    def test_banner_la_completed(self):
        uam = self.make_uam("SPON-BANNER-L4", **ALL_CHECKS_PASSED)
        response = self.submit(uam, CODE_EMAILED_SLUG, **{"status": "on"})

        self.assertEqual(response.status_code, http.client.OK)
        self.assertSuccessBanner(
            response,
            heading="All checks passed and Sponsor Certification code sent to sponsor.",
            body=None,
            warning=None,
        )

    def test_banner_la_reverted_from_complete_to_all_passed(self):
        uam = self.make_uam(
            "SPON-BANNER-L6",
            **ALL_CHECKS_PASSED,
            sponsor_certification_code_emailed=True,
        )
        response = self.submit(uam, CODE_EMAILED_SLUG)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertSuccessBanner(
            response,
            heading="Sponsor certification code marked as not sent",
            body=None,
            warning=(
                "Checks status changed from Completed to Passed all checks. "
                "If the Sponsor Certification code has already been sent, contact "
                "the Ministry of Housing, Communities and Local Government (MHCLG)"
            ),
        )

    def test_banner_la_reverted_from_complete_to_failed(self):
        uam = self.make_uam(
            "SPON-BANNER-L7",
            **ALL_CHECKS_PASSED,
            sponsor_certification_code_emailed=True,
        )
        response = self.submit(uam, A_LA_SLUG, **{"status": FAILED})

        self.assertEqual(response.status_code, http.client.OK)
        self.assertSuccessBanner(
            response,
            heading="Sponsor and household members enhanced DBS: failed",
            body=(
                "Sponsor failed local authority checks. "
                "The Ministry of Housing, Communities and Local Government (MHCLG) "
                "will contact the sponsor with this decision."
            ),
            warning=(
                "Checks status changed from Completed to Failed LA checks. "
                "If the Sponsor Certification code has already been sent, contact "
                "the Ministry of Housing, Communities and Local Government (MHCLG)"
            ),
        )

    def test_banner_la_reverted_from_complete_to_in_progress(self):
        for status in [
            IN_PROGRESS,
            NOT_STARTED,
        ]:
            with self.subTest(status=status):
                uam = self.make_uam(
                    f"SPON-BANNER-L8-{status}",
                    **ALL_CHECKS_PASSED,
                    sponsor_certification_code_emailed=True,
                )

                response = self.submit(uam, A_LA_SLUG, **{"status": status})

                self.assertEqual(response.status_code, http.client.OK)
                self.assertSuccessBanner(
                    response,
                    heading=(
                        f"Sponsor and household members enhanced DBS: {status.lower()}"
                    ),
                    body=None,
                    warning=(
                        "Checks status changed from Completed to LA checks "
                        "in progress. If the Sponsor Certification code has already "
                        "been sent, contact the Ministry of Housing, Communities and "
                        "Local Government (MHCLG)"
                    ),
                )

    def test_banner_la_reverted_from_all_passed_to_failed(self):
        uam = self.make_uam(
            "SPON-BANNER-L9",
            **ALL_CHECKS_PASSED,
        )
        response = self.submit(uam, A_LA_SLUG, **{"status": FAILED})

        self.assertEqual(response.status_code, http.client.OK)
        self.assertSuccessBanner(
            response,
            heading="Sponsor and household members enhanced DBS: failed",
            body=(
                "Sponsor failed local authority checks. "
                "The Ministry of Housing, Communities and Local Government (MHCLG) "
                "will contact the sponsor with this decision."
            ),
            warning=(
                "You changed Sponsor and household members enhanced DBS from "
                "passed to failed. "
                "Raise a support ticket to stop any follow-on actions."
            ),
        )

    def test_banner_la_reverted_from_all_passed_to_in_progress(self):
        for status in [
            IN_PROGRESS,
            NOT_STARTED,
        ]:
            with self.subTest(status=status):
                uam = self.make_uam(
                    f"SPON-BANNER-L10-{status}",
                    **ALL_CHECKS_PASSED,
                )

                response = self.submit(uam, A_LA_SLUG, **{"status": status})

                self.assertEqual(response.status_code, http.client.OK)
                self.assertSuccessBanner(
                    response,
                    heading=(
                        f"Sponsor and household members enhanced DBS: {status.lower()}"
                    ),
                    body=None,
                    warning=(
                        "You changed Sponsor and household members enhanced DBS from "
                        f"passed to {status.lower()}. "
                        "Raise a support ticket to stop any follow-on actions."
                    ),
                )

    def test_banner_la_reverted_from_failed_to_all_passed(self):
        uam = self.make_uam(
            "SPON-BANNER-L11",
            **UKVI_ALL_PASSED,
            sponsor_household_enhanced_dbs_status=FAILED,
            accommodation_exists_status=PASSED,
            accommodation_suitable_status=PASSED,
            sponsor_role_and_expectations_status=PASSED,
            sponsor_arrangements_suitable_status=PASSED,
        )
        response = self.submit(uam, A_LA_SLUG, **{"status": PASSED})

        self.assertEqual(response.status_code, http.client.OK)
        self.assertSuccessBanner(
            response,
            heading="Sponsor and household members enhanced DBS: passed",
            body="Sponsor passed all suitability checks.",
            warning=(
                "You changed Sponsor and household members enhanced DBS from failed "
                "to passed. Raise a support ticket to stop any follow-on actions."
            ),
        )

    def test_banner_la_reverted_from_failed_to_complete(self):
        uam = self.make_uam(
            "SPON-BANNER-L12",
            **UKVI_ALL_PASSED,
            sponsor_household_enhanced_dbs_status=FAILED,
            accommodation_exists_status=PASSED,
            accommodation_suitable_status=PASSED,
            sponsor_role_and_expectations_status=PASSED,
            sponsor_arrangements_suitable_status=PASSED,
            sponsor_certification_code_emailed=True,
        )
        response = self.submit(uam, A_LA_SLUG, **{"status": PASSED})

        self.assertEqual(response.status_code, http.client.OK)
        self.assertSuccessBanner(
            response,
            heading="All checks passed and Sponsor Certification code sent to sponsor.",
            body=None,
            warning=(
                "You changed Sponsor and household members enhanced DBS from failed "
                "to passed. Raise a support ticket to stop any follow-on actions."
            ),
        )

    def test_banner_la_reverted_from_failed_to_in_progress(self):
        for status in [
            IN_PROGRESS,
            NOT_STARTED,
        ]:
            with self.subTest(status=status):
                uam = self.make_uam(
                    f"SPON-BANNER-L3-{status}",
                    **UKVI_ALL_PASSED,
                    sponsor_household_enhanced_dbs_status=FAILED,
                    accommodation_exists_status=PASSED,
                    accommodation_suitable_status=PASSED,
                    sponsor_role_and_expectations_status=PASSED,
                    sponsor_arrangements_suitable_status=PASSED,
                )

                response = self.submit(uam, A_LA_SLUG, **{"status": status})

                self.assertEqual(response.status_code, http.client.OK)
                self.assertSuccessBanner(
                    response,
                    heading=(
                        f"Sponsor and household members enhanced DBS: {status.lower()}"
                    ),
                    body=None,
                    warning=(
                        "You changed Sponsor and household members enhanced DBS "
                        f"from failed to {status.lower()}. Raise a support ticket to "
                        "stop any follow-on actions."
                    ),
                )
