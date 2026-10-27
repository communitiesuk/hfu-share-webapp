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

TAG_TEMPLATES_DIR = "webapp/components/tag"
TAG_TEMPLATE_PATH = f"{TAG_TEMPLATES_DIR}/tag.html"


@register.simple_tag
def render_govuk_tag(text: str, *, colour: Optional[str] = None, css_class: str = ""):
    return render_to_string(
        TAG_TEMPLATE_PATH,
        {
            "tag": TagBuilder(
                text,
                colour=colour,
                css_class=css_class,
            )
        },
    )


def _render_boolean_govuk_tag(
    status: str | bool, colour: Optional[str] = None, css_class: str = ""
):
    return render_govuk_tag(
        "Yes" if status else "No",
        colour=colour,
        css_class=css_class,
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
        colour=visa_status_to_tag_colour(visa_status),
        css_class="app-tag--nowrap",
    )


@register.filter
def render_app_vir_status_tag(vir_status: str):
    return render_govuk_tag(
        cast(str, VisaInformationRequest.RequestStatus(vir_status).label),
        colour=vir_status_to_tag_colour(vir_status),
        css_class="app-tag--nowrap",
    )


@register.filter
def render_app_access_request_status_tag(status: AccessRequest.Status):
    return render_govuk_tag(
        cast(str, status.label),
        colour=access_request_status_to_tag_colour(status),
        css_class="app-tag--nowrap",
    )


@register.filter
def render_app_accommodation_request_status_tag(status: str):
    return render_govuk_tag(
        status,
        colour=accommodation_request_status_label_to_tag_colour(status),
        css_class="app-tag--nowrap",
    )


@register.filter
def render_app_adverse_rematch_status_tag(status: str):
    return _render_boolean_govuk_tag(
        status,
        colour=adverse_rematch_status_to_tag_colour(status),
        css_class="app-tag--nowrap",
    )


@register.filter
def render_app_alerted_status_tag(status: str):
    return render_govuk_tag(
        status,
        colour=alerted_status_to_tag_colour(status),
        css_class="app-tag--nowrap",
    )


@register.filter
def render_app_will_notify_la_central_case_flag_tag(status: str):
    return _render_boolean_govuk_tag(
        status,
        colour=will_notify_la_central_case_flag_to_tag_colour(status),
        css_class="app-tag--nowrap",
    )


@register.filter
def render_app_accommodation_checks_status_tag(status: str):
    return render_govuk_tag(
        status,
        colour=accommodation_checks_status_label_to_tag_colour(status),
        css_class="app-tag--nowrap",
    )


@register.filter
def render_app_is_principal_tag(status: str):
    return _render_boolean_govuk_tag(
        status,
        colour=is_principal_to_tag_colour(status),
        css_class="app-tag--nowrap",
    )


@register.filter
def render_app_is_uam_tag(status: str):
    return _render_boolean_govuk_tag(
        status,
        colour=is_uam_to_tag_colour(status),
        css_class="app-tag--nowrap",
    )


@register.filter
def render_app_reassignment_request_outcome_tag(outcome: ReassignmentRequest.Outcome):
    return render_govuk_tag(
        outcome,
        colour=reassignment_request_outcome_to_tag_colour(outcome),
        css_class="app-tag--nowrap",
    )


@register.filter
def render_app_value_with_tag(value: str, below: bool):
    return render_govuk_tag(
        value,
        colour="green",
        css_class=f"govuk-!-margin-{'top' if below else 'left'}-1 app-tag--nowrap",
    )


@register.filter
def render_app_safeguarding_check_status_tag(status: DevCheckV2.CheckStatus):
    return render_govuk_tag(
        safeguarding_check_status_to_tag_text(status),
        colour=safeguarding_check_status_to_tag_colour(status),
        css_class="govuk-!-margin-bottom-1 app-tag--nowrap",
    )


@register.filter
def render_app_safeguarding_status_tag(status: str):
    return render_govuk_tag(
        status,
        colour=accommodation_safeguarding_status_label_to_tag_colour(status),
        css_class="app-tag--nowrap",
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
        colour=colour,
    )
