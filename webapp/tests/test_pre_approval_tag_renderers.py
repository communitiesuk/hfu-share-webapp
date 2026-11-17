from bs4 import BeautifulSoup

from ontology.models import SponsorshipCertificationForm
from test_utils.base import BaseSimpleTestCase
from webapp.templatetags.tag_renderers import (
    render_app_la_pre_approval_check_code_sent_to_sponsor_tag,
    render_app_la_pre_approval_check_status_tag,
    render_app_ukvi_pre_approval_check_status_tag,
)

PreApprovalStatus = SponsorshipCertificationForm.PreApprovalStatus
CheckStatus = SponsorshipCertificationForm.PreApprovalCheckStatus
CodeSentStatus = SponsorshipCertificationForm.PreApprovalCheckCodeSentStatus

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
            (CheckStatus.IN_PROGRESS, "Checks in progress", "yellow"),
            (CheckStatus.PASSED, "Passed", "green"),
            (CheckStatus.FAILED, "Failed UKVI checks", "red"),
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
            (CheckStatus.IN_PROGRESS, "Checks in progress", "yellow"),
            (CheckStatus.PASSED, "Passed", "green"),
            (CheckStatus.FAILED, "Failed LA checks", "red"),
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
    def test_renders_each_code_sent_status_with_its_colour(self):
        cases = [
            (CodeSentStatus.CANNOT_SEND_CODE, "Cannot send code", "grey"),
            (CodeSentStatus.NO_LONGER_NEEDED, "No longer needed", "grey"),
            (CodeSentStatus.CODE_NOT_SENT, "Code not sent", "blue"),
            (CodeSentStatus.CODE_SENT, "Code sent", "green"),
        ]
        for status, text, colour in cases:
            with self.subTest(status=status):
                html = render_app_la_pre_approval_check_code_sent_to_sponsor_tag(status)
                self.assertTag(html, text=text, colour=colour)
