from django import template

from ontology.models import ReassignmentRequest
from webapp.constants import reassignment_request_outcome_tag_colours

register = template.Library()


@register.filter
def reassignment_request_outcome_to_tag_colour(
    value: ReassignmentRequest.Outcome,
) -> str:
    return reassignment_request_outcome_tag_colours[value]


@register.filter
def reassignment_request_outcome_label_to_tag_colour(value: str) -> str:
    for outcome in ReassignmentRequest.Outcome.choices:
        if outcome[1] == value:
            return reassignment_request_outcome_to_tag_colour(
                ReassignmentRequest.Outcome(outcome[0])
            )
    return "grey"
