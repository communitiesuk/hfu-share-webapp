from django.conf import settings

from .page_title import get_title


def app_context(request):
    return {
        "SERVICE_NAME": settings.SERVICE_NAME,
        "TITLE": get_title(request, settings.SERVICE_NAME),
    }


def govuk_assets(request):
    version = settings.GOVUK_FRONTEND_VERSION

    return {
        "GOVUK_CSS_PATH": f"gds/govuk-frontend-{version}.min.css",
        "GOVUK_JS_PATH": f"gds/govuk-frontend-{version}.min.js",
    }
