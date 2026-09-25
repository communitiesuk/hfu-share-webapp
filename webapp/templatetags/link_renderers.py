from typing import Optional

from django import template
from django.middleware.csrf import get_token
from django.template.loader import render_to_string

from webapp.component_builders import AdminLinkBuilder, LinkBuilder

register = template.Library()

LINK_TEMPLATES_DIR = "webapp/components/links"
LINK_TEMPLATE_PATH = f"{LINK_TEMPLATES_DIR}/link.html"


@register.simple_tag
def render_govuk_link(
    text: str,
    href: str,
    *,
    css_class: str = "",
    visually_hidden_text: Optional[str] = None,
    no_visited_state: bool = False,
    opens_in_new_tab: bool = False,
    **kwargs,
):
    return render_to_string(
        LINK_TEMPLATE_PATH,
        {
            "link": LinkBuilder(
                text,
                href,
                css_class=css_class,
                visually_hidden_text=visually_hidden_text,
                no_visited_state=no_visited_state,
                opens_in_new_tab=opens_in_new_tab,
                **kwargs,
            ),
        },
    )


def render_app_admin_link(
    text: str,
    href: str,
    *,
    opens_in_new_tab: bool = False,
    **kwargs,
):
    return render_to_string(
        f"{LINK_TEMPLATES_DIR}/admin_link.html",
        {
            "link": AdminLinkBuilder(
                text,
                href,
                opens_in_new_tab=opens_in_new_tab,
                **kwargs,
            ),
        },
    )


def render_app_record_link(record, value, record_href):
    return render_to_string(
        f"{LINK_TEMPLATES_DIR}/record_link.html",
        {
            "link_text": value,
            "link_href": record_href,
            "is_duplicate": not record.is_principal,
        },
    )


def render_app_form_link(
    request, name, value, record_name, *hidden_inputs, action=None, text="Select"
):
    return render_to_string(
        f"{LINK_TEMPLATES_DIR}/form_link.html",
        {
            "csrf_token": get_token(request),
            "form_action": action,
            "form_name": name,
            "form_value": value,
            "record_name": f" {record_name}",
            "hidden_inputs": hidden_inputs,
            "text": text,
        },
    )
