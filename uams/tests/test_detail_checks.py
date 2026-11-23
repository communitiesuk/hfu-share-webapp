import http.client

from bs4 import BeautifulSoup
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
)

PreApprovalCheckField = SponsorshipCertificationForm.PreApprovalCheckField


UKVI_CARD_HEADING = "UK Visas and Immigration checks"
LA_CARD_HEADING = "Local authority checks"

UKVI_CHECK_TITLES = [
    "UK consent form",
    "Ukraine consent form",
    "Sponsor immigration eligibility",
    "Sponsor and household security checks",
]
LA_CHECK_TITLES = [
    "Sponsor and household members enhanced DBS",
    "Accommodation exists",
    "Accommodation suitable",
    "Sponsor role and expectations",
    "Sponsor arrangements suitable",
    "Code sent to sponsor",
]

LA_CANNOT_EDIT_UKVI_MESSAGE = "Local authorities cannot edit these records."
LA_CHECKS_AVAILABLE_MESSAGE = "Local authority checks are now available."
LA_CHECKS_PENDING_UKVI_MESSAGE = (
    "Local authorities can record their checks once the sponsor has passed "
    "all UKVI checks."
)
LA_CHECKS_AVAILABLE_UKVI_MESSAGE = "Local authorities can now record their checks."
LA_CHECKS_BLOCKED_MESSAGE = (
    "You cannot start local authority checks until all UKVI checks have been passed."
)

UKVI_CHECK_SLUGS = [
    check.value for check in SponsorshipCertificationForm.UKVI_CHECK_FIELDS
]
LA_CHECK_SLUGS = [
    check.value for check in SponsorshipCertificationForm.LA_CHECK_FIELDS
] + [
    PreApprovalCheckField.SPONSOR_CERTIFICATION_CODE_EMAILED.value,
]


def check_statuses(ukvi="Passed", la="Passed"):
    return {
        **{
            field.value: ukvi
            for field in SponsorshipCertificationForm.UKVI_CHECK_FIELDS
        },
        **{field.value: la for field in SponsorshipCertificationForm.LA_CHECK_FIELDS},
    }


def edit_url(uam, slug):
    return reverse("uams:checks-edit", kwargs={"pk": uam.pk, "check": slug})


def parse(response):
    return BeautifulSoup(response.content.decode("utf-8"), "html.parser")


def card_by_heading(soup, heading):
    for title in soup.select("h2.govuk-summary-card__title"):
        if title.get_text(strip=True) == heading:
            return title.find_parent("div", class_="govuk-summary-card")
    return None


def parse_rows(card):
    rows = []
    for item in card.select("li.govuk-task-list__item"):
        link = item.select_one("a.govuk-task-list__link")
        if link is not None:
            title = link.get_text(strip=True)
            href = link.get("href")
        else:
            title = item.select_one("div.govuk-task-list__name-and-hint").get_text(
                strip=True
            )
            href = None
        tag = item.select_one("div.govuk-task-list__status strong.govuk-tag")
        status = tag.get_text(strip=True) if tag else None
        rows.append((title, href, status))
    return rows


def active_tab_text(soup):
    link = soup.select_one(".moj-side-navigation a[aria-current='location']")
    return link.get_text(strip=True) if link else None


def tab_texts(soup):
    return [a.get_text(strip=True) for a in soup.select(".moj-side-navigation a")]


@override_settings(UAM_CHECKS_ENABLED=True)
class UamChecksViewTests(TestSessionTokenMixin, UamsBaseTestCase):
    def setUp(self):
        super().setUp()

        # A fully-recorded application the LA-one-a user (and others) can load.
        self.checks_uam = SponsorshipCertificationFormFactory(
            reference="SPON-CHECKS-1",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            **check_statuses(),
        )
        # Same, in the Scotland DA scope, for the DA access test.
        self.checks_uam_da = SponsorshipCertificationFormFactory(
            reference="SPON-CHECKS-DA",
            ltla_name=["Aberdeenshire"],
            utla_name=["Aberdeenshire"],
            **check_statuses(),
        )

    def checks_url(self, uam):
        return reverse("uams:detail-checks", kwargs={"pk": uam.pk})

    def assertTitlesInOrder(self, rows, expected_titles):
        self.assertEqual([title for title, _, _ in rows], expected_titles)

    def test_user_without_access_to_requested_uam_is_denied_access(self):
        self.client.force_login(self.ltla_two_a_user)
        response = self.client.get(self.checks_url(self.checks_uam))

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_dev_user_is_granted_access(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(self.checks_url(self.checks_uam))

        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_granted_access(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.checks_url(self.checks_uam))

        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_granted_access(self):
        self.client.force_login(get_da_user())
        response = self.client.get(self.checks_url(self.checks_uam_da))

        self.assertEqual(response.status_code, http.client.OK)

    def test_mhclg_user_is_granted_access(self):
        self.client.force_login(get_mhclg_user())
        response = self.client.get(self.checks_url(self.checks_uam))

        self.assertEqual(response.status_code, http.client.OK)

    def test_ukvi_user_is_granted_access(self):
        self.client.force_login(get_ukvi_user())
        response = self.client.get(self.checks_url(self.checks_uam))

        self.assertEqual(response.status_code, http.client.OK)

    def test_service_support_user_is_granted_access(self):
        self.client.force_login(get_service_support_user())
        response = self.client.get(self.checks_url(self.checks_uam))

        self.assertEqual(response.status_code, http.client.OK)

    def test_ukvi_user_can_edit_ukvi_checks(self):
        self.client.force_login(get_ukvi_user())
        response = self.client.get(self.checks_url(self.checks_uam))
        soup = parse(response)

        ukvi_rows = parse_rows(card_by_heading(soup, UKVI_CARD_HEADING))

        self.assertTitlesInOrder(ukvi_rows, UKVI_CHECK_TITLES)

        for (_, href, _), slug in zip(ukvi_rows, UKVI_CHECK_SLUGS, strict=True):
            self.assertEqual(href, edit_url(self.checks_uam, slug))

        self.assertNotIn(LA_CANNOT_EDIT_UKVI_MESSAGE, soup.get_text())

    def test_ukvi_user_cannot_edit_la_checks(self):
        self.client.force_login(get_ukvi_user())
        response = self.client.get(self.checks_url(self.checks_uam))
        soup = parse(response)

        la_rows = parse_rows(card_by_heading(soup, LA_CARD_HEADING))

        self.assertTitlesInOrder(la_rows, LA_CHECK_TITLES)

        self.assertTrue(all(href is None for _, href, _ in la_rows))

        page_text = soup.get_text()
        self.assertIn(LA_CHECKS_AVAILABLE_UKVI_MESSAGE, page_text)
        self.assertNotIn(LA_CHECKS_AVAILABLE_MESSAGE, page_text)

    def test_la_user_can_edit_la_checks_when_status_ready_except_code_sent(self):
        uam = SponsorshipCertificationFormFactory(
            reference="SPON-LA-READY",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            **check_statuses(ukvi="Passed", la="Not started"),
        )

        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.checks_url(uam))
        soup = parse(response)

        ukvi_rows = parse_rows(card_by_heading(soup, UKVI_CARD_HEADING))
        la_rows = parse_rows(card_by_heading(soup, LA_CARD_HEADING))

        self.assertTitlesInOrder(la_rows, LA_CHECK_TITLES)
        for (_, href, _), slug in zip(la_rows, LA_CHECK_SLUGS, strict=True):
            if slug == PreApprovalCheckField.SPONSOR_CERTIFICATION_CODE_EMAILED.value:
                self.assertIsNone(href)
            else:
                self.assertEqual(href, edit_url(uam, slug))
        self.assertTrue(all(href is None for _, href, _ in ukvi_rows))

        la_statuses = {title: status for title, _, status in la_rows}
        self.assertEqual(
            la_statuses["Sponsor and household members enhanced DBS"], "Not started"
        )
        self.assertEqual(la_statuses["Code sent to sponsor"], "Cannot send code")

        page_text = soup.get_text()
        self.assertIn(LA_CHECKS_AVAILABLE_MESSAGE, page_text)
        self.assertIn(LA_CANNOT_EDIT_UKVI_MESSAGE, page_text)

    def test_la_user_cannot_edit_la_checks_when_status_not_ready(self):
        uam = SponsorshipCertificationFormFactory(
            reference="SPON-LA-NOT-READY",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            **check_statuses(ukvi="Not started", la="Not started"),
        )

        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.checks_url(uam))
        soup = parse(response)

        ukvi_rows = parse_rows(card_by_heading(soup, UKVI_CARD_HEADING))
        la_rows = parse_rows(card_by_heading(soup, LA_CARD_HEADING))

        self.assertTrue(all(href is None for _, href, _ in ukvi_rows))
        self.assertTrue(all(href is None for _, href, _ in la_rows))

        page_text = soup.get_text()
        self.assertIn(LA_CHECKS_BLOCKED_MESSAGE, page_text)
        self.assertNotIn(LA_CHECKS_AVAILABLE_MESSAGE, page_text)

    def test_la_user_can_edit_all_la_checks_when_status_complete(self):
        uam = SponsorshipCertificationFormFactory(
            reference="SPON-LA-READY",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            **check_statuses(ukvi="Passed", la="Passed"),
        )

        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.checks_url(uam))
        soup = parse(response)

        ukvi_rows = parse_rows(card_by_heading(soup, UKVI_CARD_HEADING))
        la_rows = parse_rows(card_by_heading(soup, LA_CARD_HEADING))

        self.assertTitlesInOrder(la_rows, LA_CHECK_TITLES)
        for (_, href, _), slug in zip(la_rows, LA_CHECK_SLUGS, strict=True):
            self.assertEqual(href, edit_url(uam, slug))
        self.assertTrue(all(href is None for _, href, _ in ukvi_rows))

        la_statuses = {title: status for title, _, status in la_rows}
        self.assertEqual(
            la_statuses["Sponsor and household members enhanced DBS"], "Passed"
        )
        self.assertEqual(la_statuses["Code sent to sponsor"], "Code not sent")

        page_text = soup.get_text()
        self.assertIn(LA_CHECKS_AVAILABLE_MESSAGE, page_text)
        self.assertIn(LA_CANNOT_EDIT_UKVI_MESSAGE, page_text)

    def test_renders_checks_tab(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(self.checks_url(self.checks_uam))
        soup = parse(response)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(active_tab_text(soup), "Checks")
        self.assertIsNotNone(card_by_heading(soup, UKVI_CARD_HEADING))


class UamChecksTabFeatureFlagTests(TestSessionTokenMixin, UamsBaseTestCase):
    def setUp(self):
        super().setUp()

        self.checks_uam = SponsorshipCertificationFormFactory(
            reference="SPON-CHECKS-FLAG",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            **check_statuses(),
        )

    def overview_url(self, uam):
        return reverse("uams:detail-overview", kwargs={"pk": uam.pk})

    def checks_url(self, uam):
        return reverse("uams:detail-checks", kwargs={"pk": uam.pk})

    @override_settings(UAM_CHECKS_ENABLED=False)
    def test_checks_tab_hidden_for_non_dev_user_when_flag_disabled(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.overview_url(self.checks_uam))
        soup = parse(response)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertNotIn("Checks", tab_texts(soup))

    @override_settings(UAM_CHECKS_ENABLED=True)
    def test_checks_tab_shown_for_non_dev_user_when_flag_enabled(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.overview_url(self.checks_uam))
        soup = parse(response)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertIn("Checks", tab_texts(soup))

    @override_settings(UAM_CHECKS_ENABLED=False)
    def test_checks_tab_shown_for_dev_user_regardless_of_flag(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(self.overview_url(self.checks_uam))
        soup = parse(response)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertIn("Checks", tab_texts(soup))

    @override_settings(UAM_CHECKS_ENABLED=True)
    def test_non_dev_user_can_load_checks_tab_when_flag_enabled(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.checks_url(self.checks_uam))
        soup = parse(response)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(active_tab_text(soup), "Checks")
