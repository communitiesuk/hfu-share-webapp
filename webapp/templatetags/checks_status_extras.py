from django import template

from ontology.models import MvAccommodationRequest
from webapp.constants import (
    ACCOMMODATION_REQUEST_CHECKS_NO_STATUS_TAG_COLOUR,
    ACCOMMODATION_REQUEST_NO_STATUS_TAG_COLOUR,
    ACCOMMODATION_REQUEST_SAFEGUARDING_NO_STATUS_TAG_COLOUR,
    accommodation_request_checks_status_tag_colours,
    accommodation_request_safeguarding_status_tag_colours,
    accommodation_request_status_tag_colours,
)

register = template.Library()

LABEL_TO_CHECKS_STATUS = {
    label.lower(): MvAccommodationRequest.ChecksStatus(value)
    for value, label in MvAccommodationRequest.ChecksStatus.choices
}


@register.filter
def accommodation_checks_status_label_to_tag_colour(value: str) -> str:
    status = LABEL_TO_CHECKS_STATUS.get(value.lower())
    if status:
        return accommodation_request_checks_status_tag_colours.get(
            status, ACCOMMODATION_REQUEST_CHECKS_NO_STATUS_TAG_COLOUR
        )
    return ACCOMMODATION_REQUEST_CHECKS_NO_STATUS_TAG_COLOUR


LABEL_TO_STATUS = {
    label.lower(): MvAccommodationRequest.Status(value)
    for value, label in MvAccommodationRequest.Status.choices
}


@register.filter
def accommodation_request_status_label_to_tag_colour(value: str) -> str:
    status = LABEL_TO_STATUS.get(value.lower())
    if status:
        return accommodation_request_status_tag_colours.get(
            status, ACCOMMODATION_REQUEST_NO_STATUS_TAG_COLOUR
        )
    return ACCOMMODATION_REQUEST_NO_STATUS_TAG_COLOUR


LABEL_TO_SAFEGUARDING_STATUS = {
    label.lower(): MvAccommodationRequest.SafeguardingStatus(value)
    for value, label in MvAccommodationRequest.SafeguardingStatus.choices
}


@register.filter
def accommodation_safeguarding_status_label_to_tag_colour(value: str) -> str:
    status = LABEL_TO_SAFEGUARDING_STATUS.get(value.lower())
    if status:
        return accommodation_request_safeguarding_status_tag_colours.get(
            status, ACCOMMODATION_REQUEST_SAFEGUARDING_NO_STATUS_TAG_COLOUR
        )
    return ACCOMMODATION_REQUEST_SAFEGUARDING_NO_STATUS_TAG_COLOUR
