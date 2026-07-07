import http.client
from unittest.mock import call, patch

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse, HttpResponseRedirect
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from accounts.tests.factories import UserFactory
from user_management.tests.base import get_la_user
from webapp.middleware import LandingPageRedirectMiddleware, RequestTimeMiddleware


class HealthCheckMiddlewareTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check_ok(self):
        """Test /health returns 200 when the system is up."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, http.client.OK)

    def test_health_check_next_ok(self):
        """Test / returns 302 when the system is up."""

        response = self.client.get("/")
        self.assertEqual(response.status_code, http.client.FOUND)

    @patch("webapp.middleware.HealthCheckMiddleware.__call__")
    def test_health_check_not_ok(self, mock_health_check_middleware):
        """Test /health returns 5xx when the system is down."""

        def _failing_call(request):
            if request.path == "/health":
                return HttpResponse(
                    "Service Unavailable", status=http.client.INTERNAL_SERVER_ERROR
                )
            return HttpResponse("ok")

        mock_health_check_middleware.side_effect = _failing_call

        response = self.client.get("/health")
        self.assertEqual(response.status_code, http.client.INTERNAL_SERVER_ERROR)


class LandingPageRedirectMiddlewareTests(TestCase):
    EXPECTED_URL = "/landing-page"

    def setUp(self):
        self.factory = RequestFactory()

    def assert_response_redirected(self, response, expected_url):
        self.assertEqual(response.status_code, http.client.FOUND)
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, expected_url)

    def build_user(self, is_dev=False, is_superuser=False):
        return UserFactory(is_dev=is_dev, is_superuser=is_superuser)

    def assert_request_redirected(self, request, expected_url):
        middleware = LandingPageRedirectMiddleware(
            lambda _: self.fail("Should have redirected but called get_response")
        )
        response = middleware(request)
        self.assert_response_redirected(response, expected_url)

    def assert_request_not_redirected(self, request):
        middleware = LandingPageRedirectMiddleware(lambda _: HttpResponse("content"))
        response = middleware(request)
        self.assertEqual(response.status_code, http.client.OK)

    def test_dev_user_redirected_to_landing_page(self):
        """Test GET / for a dev user is redirected to the general landing page."""
        request = self.factory.get("/")
        request.user = self.build_user(is_dev=True)
        self.assert_request_redirected(request, self.EXPECTED_URL)

    def test_superuser_redirected_to_landing_page(self):
        """Test GET / for a superuser is redirected to the general landing page."""
        request = self.factory.get("/")
        request.user = self.build_user(is_superuser=True)
        self.assert_request_redirected(request, self.EXPECTED_URL)

    def test_other_redirected_to_landing_page(self):
        """Test GET / for a normal user is redirected to the general landing page."""
        request = self.factory.get("/")
        request.user = self.build_user()
        self.assert_request_redirected(request, self.EXPECTED_URL)

    def test_anonymous_user_not_redirected(self):
        """Test GET / for a not-logged-in user is not redirected."""
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assert_request_not_redirected(request)

    def test_dev_user_post_is_not_redirected(self):
        """Test POST / for a dev user is not redirected."""
        request = self.factory.post("/")
        request.user = self.build_user(is_dev=True)
        self.assert_request_not_redirected(request)

    def test_dev_user_get_other_page_is_not_redirected(self):
        """Test GET /apps/visa-applications for a dev user is not redirected."""
        request = self.factory.post("/apps/visa-applications")
        request.user = self.build_user(is_dev=True)
        self.assert_request_not_redirected(request)


class CSPMiddlewareTests(TestSessionTokenMixin, TestCase):
    def test_header_is_set(self):
        self.client.force_login(get_la_user())
        response = self.client.get("/")

        self.assertIn("Content-Security-Policy", response.headers)

    def test_csp_report_view_post_method_returns_204(self):
        self.client.force_login(get_la_user())
        example_csp_report_json = {"csp-report": "value"}
        with patch("webapp.views.logger") as mock_logger:
            response = self.client.post("/csp-report/", example_csp_report_json)

            self.assertEqual(response.status_code, 204)
            mock_logger.warning.assert_called_once_with(
                "CSP Violation: %s",
                '--BoUnDaRyStRiNg\r\nContent-Disposition: form-data; name="csp-report"\r\n\r\nvalue\r\n--BoUnDaRyStRiNg--\r\n',  # noqa E501
            )

    def test_csp_report_view_get_method_returns_405(self):
        self.client.force_login(get_la_user())
        response = self.client.get("/csp-report/")

        self.assertEqual(response.status_code, 405)


class PermissionsPolicyMiddlewareTests(TestSessionTokenMixin, TestCase):
    def test_header_is_set(self):
        self.client.force_login(get_la_user())
        response = self.client.get("/")

        self.assertIn("Permissions-Policy", response.headers)
        self.assertEqual(
            response.headers["Permissions-Policy"],
            "microphone=(), camera=(), geolocation=(), "
            "autoplay=(), fullscreen=(), picture-in-picture=(), "
            "payment=(), usb=(), accelerometer=(), gyroscope=(), "
            "magnetometer=(), publickey-credentials-get=(), "
            "display-capture=(), web-share=(), interest-cohort=()",
        )


class GoogleAnalyticsMiddlewareTests(TestSessionTokenMixin, TestCase):
    GOOGLE_ANALYTICS_SCRIPT_URL = "https://www.googletagmanager.com/gtag/js?id=G-1234"

    @patch("case_management.settings.GOOGLE_ANALYTICS_ENABLED", "AnyOtherValue")
    @patch("case_management.settings.GOOGLE_ANALYTICS_ID", "G-1234")
    def test_google_analytics_script_is_not_rendered_if_setting_is_not_enabled(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertNotContains(response, self.GOOGLE_ANALYTICS_SCRIPT_URL)
        # Cookie banner should be hidden
        self.assertNotContains(response, '<div class="govuk-cookie-banner')
        # Assert landing page shows as normal
        self.assertContains(response, "Welcome")

    @patch("case_management.settings.GOOGLE_ANALYTICS_ENABLED", "Enabled")
    @patch("case_management.settings.GOOGLE_ANALYTICS_ID", None)
    def test_google_analytics_script_is_not_rendered_if_id_is_missing(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertNotContains(response, self.GOOGLE_ANALYTICS_SCRIPT_URL)
        # Cookie banner should be hidden
        self.assertNotContains(response, '<div class="govuk-cookie-banner')
        # Assert landing page shows as normal
        self.assertContains(response, "Welcome")

    @patch("case_management.settings.GOOGLE_ANALYTICS_ENABLED", "Enabled")
    @patch("case_management.settings.GOOGLE_ANALYTICS_ID", "G-1234")
    def test_google_analytics_script_rendered_in_template_if_consent_given(self):
        user = get_la_user()
        self.client.force_login(user)
        self.client.cookies.load({"cookie_consent": "true"})
        response = self.client.get(reverse("webapp:landing-page"))

        self.assertContains(response, self.GOOGLE_ANALYTICS_SCRIPT_URL)
        # Cookie banner should be in the response (but hidden via javascript)
        self.assertContains(response, '<div class="govuk-cookie-banner')
        # Assert landing page shows as normal
        self.assertContains(response, "Welcome")

    @patch("case_management.settings.GOOGLE_ANALYTICS_ENABLED", "Enabled")
    @patch("case_management.settings.GOOGLE_ANALYTICS_ID", "G-1234")
    def test_google_analytics_script_is_not_rendered_if_consent_is_missing(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertNotContains(response, self.GOOGLE_ANALYTICS_SCRIPT_URL)
        # Cookie banner should be in the response
        self.assertContains(response, '<div class="govuk-cookie-banner')
        # Assert landing page shows as normal
        self.assertContains(response, "Welcome")

    @patch("case_management.settings.GOOGLE_ANALYTICS_ENABLED", "Enabled")
    @patch("case_management.settings.GOOGLE_ANALYTICS_ID", "G-1234")
    def test_google_analytics_script_is_not_rendered_if_consent_is_false(self):
        user = get_la_user()
        self.client.force_login(user)
        self.client.cookies.load({"cookie_consent": "false"})

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertNotContains(response, self.GOOGLE_ANALYTICS_SCRIPT_URL)
        # Cookie banner should be in the response (but hidden via javascript)
        self.assertContains(response, '<div class="govuk-cookie-banner')
        # Assert landing page shows as normal
        self.assertContains(response, "Welcome")


class RequestTimeMiddlewareTests(TestCase):
    def setUp(self):
        self.Middleware = RequestTimeMiddleware
        self.rf = RequestFactory()

    def test_logs_start_and_processing_time_with_same_request_id(self):
        req = self.rf.get("/ping")
        req.user = AnonymousUser()
        res = HttpResponse("ok", status=200)

        with (
            patch("webapp.middleware.time.time_ns", side_effect=[1_000, 1_250]),
            patch("webapp.middleware.uuid.uuid4", return_value="abc123def456"),
            patch("webapp.middleware.logger") as mock_logger,
        ):
            mw = self.Middleware(lambda r: res)
            returned = mw(req)

        self.assertIs(returned, res)

        expected_secs = 250 / 1e9
        # request_id is first 6 chars of patched uuid ("abc123def456")
        rid = "abc123"

        expected_calls = [
            call("%s started request %s to %s.", "Unknown user ID", rid, "/ping"),
            call("Request %s to %s took %.6f seconds.", rid, "/ping", expected_secs),
        ]
        self.assertEqual(mock_logger.info.call_count, 2)
        mock_logger.info.assert_has_calls(expected_calls)

    def test_logs_include_user_id_if_authenticated(self):
        user = get_la_user()
        req = self.rf.get("/ping")
        req.user = user
        res = HttpResponse("ok", status=200)

        with (
            patch("webapp.middleware.time.time_ns", side_effect=[1_000, 1_250]),
            patch("webapp.middleware.uuid.uuid4", return_value="abc123def456"),
            patch("webapp.middleware.logger") as mock_logger,
        ):
            mw = self.Middleware(lambda r: res)
            returned = mw(req)

        self.assertIs(returned, res)

        expected_secs = 250 / 1e9
        # request_id is first 6 chars of patched uuid ("abc123def456")
        rid = "abc123"
        userid_string = f"User ID {user.id}"

        expected_calls = [
            call("%s started request %s to %s.", userid_string, rid, "/ping"),
            call("Request %s to %s took %.6f seconds.", rid, "/ping", expected_secs),
        ]
        self.assertEqual(mock_logger.info.call_count, 2)
        mock_logger.info.assert_has_calls(expected_calls)

    def test_returns_get_response_result_unmodified(self):
        req = self.rf.get("/anything")
        req.user = AnonymousUser()
        res = HttpResponse("payload", status=204)

        with (
            patch("webapp.middleware.time.time_ns", side_effect=[5, 10]),
            patch("webapp.middleware.uuid.uuid4", return_value="abcdef123456"),
            patch("webapp.middleware.logger"),
        ):
            mw = self.Middleware(lambda r: res)
            returned = mw(req)

        self.assertIs(returned, res)
        self.assertEqual(returned.status_code, 204)
        self.assertEqual(returned.content, b"payload")

    def test_logs_full_path_including_querystring_on_both_lines(self):
        req = self.rf.get("/items?search=abc")
        req.user = AnonymousUser()
        res = HttpResponse("ok")

        with (
            patch("webapp.middleware.time.time_ns", side_effect=[100, 200]),
            patch("webapp.middleware.uuid.uuid4", return_value="cafebabe0000"),
            patch("webapp.middleware.logger") as mock_logger,
        ):
            mw = self.Middleware(lambda r: res)
            mw(req)

        expected_secs = 100 / 1e9
        rid = "cafeba"  # first 6 chars

        expected_calls = [
            call(
                "%s started request %s to %s.",
                "Unknown user ID",
                rid,
                "/items?search=abc",
            ),
            call(
                "Request %s to %s took %.6f seconds.",
                rid,
                "/items?search=abc",
                expected_secs,
            ),
        ]
        self.assertEqual(mock_logger.info.call_count, 2)
        mock_logger.info.assert_has_calls(expected_calls)
