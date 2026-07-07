from django import template

from ontology.models import DevCheckV2
from ontology.models.DevCheckV2 import validate_safeguarding_status
from webapp.constants import (
    GREY,
    safeguarding_check_status_tag_colours,
    safeguarding_check_status_tag_label_text,
)

register = template.Library()

LABEL_TO_SAFEGUARDING_CHECK_STATUS = {
    label: DevCheckV2.CheckStatus(value)
    for value, label in DevCheckV2.CheckStatus.choices
}


@register.filter
def safeguarding_check_status_to_tag_colour(value: DevCheckV2.CheckStatus) -> str:
    safeguarding_status_value = validate_safeguarding_status(value)
    return safeguarding_check_status_tag_colours.get(safeguarding_status_value, GREY)


@register.filter
def safeguarding_check_status_to_tag_text(value: DevCheckV2.CheckStatus) -> str:
    safeguarding_status_value = validate_safeguarding_status(value)
    return safeguarding_check_status_tag_label_text.get(
        safeguarding_status_value, "Not available"
    )


@register.filter
def safeguarding_check_status_is_not_started(value: DevCheckV2.CheckStatus) -> bool:
    return value == DevCheckV2.CheckStatus.NOT_STARTED
