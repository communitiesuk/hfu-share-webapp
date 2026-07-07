from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from user_management.tests.base import get_user_with_no_access


class CookiesPageTests(TestSessionTokenMixin, TestCase):
    def test_cookies_page_is_displayed(self):
        user = get_user_with_no_access()
        self.client.force_login(user)

        response = self.client.get(reverse("webapp:cookies"))

        self.assertContains(
            response,
            "Cookies are small files saved on your phone",
        )
        self.assertTemplateUsed(
            response,
            "webapp/pages/cookies/cookies.html",
        )

    @patch("case_management.settings.GOOGLE_ANALYTICS_ENABLED", "Enabled")
    @patch("case_management.settings.GOOGLE_ANALYTICS_ID", "G-1234")
    def test_cookies_page_includes_analytics_info_if_enabled(self):
        user = get_user_with_no_access()
        self.client.force_login(user)

        response = self.client.get(reverse("webapp:cookies"))

        self.assertContains(
            response,
            "Analytics cookies (optional)",
        )
        # Main cookie info should still be displayed
        self.assertContains(
            response,
            "Cookies are small files saved on your phone",
        )

    @patch("case_management.settings.GOOGLE_ANALYTICS_ENABLED", "Disabled")
    @patch("case_management.settings.GOOGLE_ANALYTICS_ID", "G-1234")
    def test_cookies_page_does_not_include_analytics_info_if_disabled(self):
        user = get_user_with_no_access()
        self.client.force_login(user)

        response = self.client.get(reverse("webapp:cookies"))

        self.assertNotContains(
            response,
            "Analytics cookies (optional)",
        )
        self.assertNotContains(
            response,
            "Do you want to accept analytics cookies?",
        )
        # Main cookie info should still be displayed
        self.assertContains(
            response,
            "Cookies are small files saved on your phone",
        )

    def test_cookies_link_is_displayed_in_footer_on_other_pages(self):
        user = get_user_with_no_access()
        self.client.force_login(user)

        response = self.client.get(reverse("webapp:landing-page"))

        # assert link is displayed in the footer
        self.assertContains(response, reverse("webapp:cookies"))
