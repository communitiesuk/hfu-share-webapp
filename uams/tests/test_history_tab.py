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
PreApprovalCheckStatus = SponsorshipCertificationForm.PreApprovalCheckStatus

HISTORY_DESCRIPTION = (
    "This history shows the dates a change was made to the application to "
    "sponsor a child record on the system."
)


def parse(response):
    return BeautifulSoup(response.content.decode("utf-8"), "html.parser")


def tab_texts(soup):
    return [a.get_text(strip=True) for a in soup.select(".moj-side-navigation a")]


# TODO: Remove decorator when releasing the feature to all
@override_settings(UAM_CHECKS_ENABLED=True)
class UamDetailHistoryViewTests(TestSessionTokenMixin, UamsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.uam = SponsorshipCertificationFormFactory(
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )
        self.history_url = reverse("uams:detail-history", kwargs={"pk": self.uam.pk})

    def test_user_without_access_to_requested_uam_is_denied_access(self):
        self.client.force_login(self.ltla_two_a_user)
        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_dev_user_is_granted_access(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_granted_access(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_granted_access(self):
        self.client.force_login(get_da_user())
        response = self.client.get(
            reverse("uams:detail-history", kwargs={"pk": self.scotland_da_uam.pk})
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_mhclg_user_is_granted_access(self):
        self.client.force_login(get_mhclg_user())
        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, http.client.OK)

    def test_ukvi_user_is_granted_access(self):
        self.client.force_login(get_ukvi_user())
        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, http.client.OK)

    def test_service_support_user_is_granted_access(self):
        self.client.force_login(get_service_support_user())
        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, http.client.OK)

    def test_history_description_is_displayed(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, HISTORY_DESCRIPTION)

    def test_shows_no_events_when_nothing_has_changed(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.history_url)

        self.assertContains(response, "No events")

    def test_shows_check_update_interactions(self):
        admin_user = get_admin_user()
        self.uam.update_pre_approval_check_status(
            PreApprovalCheckField.UK_CONSENT_FORM_STATUS,
            PreApprovalCheckStatus.PASSED,
            admin_user,
        )

        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.history_url)

        self.assertContains(response, "UK consent form check")
        self.assertContains(response, "UK consent form: passed")
        self.assertContains(response, admin_user.email)

    def test_does_not_show_interactions_for_other_uams(self):
        other_uam = SponsorshipCertificationFormFactory(
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )
        other_uam.update_pre_approval_check_status(
            PreApprovalCheckField.UKRAINE_CONSENT_FORM_STATUS,
            PreApprovalCheckStatus.FAILED,
            get_admin_user(),
        )

        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.history_url)

        self.assertNotContains(response, "Ukraine consent form check")
        self.assertContains(response, "No events")

    def test_history_tab_is_shown(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(
            reverse("uams:detail-overview", kwargs={"pk": self.uam.pk})
        )

        self.assertIn("History", tab_texts(parse(response)))


# TODO: Remove this class of tests when releasing the feature to all
@override_settings(UAM_CHECKS_ENABLED=False)
class UamDetailHistoryViewFeatureFlagTests(TestSessionTokenMixin, UamsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.uam = SponsorshipCertificationFormFactory(
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )
        self.overview_url = reverse("uams:detail-overview", kwargs={"pk": self.uam.pk})
        self.history_url = reverse("uams:detail-history", kwargs={"pk": self.uam.pk})

    def test_history_tab_hidden_for_non_dev_user_when_flag_disabled(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.overview_url)

        self.assertNotIn("History", tab_texts(parse(response)))

    def test_non_dev_user_denied_when_flag_disabled(self):
        self.client.force_login(self.ltla_one_a_user)
        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_dev_user_can_view_history_regardless_of_flag(self):
        self.client.force_login(get_admin_user())
        overview_response = self.client.get(self.overview_url)
        history_response = self.client.get(self.history_url)

        self.assertIn("History", tab_texts(parse(overview_response)))
        self.assertEqual(history_response.status_code, http.client.OK)
