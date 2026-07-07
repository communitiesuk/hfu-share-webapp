from django.conf import settings

from .page_title import get_title


def app_context(request):
    return {
        "SERVICE_NAME": settings.SERVICE_NAME,
        "TITLE": get_title(request, settings.SERVICE_NAME),
    }
