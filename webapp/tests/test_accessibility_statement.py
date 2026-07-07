from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from user_management.tests.base import get_user_with_no_access


class AccessibilityStatementPageTests(TestSessionTokenMixin, TestCase):
    def test_accessibility_statement_page_is_displayed(self):
        user = get_user_with_no_access()
        self.client.force_login(user)

        response = self.client.get(reverse("webapp:accessibility-statement"))

        self.assertContains(
            response, "Accessibility statement for Share Homes for Ukraine data (Share)"
        )
        self.assertTemplateUsed(
            response,
            "webapp/pages/accessibility_statement/accessibility_statement.html",
        )

        # assert link is displayed once, in the footer
        self.assertContains(response, reverse("webapp:accessibility-statement"), 1)

    def test_accessibility_statement_link_is_displayed_in_footer(self):
        user = get_user_with_no_access()
        self.client.force_login(user)

        response = self.client.get(reverse("webapp:landing-page"))

        # assert link is displayed once, in the footer
        self.assertContains(response, reverse("webapp:accessibility-statement"), 1)
