from django import template

from webapp.constants import (
    accommodation_request_adverse_rematch_status_tag_colours,
    accommodation_request_central_case_flag_tag_colours,
    accommodation_request_is_principal_tag_colours,
    accommodation_request_is_uam_tag_colours,
    accommodation_request_linked_adverse_hit_tag_colours,
    accommodation_request_will_notify_la_central_case_flag_tag_colours,
)

register = template.Library()


@register.filter
def adverse_rematch_status_to_tag_colour(value):
    return accommodation_request_adverse_rematch_status_tag_colours.get(value, "grey")


@register.filter
def central_case_flag_to_tag_colour(value):
    return accommodation_request_central_case_flag_tag_colours.get(value, "grey")


@register.filter
def is_uam_to_tag_colour(value):
    return accommodation_request_is_uam_tag_colours.get(value, "grey")


@register.filter
def is_principal_to_tag_colour(value):
    return accommodation_request_is_principal_tag_colours.get(value, "grey")


@register.filter
def linked_adverse_hit_to_tag_colour(value):
    return accommodation_request_linked_adverse_hit_tag_colours.get(value, "grey")


@register.filter
def will_notify_la_central_case_flag_to_tag_colour(value):
    return accommodation_request_will_notify_la_central_case_flag_tag_colours.get(
        value, "grey"
    )
