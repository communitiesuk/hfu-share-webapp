from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from django.test import TestCase

from accounts.tests.base import TestSessionTokenMixin
from user_management.tests.base import (
    get_admin_user,
    get_user_with_no_access,
)


class ErrorPageTests(TestSessionTokenMixin, TestCase):
    def test_should_render_custom_404_template_if_url_not_found(self):
        user = get_user_with_no_access()
        self.client.force_login(user)

        response = self.client.get("/not-a-real-page")

        self.assertTemplateUsed(response, "404.html")

    @patch("webapp.views.LandingPageView.get_tables")
    def test_should_render_custom_500_template_if_error_raised(self, get_tables):
        get_tables.side_effect = Exception("Unexpected error")

        user = get_admin_user()
        self.client.force_login(user)
        self.client.raise_request_exception = False

        response = self.client.get("/landing-page")

        self.assertEqual(response.status_code, 500)
        self.assertTemplateUsed(response, "500.html")

    def test_500_template_renders_with_empty_context(self):
        # handler500 renders with no request context and no context
        # processors, so the shared partials included in 500.html must not
        # rely on any context variables
        html = render_to_string("500.html")

        self.assertIn("Sorry, there is a problem with the service", html)
        self.assertIn("govuk-phase-banner", html)
        self.assertIn("govuk-footer", html)
        self.assertIn("Open Government Licence", html)

    @patch("webapp.views.LandingPageView.get_tables")
    def test_should_render_custom_403_template_if_access_denied(self, get_tables):
        get_tables.side_effect = PermissionDenied("Access denied")

        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get("/landing-page")
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")
