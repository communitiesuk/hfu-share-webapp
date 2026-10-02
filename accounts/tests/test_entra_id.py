from unittest.mock import ANY, patch

from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponseForbidden
from django.test import RequestFactory
from django.urls import reverse

from accounts.authentication import Authentication
from accounts.exceptions import FlowError, StateMismatchError
from accounts.tests.base import TestSessionTokenMixin
from accounts.views import LOGIN_REDIRECT_SESSION_KEY
from test_utils.base import BaseTestCase
from user_management.tests.base import get_admin_user

ENTRA_DOMAIN = "login.microsoftonline.com"


class EntraIdMissingSessionTokenTestCase(BaseTestCase):
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
    def test_entra_callback_renders_access_denied_page_if_flow_missing(
        self, mock_get_token_from_flow
    ):
        mock_get_token_from_flow.side_effect = FlowError(
            "Flow cannot be extracted from session"
        )

        with self.settings(ENTRA_ID_ENABLED=True):
            response = self.client.get(reverse("accounts:callback"))

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")
        self.assertContains(response, "Access Denied", status_code=403)

    @patch("accounts.views.Authentication.get_token_from_flow")
    def test_entra_callback_renders_access_denied_page_if_state_mismatched(
        self, mock_get_token_from_flow
    ):
        mock_get_token_from_flow.side_effect = StateMismatchError(
            "State in the auth response does not match the stored flow"
        )

        with self.settings(ENTRA_ID_ENABLED=True):
            response = self.client.get(reverse("accounts:callback"))

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")
        self.assertContains(response, "Access Denied", status_code=403)

    @patch("accounts.views.Authentication.get_token_from_flow")
    @patch("accounts.views.authenticate")
    def test_entra_callback_renders_access_denied_page_if_not_authenticated(
        self, mock_authenticate, mock_get_token_from_flow
    ):
        mock_get_token_from_flow.return_value = "token"
        mock_authenticate.return_value = None

        with self.settings(ENTRA_ID_ENABLED=True):
            response = self.client.get(reverse("accounts:callback"))

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")
        self.assertContains(response, "Access Denied", status_code=403)


class EntraIdRedirectsUserToPageTheyWantedToVisitTestCase(BaseTestCase):
    @patch("accounts.views.Authentication.get_auth_uri")
    @patch("accounts.views.Authentication.get_token_from_flow")
    @patch("accounts.views.authenticate")
    def test_redirects_to_the_page_they_wanted_to_visit(
        self, mock_authenticate, mock_get_token_from_flow, mock_get_auth_uri
    ):
        mock_get_auth_uri.return_value = "https://example.com/auth"
        mock_get_token_from_flow.return_value = "token"
        entra_user = get_admin_user()
        entra_user.backend = "accounts.backend.EntraBackend"
        mock_authenticate.return_value = entra_user

        test_url = "/test-page-that-the-user-wants"

        with self.settings(ENTRA_ID_ENABLED=True):
            login_response = self.client.get(
                reverse("accounts:login"), {"next": test_url}, follow=False
            )
            self.assertEqual(login_response.status_code, 302)
            self.assertEqual(self.client.session[LOGIN_REDIRECT_SESSION_KEY], test_url)

            callback_response = self.client.get(reverse("accounts:callback"))
            self.assertRedirects(
                callback_response, test_url, fetch_redirect_response=False
            )

    @patch("accounts.views.Authentication.get_auth_uri")
    @patch("accounts.views.Authentication.get_token_from_flow")
    @patch("accounts.views.authenticate")
    def test_does_not_redirect_to_an_unsafe_next_url(
        self, mock_authenticate, mock_get_token_from_flow, mock_get_auth_uri
    ):
        mock_get_auth_uri.return_value = "https://example.com/auth"
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
                    self.client.session.flush()
                    self.client.get(reverse("accounts:login"), {"next": next_url})
                    self.assertNotIn(LOGIN_REDIRECT_SESSION_KEY, self.client.session)

                    response = self.client.get(reverse("accounts:callback"))
                    self.assertRedirects(
                        response,
                        settings.LOGIN_REDIRECT_URL,
                        fetch_redirect_response=False,
                    )

    @patch("accounts.views.Authentication.get_auth_uri")
    @patch("accounts.views.Authentication.get_token_from_flow")
    @patch("accounts.views.authenticate")
    def test_redirects_to_the_landing_page_if_no_next_url(
        self, mock_authenticate, mock_get_token_from_flow, mock_get_auth_uri
    ):
        mock_get_auth_uri.return_value = "https://example.com/auth"
        mock_get_token_from_flow.return_value = "token"
        entra_user = get_admin_user()
        entra_user.backend = "accounts.backend.EntraBackend"
        mock_authenticate.return_value = entra_user

        with self.settings(ENTRA_ID_ENABLED=True):
            self.client.session.flush()
            self.client.get(reverse("accounts:login"))
            self.assertNotIn(LOGIN_REDIRECT_SESSION_KEY, self.client.session)

            response = self.client.get(reverse("accounts:callback"))
            self.assertRedirects(
                response, settings.LOGIN_REDIRECT_URL, fetch_redirect_response=False
            )


class EntraIdSessionTokenTestCase(TestSessionTokenMixin, BaseTestCase):
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


class EntraIdStateMismatchTestCase(TestSessionTokenMixin, BaseTestCase):
    @patch("accounts.views.Authentication.get_token_from_flow")
    def test_entra_callback_does_not_log_out_an_existing_user(
        self, mock_get_token_from_flow
    ):
        mock_get_token_from_flow.side_effect = StateMismatchError("state mismatch")
        entra_user = get_admin_user()
        self.client.force_login(entra_user)

        with self.settings(ENTRA_ID_ENABLED=True):
            self.client.get(reverse("accounts:callback"))

        self.assertEqual(self.client.session[SESSION_KEY], str(entra_user.pk))


class GetTokenFromFlowStateTestCase(BaseTestCase):
    def _get_authentication(self, flow, query):
        request = RequestFactory().get(reverse("accounts:callback"), query)
        SessionMiddleware(lambda _request: None).process_request(request)
        request.session["auth_flow"] = flow
        return Authentication(request)

    @patch("accounts.authentication.Authentication.msal_app")
    def test_raises_if_the_response_state_does_not_match_the_flow(self, mock_msal_app):
        authentication = self._get_authentication(
            flow={"state": "the-state-we-issued"},
            query={"state": "a-different-state", "code": "some-code"},
        )

        with self.assertRaises(StateMismatchError):
            authentication.get_token_from_flow()

        mock_msal_app.acquire_token_by_auth_code_flow.assert_not_called()

    @patch("accounts.authentication.Authentication.msal_app")
    def test_exchanges_the_code_when_the_state_matches(self, mock_msal_app):
        mock_msal_app.acquire_token_by_auth_code_flow.return_value = {
            "access_token": "an-access-token",
            "id_token_claims": {},
        }
        authentication = self._get_authentication(
            flow={"state": "the-state-we-issued"},
            query={"state": "the-state-we-issued", "code": "some-code"},
        )

        token = authentication.get_token_from_flow()

        self.assertEqual(token["access_token"], "an-access-token")
        mock_msal_app.acquire_token_by_auth_code_flow.assert_called_once()
