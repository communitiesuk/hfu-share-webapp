from django import template
from django.utils.timezone import localtime

from ontology.models.VisaInformationRequest import VisaInformationRequest
from webapp.constants import (
    no_vir_status,
    no_visa_status,
    vir_status_by_name,
    visa_status_by_name,
)

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def visa_status_to_tag_colour(value: str | None) -> str:
    return visa_status_by_name.get(value, no_visa_status).tag_colour


@register.filter
def vir_status_to_tag_colour(value: str | None) -> str:
    return vir_status_by_name.get(value, no_vir_status).tag_colour


@register.filter
def get_checktype_label(value):
    try:
        return VisaInformationRequest.RequestedCheckType(value).label
    except (ValueError, AttributeError):
        return value


@register.filter
def get_requesttype_label(value):
    try:
        return VisaInformationRequest.RequestType(value).label
    except (ValueError, AttributeError):
        return value


@register.filter
def format_vir_datetime(value):
    if value:
        value = localtime(value)
        return (
            value.strftime("%d %b %Y at %-I:%M%p")
            .replace("AM", "am")
            .replace("PM", "pm")
        )
    return ""
