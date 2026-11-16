from django import template

from ontology.models import SponsorshipCertificationForm
from webapp.constants import pre_approval_status_tag_colours

register = template.Library()


@register.filter
def pre_approval_status_to_tag_colour(value: str) -> str:
    return pre_approval_status_tag_colours[
        SponsorshipCertificationForm.PreApprovalStatus(value)
    ]
