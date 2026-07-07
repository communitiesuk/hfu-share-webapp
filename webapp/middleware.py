import logging
import time
import uuid

from django.http import Http404, HttpResponse
from django.shortcuts import redirect

from case_management import settings

logger = logging.getLogger(__name__)


class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/health":
            return HttpResponse("ok")
        return self.get_response(request)


class RequestTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time_ns()
        request_id = str(uuid.uuid4())[:6]

        # Log user if available in session
        user = request.user
        user_id = f"User ID {user.id}" if user.is_authenticated else "Unknown user ID"

        logger.info(
            "%s started request %s to %s.",
            user_id,
            request_id,
            request.get_full_path(),
        )
        response = self.get_response(request)

        processing_time = time.time_ns() - start_time

        logger.info(
            "Request %s to %s took %.6f seconds.",
            request_id,
            request.get_full_path(),
            processing_time / 1e9,
        )

        return response

    def process_template_response(self, _, response):
        response.context_data["environment"] = settings.ENVIRONMENT

        return response


class AdminAreaRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin"):
            user = request.user
            if not user.is_authenticated or not user.is_staff:
                raise Http404("Not found")
        return self.get_response(request)


class LandingPageRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "GET" and request.path == "/":
            redirect_response = self.landing_page_redirect(request)
            if redirect_response:
                return redirect_response

        return self.get_response(request)

    def landing_page_redirect(self, request):
        if request.user.is_authenticated:
            return redirect("webapp:landing-page")
        # User isn't logged in.
        # No action here: LoginRequiredMiddleware will handle this instead.
        return None


class PermissionsPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Deny everything by default — empty () for each feature
        response.headers["Permissions-Policy"] = (
            "microphone=(), camera=(), geolocation=(), "  # Privacy
            "autoplay=(), fullscreen=(), picture-in-picture=(), "  # Video features
            "payment=(), usb=(), "  # Payment and USB access
            "accelerometer=(), gyroscope=(), magnetometer=(), "  # Sensors
            "publickey-credentials-get=(), display-capture=(), web-share=(), "  # Misc
            "interest-cohort=()"  # FLoC
        )

        return response


class GoogleAnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_template_response(self, request, response):
        cookie_consent = request.COOKIES.get("cookie_consent", "unknown")
        response.context_data["cookie_consent"] = cookie_consent

        if (
            settings.GOOGLE_ANALYTICS_ID
            and settings.GOOGLE_ANALYTICS_ENABLED == "Enabled"
        ):
            # Include cookie banner code
            response.context_data["analytics_enabled"] = True
            response.context_data["google_analytics_id"] = settings.GOOGLE_ANALYTICS_ID

        if cookie_consent == "true":
            # Enable analytics events
            response.context_data["analytics_consent_granted"] = True
        elif cookie_consent in ["false", "unknown"]:
            # Make absolutely sure the consent is disabled
            response.context_data["analytics_consent_granted"] = False
        else:
            # Don't log the unknown value directly in case of malicious cookie/PII
            logger.warning("Analytics consent cookie value not recognised")

        return response
