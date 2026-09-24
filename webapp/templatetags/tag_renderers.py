from typing import Optional, cast

from django import template
from django.template.loader import render_to_string

from accounts.models import AccessRequest
from case_management import settings
from ontology.models import (
    DevCheckV2,
    ReassignmentRequest,
    VisaInformationRequest,
)
from user_management.templatetags.access_request_extras import (
    access_request_status_to_tag_colour,
)
from visa_applications.templatetags.visa_application_extras import (
    vir_status_to_tag_colour,
    visa_status_to_tag_colour,
)
from webapp.component_builders import TagBuilder
from webapp.templatetags.alerted_status_extras import alerted_status_to_tag_colour
from webapp.templatetags.checks_status_extras import (
    accommodation_checks_status_label_to_tag_colour,
    accommodation_request_status_label_to_tag_colour,
    accommodation_safeguarding_status_label_to_tag_colour,
)
from webapp.templatetags.reassignment_request_extras import (
    reassignment_request_outcome_to_tag_colour,
)
from webapp.templatetags.safeguarding_checks_extras import (
    safeguarding_check_status_to_tag_colour,
    safeguarding_check_status_to_tag_text,
)
from webapp.templatetags.safeguarding_extras import (
    adverse_rematch_status_to_tag_colour,
    is_principal_to_tag_colour,
    is_uam_to_tag_colour,
    will_notify_la_central_case_flag_to_tag_colour,
)

register = template.Library()


@register.simple_tag
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


def _render_boolean_govuk_tag(
    status: str | bool, colour: Optional[str] = None, css_class: str = ""
):
    return render_govuk_tag(
        "Yes" if status else "No",
        colour,
        css_class,
    )


@register.simple_tag
def render_app_environment_tag():
    return render_govuk_tag(
        f"You are in the {settings.ENVIRONMENT} environment.",
        css_class="govuk-phase-banner__content__tag",
    )


@register.simple_tag
def render_app_phase_banner_tag():
    return render_govuk_tag(
        "Beta",
        css_class="govuk-phase-banner__content__tag",
    )


@register.filter
def render_app_visa_status_tag(visa_status: str):
    return render_govuk_tag(
        visa_status,
        visa_status_to_tag_colour(visa_status),
        "app-tag--nowrap",
    )


@register.filter
def render_app_vir_status_tag(vir_status: str):
    return render_govuk_tag(
        cast(str, VisaInformationRequest.RequestStatus(vir_status).label),
        vir_status_to_tag_colour(vir_status),
        "app-tag--nowrap",
    )


@register.filter
def render_app_access_request_status_tag(status: AccessRequest.Status):
    return render_govuk_tag(
        cast(str, status.label),
        access_request_status_to_tag_colour(status),
        "app-tag--nowrap",
    )


@register.filter
def render_app_accommodation_request_status_tag(status: str):
    return render_govuk_tag(
        status,
        accommodation_request_status_label_to_tag_colour(status),
        "app-tag--nowrap",
    )


@register.filter
def render_app_adverse_rematch_status_tag(status: str):
    return _render_boolean_govuk_tag(
        status,
        adverse_rematch_status_to_tag_colour(status),
        "app-tag--nowrap",
    )


@register.filter
def render_app_alerted_status_tag(status: str):
    return render_govuk_tag(
        status,
        alerted_status_to_tag_colour(status),
        "app-tag--nowrap",
    )


@register.filter
def render_app_will_notify_la_central_case_flag_tag(status: str):
    return _render_boolean_govuk_tag(
        status,
        will_notify_la_central_case_flag_to_tag_colour(status),
        "app-tag--nowrap",
    )


@register.filter
def render_app_accommodation_checks_status_tag(status: str):
    return render_govuk_tag(
        status,
        accommodation_checks_status_label_to_tag_colour(status),
        "app-tag--nowrap",
    )


@register.filter
def render_app_is_principal_tag(status: str):
    return _render_boolean_govuk_tag(
        status,
        is_principal_to_tag_colour(status),
        "app-tag--nowrap",
    )


@register.filter
def render_app_is_uam_tag(status: str):
    return _render_boolean_govuk_tag(
        status,
        is_uam_to_tag_colour(status),
        "app-tag--nowrap",
    )


@register.filter
def render_app_reassignment_request_outcome_tag(outcome: ReassignmentRequest.Outcome):
    return render_govuk_tag(
        outcome,
        reassignment_request_outcome_to_tag_colour(outcome),
        "app-tag--nowrap",
    )


@register.filter
def render_app_value_with_tag(value: str, below: bool):
    return render_govuk_tag(
        value,
        "green",
        f"govuk-!-margin-{'top' if below else 'left'}-1 app-tag--nowrap",
    )


@register.filter
def render_app_safeguarding_check_status_tag(status: DevCheckV2.CheckStatus):
    return render_govuk_tag(
        safeguarding_check_status_to_tag_text(status),
        safeguarding_check_status_to_tag_colour(status),
        "govuk-!-margin-bottom-1 app-tag--nowrap",
    )


@register.filter
def render_app_safeguarding_status_tag(status: str):
    return render_govuk_tag(
        status,
        accommodation_safeguarding_status_label_to_tag_colour(status),
        "app-tag--nowrap",
    )


@register.filter
def render_app_task_status_tag(status: str):
    match status:
        case "INCOMPLETE":
            colour = "yellow"
        case "URGENT":
            colour = "red"
        case _:
            colour = "green"

    return render_govuk_tag(
        status,
        colour,
    )
