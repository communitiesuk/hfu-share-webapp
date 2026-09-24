from typing import Optional

from django.middleware.csrf import get_token
from django.template.loader import render_to_string

from visa_applications.templatetags.visa_application_extras import (
    visa_status_to_tag_colour,
)

from ..component_builders import TagBuilder, LinkBuilder


def render_govuk_link(
    text: str,
    href: str,
    css_class: str = "",
    no_visited_state: bool = False,
    opens_in_new_tab: bool = False,
):
    return render_to_string(
        "webapp/components/typography/link.html",
        {
            "link": LinkBuilder(
                text,
                href,
                css_class,
                no_visited_state,
                opens_in_new_tab,
            ),
        },
    )

def render_app_select_link(management_form, request, name, value, record_name):
    return render_to_string(
        "webapp/components/typography/select_link.html",
        {
            "management_form": management_form,
            "csrf_token": get_token(request),
            "form_name": name,
            "form_value": value,
            "record_name": record_name,
        },
    )


def render_app_record_link(record, value, record_href):
    return render_to_string(
        "webapp/components/typography/record_link.html",
        {
            "link": LinkBuilder(value, record_href),
            "is_duplicate": not record.is_principal,
        },
    )


def render_app_undo_deduplication_link(record_name, actions_tab_link):
    return render_to_string(
        "webapp/components/typography/undo_deduplication_link.html",
        {
            "link": LinkBuilder(f"actions tab for {record_name}.", actions_tab_link),
        },
    )

def render_govuk_tag(text: str, colour: Optional[str] = None, css_class: str = ""):
    return render_to_string(
        "webapp/components/tag/tag.html",
        {
            "tag": TagBuilder(
                text,
                colour,
                css_class,
            )
        },
    )


def render_app_visa_status_tag(visa_status: str):
    return render_to_string(
        "webapp/components/tag/tag.html",
        {
            "tag": TagBuilder(
                visa_status,
                visa_status_to_tag_colour(visa_status),
                'app-tag--nowrap',
            )
        },
    )


def render_app_concatenated_text(*items):
        return render_to_string(
        "webapp/components/typography/concatenated_text.html",
        {
            "items": items
        },
    )
