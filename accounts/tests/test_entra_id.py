from unittest.mock import ANY, patch
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.http import HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse

from accounts.exceptions import FlowError
from accounts.tests.base import TestSessionTokenMixin
from user_management.tests.base import get_admin_user

ENTRA_DOMAIN = "login.microsoftonline.com"


class EntraIdMissingSessionTokenTestCase(TestCase):
    def test_redirect_if_not_logged_in_with_any_user(self):
        with self.settings(ENTRA_ID_ENABLED=True):
            response = self.client.get("/", follow=True)
            self.assertEqual(response.request.get("SERVER_NAME"), ENTRA_DOMAIN)
            self.assertEqual(response.status_code, 400)
            final_redirect_url, final_status_code = response.redirect_chain[-1]
            assert ENTRA_DOMAIN in final_redirect_url
            assert final_status_code == 302

    def test_redirect_if_logged_in_without_entra_id(self):
        with self.settings(ENTRA_ID_ENABLED=True):
            self.client.force_login(get_admin_user())
            response = self.client.get("/", follow=True)
            self.assertEqual(response.request.get("SERVER_NAME"), ENTRA_DOMAIN)
            self.assertEqual(response.status_code, 400)
            final_redirect_url, final_status_code = response.redirect_chain[-1]
            assert ENTRA_DOMAIN in final_redirect_url
            assert final_status_code == 302

    def test_entra_callback_raises_403_error_if_no_user(self):
        with self.settings(ENTRA_ID_ENABLED=True):
            with self.assertRaises(Exception) as context:
                self.client.get(reverse("accounts:callback"))
                assert context.exception is HttpResponseForbidden
                assert context.msg == "You are not allowed to access this application."

    @patch("accounts.views.Authentication.get_token_from_flow")
    def test_entra_callback_returns_403_if_flow_missing(self, mock_get_token_from_flow):
        mock_get_token_from_flow.side_effect = FlowError(
            "Flow cannot be extracted from session"
        )

        with self.settings(ENTRA_ID_ENABLED=True):
            response = self.client.get(reverse("accounts:callback"))

        self.assertContains(
            response,
            "Unable to complete authentication process. Please try to login again.",
            status_code=403,
        )


class EntraIdRedirectsUserToPageTheyWantedToVisitTestCase(TestCase):
    @patch("accounts.authentication.Authentication.get_token_from_flow")
    @patch("accounts.views.authenticate")
    def test_redirects_to_the_page_they_wanted_to_visit(
        self, mock_authenticate, mock_get_token_from_flow
    ):
        mock_get_token_from_flow.return_value = "token"
        entra_user = get_admin_user()
        entra_user.backend = "accounts.backend.EntraBackend"
        mock_authenticate.return_value = entra_user

        test_url = "/test-page-that-the-user-wants"

        with self.settings(ENTRA_ID_ENABLED=True):
            self.client.force_login(get_admin_user())
            response = self.client.get(test_url, follow=True)

            final_redirect_url, _ = response.redirect_chain[-1]
            parsed_redirect_url = urlparse(final_redirect_url)
            state = parse_qs(parsed_redirect_url.query)["state"][0]

            auth_callback = reverse("accounts:callback") + "?state=" + state

            response = self.client.get(auth_callback)
            self.assertRedirects(response, test_url, fetch_redirect_response=False)

    @patch("accounts.authentication.Authentication.get_token_from_flow")
    @patch("accounts.views.authenticate")
    def test_does_not_redirect_to_an_unsafe_next_url(
        self, mock_authenticate, mock_get_token_from_flow
    ):
        mock_get_token_from_flow.return_value = "token"
        entra_user = get_admin_user()
        entra_user.backend = "accounts.backend.EntraBackend"
        mock_authenticate.return_value = entra_user

        unsafe_next_urls = [
            "https://evil.com",  # external domain
            "//evil.com",  # protocol-relative
        ]

        for next_url in unsafe_next_urls:
            with self.subTest(next_url=next_url):
                with self.settings(ENTRA_ID_ENABLED=True):
                    self.client.force_login(get_admin_user())
                    response = self.client.get(f"/login?next={next_url}", follow=True)

                    final_redirect_url, _ = response.redirect_chain[-1]
                    parsed_redirect_url = urlparse(final_redirect_url)
                    state = parse_qs(parsed_redirect_url.query)["state"][0]

                    auth_callback = reverse("accounts:callback") + "?state=" + state

                    response = self.client.get(auth_callback)
                    self.assertRedirects(
                        response,
                        settings.LOGIN_REDIRECT_URL,
                        fetch_redirect_response=False,
                    )

    @patch("accounts.authentication.Authentication.get_token_from_flow")
    @patch("accounts.views.authenticate")
    def test_redirects_to_the_landing_page_if_no_next_url(
        self, mock_authenticate, mock_get_token_from_flow
    ):
        mock_get_token_from_flow.return_value = "token"
        entra_user = get_admin_user()
        entra_user.backend = "accounts.backend.EntraBackend"
        mock_authenticate.return_value = entra_user

        test_url = "/test-page-that-the-user-wants"

        with self.settings(ENTRA_ID_ENABLED=True):
            self.client.force_login(get_admin_user())
            self.client.get(test_url, follow=True)

            auth_callback = reverse("accounts:callback")

            response = self.client.get(auth_callback)
            self.assertRedirects(
                response, settings.LOGIN_REDIRECT_URL, fetch_redirect_response=False
            )


class EntraIdSessionTokenTestCase(TestSessionTokenMixin, TestCase):
    def test_redirects_to_landing_page_if_logged_in_with_entra_id(self):
        with self.settings(ENTRA_ID_ENABLED=True):
            self.client.force_login(get_admin_user())
            response = self.client.get("/")
            self.assertRedirects(response, reverse("webapp:landing-page"))

    @patch("accounts.authentication.Authentication.get_token_from_flow")
    @patch("accounts.views.authenticate")
    def test_entra_callback_redirects_if_user_authenticated(
        self, mock_authenticate, mock_get_token_from_flow
    ):
        mock_get_token_from_flow.return_value = "token"
        entra_user = get_admin_user()
        entra_user.backend = "accounts.backend.EntraBackend"
        mock_authenticate.return_value = entra_user

        with self.settings(ENTRA_ID_ENABLED=True):
            response = self.client.get(reverse("accounts:callback"))
            self.assertRedirects(
                response, settings.LOGIN_REDIRECT_URL, fetch_redirect_response=False
            )

    @patch("accounts.authentication.Authentication.get_token_from_flow")
    @patch("accounts.views.authenticate")
    def test_entra_callback_authenticates_with_token_from_flow(
        self, mock_authenticate, mock_get_token_from_flow
    ):
        mock_get_token_from_flow.return_value = "token"
        entra_user = get_admin_user()
        entra_user.backend = "accounts.backend.EntraBackend"
        mock_authenticate.return_value = entra_user

        request_passed_to_authenticate = ANY
        with self.settings(ENTRA_ID_ENABLED=True):
            self.client.get(reverse("accounts:callback"))

        mock_authenticate.assert_called_once_with(
            request_passed_to_authenticate, token="token"
        )

    @patch("accounts.authentication.Authentication.get_token_from_flow")
    @patch("accounts.views.authenticate")
    def test_entra_callback_logs_in_the_authenticated_user(
        self, mock_authenticate, mock_get_token_from_flow
    ):
        mock_get_token_from_flow.return_value = "token"
        entra_user = get_admin_user()
        entra_user.backend = "accounts.backend.EntraBackend"
        mock_authenticate.return_value = entra_user

        with self.settings(ENTRA_ID_ENABLED=True):
            self.client.get(reverse("accounts:callback"))

        session_user_id = self.client.session[SESSION_KEY]
        self.assertEqual(session_user_id, str(entra_user.pk))

    def test_logout_redirects_to_entra_id_logout(self):
        with self.settings(ENTRA_ID_ENABLED=True):
            self.client.force_login(get_admin_user())
            response = self.client.get(reverse("accounts:logout"))
            self.assertRedirects(
                response,
                f"{settings.ENTRA_AUTH['AUTHORITY']}/oauth2/v2.0/logout?",
                fetch_redirect_response=False,
            )
