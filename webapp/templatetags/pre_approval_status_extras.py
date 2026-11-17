from django import template

from ontology.models import SponsorshipCertificationForm
from webapp.constants import (
    la_pre_approval_check_status_to_text,
    pre_approval_check_code_sent_status_tag_colours,
    pre_approval_check_status_tag_colours,
    pre_approval_status_tag_colours,
    ukvi_pre_approval_check_status_to_text,
)

register = template.Library()


@register.filter
def pre_approval_status_to_tag_colour(value: str) -> str:
    return pre_approval_status_tag_colours[
        SponsorshipCertificationForm.PreApprovalStatus(value)
    ]


@register.filter
def pre_approval_check_status_to_tag_colour(value: str) -> str:
    return pre_approval_check_status_tag_colours[
        SponsorshipCertificationForm.PreApprovalCheckStatus(value)
    ]


def ukvi_pre_approval_check_status_to_tag_text(value: str) -> str:
    return ukvi_pre_approval_check_status_to_text[
        SponsorshipCertificationForm.PreApprovalCheckStatus(value)
    ]


def la_pre_approval_check_status_to_tag_text(value: str) -> str:
    return la_pre_approval_check_status_to_text[
        SponsorshipCertificationForm.PreApprovalCheckStatus(value)
    ]


@register.filter
def pre_approval_checkcode_sent_status_to_tag_colour(value: str) -> str:
    return pre_approval_check_code_sent_status_tag_colours[
        SponsorshipCertificationForm.PreApprovalCheckCodeSentStatus(value)
    ]
