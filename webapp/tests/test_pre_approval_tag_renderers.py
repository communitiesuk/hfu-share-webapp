from bs4 import BeautifulSoup

from ontology.models import SponsorshipCertificationForm
from test_utils.base import BaseSimpleTestCase
from webapp.templatetags.tag_renderers import (
    render_app_la_pre_approval_check_status_tag,
    render_app_la_pre_approval_code_sent_to_sponsor_tag,
    render_app_ukvi_pre_approval_check_status_tag,
)

PreApprovalStatus = SponsorshipCertificationForm.PreApprovalStatus
CheckStatus = SponsorshipCertificationForm.PreApprovalCheckStatus

LA_READY_STATUSES = [
    PreApprovalStatus.WAITING_FOR_LA_CHECKS,
    PreApprovalStatus.LA_CHECKS_IN_PROGRESS,
    PreApprovalStatus.FAILED_LA_CHECKS,
    PreApprovalStatus.PASSED_ALL_CHECKS,
    PreApprovalStatus.COMPLETED,
]
LA_NOT_READY_STATUSES = [
    PreApprovalStatus.WAITING_FOR_UKVI_CHECKS,
    PreApprovalStatus.UKVI_CHECKS_IN_PROGRESS,
    PreApprovalStatus.STATUS_NOT_RECORDED,
]


def parse_tag(html):
    strong = BeautifulSoup(html, "html.parser").find("strong")
    return strong.get_text(strip=True), set(strong.get("class") or [])


class PreApprovalTagRendererTestMixin:
    def assertTag(self, html, *, text, colour):
        actual_text, classes = parse_tag(html)
        self.assertEqual(actual_text, text)
        self.assertEqual(
            classes,
            {"govuk-tag", f"govuk-tag--{colour}", "app-tag--nowrap"},
        )


class RenderUkviPreApprovalCheckStatusTagTests(
    PreApprovalTagRendererTestMixin, BaseSimpleTestCase
):
    def test_renders_each_check_status_with_its_colour(self):
        cases = [
            (None, "Not started", "blue"),
            (CheckStatus.NOT_STARTED, "Not started", "blue"),
            (CheckStatus.IN_PROGRESS, "In progress", "yellow"),
            (CheckStatus.PASSED, "Passed", "green"),
            (CheckStatus.FAILED, "Failed", "red"),
        ]
        for status, text, colour in cases:
            with self.subTest(status=status):
                html = render_app_ukvi_pre_approval_check_status_tag(status)
                self.assertTag(html, text=text, colour=colour)


class RenderLaPreApprovalCheckStatusTagTests(
    PreApprovalTagRendererTestMixin, BaseSimpleTestCase
):
    def test_shows_real_check_status_when_la_checks_are_live(self):
        for pre_approval_status in LA_READY_STATUSES:
            with self.subTest(pre_approval_status=pre_approval_status):
                html = render_app_la_pre_approval_check_status_tag(
                    pre_approval_status, CheckStatus.NOT_STARTED
                )
                self.assertTag(html, text="Not started", colour="blue")

    def test_passes_through_each_check_status_colour_when_live(self):
        cases = [
            (None, "Not started", "blue"),
            (CheckStatus.NOT_STARTED, "Not started", "blue"),
            (CheckStatus.IN_PROGRESS, "In progress", "yellow"),
            (CheckStatus.PASSED, "Passed", "green"),
            (CheckStatus.FAILED, "Failed", "red"),
        ]
        for status, text, colour in cases:
            with self.subTest(status=status):
                html = render_app_la_pre_approval_check_status_tag(
                    PreApprovalStatus.WAITING_FOR_LA_CHECKS, status
                )
                self.assertTag(html, text=text, colour=colour)

    def test_shows_no_longer_needed_when_ukvi_checks_failed(self):
        html = render_app_la_pre_approval_check_status_tag(
            PreApprovalStatus.FAILED_UKVI_CHECKS, CheckStatus.PASSED
        )
        self.assertTag(html, text="No longer needed", colour="grey")

    def test_shows_cannot_start_checks_for_other_statuses(self):
        for pre_approval_status in LA_NOT_READY_STATUSES:
            with self.subTest(pre_approval_status=pre_approval_status):
                html = render_app_la_pre_approval_check_status_tag(
                    pre_approval_status, CheckStatus.PASSED
                )
                self.assertTag(html, text="Cannot start checks", colour="grey")


class RenderLaCodeSentToSponsorTagTests(
    PreApprovalTagRendererTestMixin, BaseSimpleTestCase
):
    def test_shows_code_sent_when_all_checks_passed_and_code_sent(self):
        for pre_approval_status in [
            PreApprovalStatus.PASSED_ALL_CHECKS,
            PreApprovalStatus.COMPLETED,
        ]:
            with self.subTest(pre_approval_status=pre_approval_status):
                html = render_app_la_pre_approval_code_sent_to_sponsor_tag(
                    pre_approval_status, True
                )
                self.assertTag(html, text="Code sent", colour="green")

    def test_shows_code_not_sent_when_all_checks_passed_but_code_not_sent(self):
        for pre_approval_status in [
            PreApprovalStatus.PASSED_ALL_CHECKS,
            PreApprovalStatus.COMPLETED,
        ]:
            with self.subTest(pre_approval_status=pre_approval_status):
                html = render_app_la_pre_approval_code_sent_to_sponsor_tag(
                    pre_approval_status, False
                )
                self.assertTag(html, text="Code not sent", colour="blue")

    def test_shows_no_longer_needed_when_ukvi_checks_failed(self):
        for code_sent in [True, False]:
            with self.subTest(code_sent=code_sent):
                html = render_app_la_pre_approval_code_sent_to_sponsor_tag(
                    PreApprovalStatus.FAILED_UKVI_CHECKS, code_sent
                )
                self.assertTag(html, text="No longer needed", colour="grey")

    def test_shows_cannot_send_code_for_other_statuses(self):
        other_statuses = [
            PreApprovalStatus.WAITING_FOR_UKVI_CHECKS,
            PreApprovalStatus.UKVI_CHECKS_IN_PROGRESS,
            PreApprovalStatus.WAITING_FOR_LA_CHECKS,
            PreApprovalStatus.LA_CHECKS_IN_PROGRESS,
            PreApprovalStatus.FAILED_LA_CHECKS,
            PreApprovalStatus.STATUS_NOT_RECORDED,
        ]
        for pre_approval_status in other_statuses:
            with self.subTest(pre_approval_status=pre_approval_status):
                html = render_app_la_pre_approval_code_sent_to_sponsor_tag(
                    pre_approval_status, False
                )
                self.assertTag(html, text="Cannot send code", colour="grey")
