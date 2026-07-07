from unittest.mock import patch

from django.core.exceptions import PermissionDenied
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

        with self.assertRaisesMessage(Exception, "Unexpected error"):
            response = self.client.get("/landing-page")
            self.assertTemplateUsed(response, "500.html")

    @patch("webapp.views.LandingPageView.get_tables")
    def test_should_render_custom_403_template_if_access_denied(self, get_tables):
        get_tables.side_effect = PermissionDenied("Access denied")

        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get("/landing-page")
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")
