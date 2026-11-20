from django import template
from django.template.loader import render_to_string

register = template.Library()

NOTIFICATION_BANNER_CONTENT_TEMPLATES_DIR = "webapp/components/notification_banner"
NOTIFICATION_BANNER_CONTENT_TEMPLATE_PATH = (
    f"{NOTIFICATION_BANNER_CONTENT_TEMPLATES_DIR}/notification_banner_content.html"
)


@register.simple_tag
def render_govuk_notification_banner_content(
    heading: str,
    body: str,
):
    return render_to_string(
        NOTIFICATION_BANNER_CONTENT_TEMPLATE_PATH,
        {
            "heading": heading,
            "body": body,
        },
    )
