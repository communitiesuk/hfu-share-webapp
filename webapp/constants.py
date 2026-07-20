from dataclasses import dataclass

from django.contrib import messages

from accounts.enums import GroupType
from accounts.models import AccessRequest
from ontology.models import (
    DevCheckV2,
    MvAccommodationRequest,
    ReassignmentRequest,
    SafeguardingReferral,
)
from webapp.templatetags.timeline_extras import AuditEventType

# GOV.UK tag colours constants
GREY = "grey"
GREEN = "green"
TURQUOISE = "turquoise"
BLUE = "blue"
PURPLE = "purple"
PINK = "pink"
RED = "red"
ORANGE = "orange"
YELLOW = "yellow"


# Visa Status
@dataclass
class VisaStatus:
    id: int
    name: str | None
    tag_colour: str  # one of the .govuk-tag--* colours
    sort_order: int


visa_status_list = [
    VisaStatus(1, "Arrived", GREEN, 5),
    VisaStatus(2, "Issued", TURQUOISE, 4),
    VisaStatus(3, "Confirmed", BLUE, 3),
    VisaStatus(4, "Flow Visa Pending", PURPLE, 9),  # specific to UAMs
    VisaStatus(5, "Pending", YELLOW, 2),
    VisaStatus(6, "Refused", RED, 7),
    VisaStatus(7, "Withdrawn", GREY, 6),
    VisaStatus(8, "Lapsed", ORANGE, 8),  # expired in Home Office system after ~241 days
    VisaStatus(9, "Missing Application", PINK, 1),
]
no_visa_status = VisaStatus(10, None, GREY, 10)
visa_status_some_issued = VisaStatus(2, "Some issued", TURQUOISE, 11)
visa_status_by_name = {value.name: value for value in visa_status_list}
visa_status_list_ordered = sorted(visa_status_list, key=lambda x: x.sort_order)


# VIR Status
@dataclass
class VIRStatus:
    id: int
    name: str | None
    tag_colour: str  # one of the .govuk-tag--* colours
    sort_order: int


vir_status_list = [
    VIRStatus(1, "Awaiting UKVI", ORANGE, 1),
    VIRStatus(2, "Awaiting LA", PURPLE, 2),
    VIRStatus(3, "Closed", GREEN, 3),
]
no_vir_status = VIRStatus(10, None, GREY, 10)
vir_status_by_name = {value.name: value for value in vir_status_list}
vir_status_list_ordered = sorted(vir_status_list, key=lambda x: x.sort_order)

ACCOMMODATION_REQUEST_CHECKS_NO_STATUS_TAG_COLOUR = GREY
accommodation_request_checks_status_tag_colours = {
    MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED: YELLOW,
    MvAccommodationRequest.ChecksStatus.PRE_ARRIVAL_CHECKS_COMPLETE: PINK,
    MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED: GREEN,
    MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED: BLUE,
    MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED: RED,
    MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE: ORANGE,
    MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME: ORANGE,
    MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY: ORANGE,
    MvAccommodationRequest.ChecksStatus.REMATCH_REQUIRED: YELLOW,
    MvAccommodationRequest.ChecksStatus.IN_TEMPORARY_ACCOMMODATION: GREY,
    MvAccommodationRequest.ChecksStatus.CANCELLED: GREY,
}

ACCOMMODATION_REQUEST_NO_STATUS_TAG_COLOUR = GREY
accommodation_request_status_tag_colours = {
    MvAccommodationRequest.Status.ACCOMMODATION_ASSIGNED: GREEN,
    MvAccommodationRequest.Status.MISSING_ACCOMMODATION: ORANGE,
    MvAccommodationRequest.Status.ARRIVAL_CONFIRMED: YELLOW,
}

access_request_status_tag_colours = {
    AccessRequest.Status.PENDING: BLUE,
    AccessRequest.Status.APPROVED: GREEN,
    AccessRequest.Status.REJECTED: RED,
}

reassignment_request_outcome_tag_colours = {
    ReassignmentRequest.Outcome.PENDING: YELLOW,
    ReassignmentRequest.Outcome.ACCEPTED: GREEN,
    ReassignmentRequest.Outcome.REJECTED: RED,
    ReassignmentRequest.Outcome.NEEDS_ACCOMMODATION_REQUEST: GREY,
}

safeguarding_check_status_tag_colours = {
    DevCheckV2.CheckStatus.NOT_STARTED: GREY,
    DevCheckV2.CheckStatus.IN_PROGRESS: BLUE,
    DevCheckV2.CheckStatus.NO_LONGER_NEEDED: GREY,
    DevCheckV2.CheckStatus.PASSED: GREEN,
    DevCheckV2.CheckStatus.FAILED: RED,
    DevCheckV2.CheckStatus.UNAVAILABLE: GREY,
}

safeguarding_check_status_tag_label_text = {
    DevCheckV2.CheckStatus.NOT_STARTED: "Checks not started",
    DevCheckV2.CheckStatus.IN_PROGRESS: "Checks in progress",
    DevCheckV2.CheckStatus.NO_LONGER_NEEDED: "Checks complete: No longer needed",
    DevCheckV2.CheckStatus.PASSED: "Checks complete: Passed",
    DevCheckV2.CheckStatus.FAILED: "Checks complete: Failed",
    DevCheckV2.CheckStatus.UNAVAILABLE: "Check status unavailable",
}

ACCOMMODATION_REQUEST_SAFEGUARDING_NO_STATUS_TAG_COLOUR = GREY
accommodation_request_safeguarding_status_tag_colours = {
    MvAccommodationRequest.SafeguardingStatus.NO_NOTIFICATIONS: GREY,
    MvAccommodationRequest.SafeguardingStatus.NO_OPEN_NOTIFICATIONS: GREY,
    MvAccommodationRequest.SafeguardingStatus.ACTIVE_NOTIFICATIONS: YELLOW,
    MvAccommodationRequest.SafeguardingStatus.UNASSIGNED_NOTIFICATIONS: RED,
}

accommodation_request_adverse_rematch_status_tag_colours = {
    True: RED,
    False: GREEN,
}

accommodation_request_central_case_flag_tag_colours = {
    True: GREEN,
    False: RED,
}

accommodation_request_is_uam_tag_colours = {
    True: GREEN,
    False: YELLOW,
}

accommodation_request_is_principal_tag_colours = {
    True: GREEN,
    False: RED,
}

accommodation_request_linked_adverse_hit_tag_colours = {
    True: RED,
    False: GREEN,
}

accommodation_request_will_notify_la_central_case_flag_tag_colours = {
    True: GREEN,
    False: RED,
}

alerted_status_tag_colours = {
    SafeguardingReferral.AlertedStatus.ALERTED: RED,
    SafeguardingReferral.AlertedStatus.NOT_ALERTED: GREY,
    SafeguardingReferral.AlertedStatus.SOME_ALERTED: TURQUOISE,
}


def status_to_tag_colour(status_type: str, value: str) -> str | None:
    match status_type:
        case "visa_status":
            return (visa_status_by_name.get(value) or no_visa_status).tag_colour
        case "accommodation_checks_status":
            return (
                accommodation_request_checks_status_tag_colours[value]
                if isinstance(value, MvAccommodationRequest.ChecksStatus)
                else ACCOMMODATION_REQUEST_CHECKS_NO_STATUS_TAG_COLOUR
            )
        case "accommodation_request_status":
            return (
                accommodation_request_status_tag_colours[value]
                if isinstance(value, MvAccommodationRequest.Status)
                else ACCOMMODATION_REQUEST_NO_STATUS_TAG_COLOUR
            )
        case "sponsor_withdrawn":
            return RED
        case _:
            return None


message_level_to_notification_banner_variant_override = {
    messages.SUCCESS: "success"
}  # Regular variant by default
message_level_to_notification_banner_title_override = {
    messages.SUCCESS: "Success"
}  # "Important" by default

# Search
WHOLE_STRING_ONLY_SEARCH_FIELDS = [
    # used for VisaApplications
    "application_unique_application_number",
    "gwf",
    # used for Guests
    "application_number",
    "passport_id",
    # used for VIRs
    "visa_application__application_unique_application_number",
    "visa_application__gwf",
    # used for EscalatedChecks
    "person__application_number",
    "person__gwf",
    # used for UAMs
    "reference",
    "identification_number",
]

VISA_APPLICATION_SEARCH_FIELDS: list[str] = [
    "title",
    "Q97c_sponsor_name",
    "ltla_name",
    "gwf",
    "application_unique_application_number",
]

VIR_SEARCH_FIELDS: list[str] = [
    "visa_application__title",
    "visa_application__gwf",
    "visa_application__application_unique_application_number",
]

GUEST_SEARCH_FIELDS: list[str] = [
    "full_name",
    "first_name",
    "last_name",
    "passport_id",
    "email",
    "application_number",
]

REASSIGNMENT_REQUEST_SEARCH_FIELDS: list[str] = [
    "guest_full_names",
]

ACCOMMODATION_REQUEST_SEARCH_FIELDS: list[str] = ["title"]

ACCOMMODATION_SEARCH_FIELDS: list[str] = [
    "full_address",
    "postcode__postcode",
    "postcode__postcode_formatted",
    "postcode__title",
]

SPONSORS_SEARCH_FIELDS: list[str] = [
    "first_name",
    "last_name",
    "full_name",
    "email",
    "phone_number",
]

ACCESS_REQUEST_SEARCH_FIELDS: list[str] = [
    "requester__first_name",
    "requester__last_name",
    "requester__email",
]

USERS_SEARCH_FIELDS: list[str] = [
    "first_name",
    "last_name",
    "email",
]

GROUP_SEARCH_FIELDS: list[str] = [
    "name",
    "groupinfo__description",
]

ESCALATED_CHECKS_SEARCH_FIELDS: list[str] = [
    "person_full_name",
    "person__first_name",
    "person__last_name",
    "person__passport_id",
    "person__gwf",
    "person__application_number",
]

UAMS_SEARCH_FIELDS: list[str] = [
    "sponsor_full_name",
    "identification_number",
    "ltla_name",
    "reference",
]

ACCESS_REQUEST_TABLE_COLUMN_ATTRS = {"td": {"style": "width: 25%;"}}

SELECT_ACCOMMODATION_TABLE_COLUMN_ATTRS = {"td": {"style": "width: 45%;"}}

ACCOMMODATION_ALLOWED_GROUP_TYPES = {
    GroupType.LOCAL_AUTHORITY,
    GroupType.DEVOLVED_ADMINISTRATION,
    GroupType.MHCLG,
    GroupType.DEV,
    GroupType.SERVICE_SUPPORT,
    GroupType.HOME_OFFICE,
}

ACCOMMODATION_REQUEST_ALLOWED_GROUP_TYPES = {
    GroupType.LOCAL_AUTHORITY,
    GroupType.DEVOLVED_ADMINISTRATION,
    GroupType.MHCLG,
    GroupType.DEV,
    GroupType.SERVICE_SUPPORT,
    GroupType.HOME_OFFICE,
}

# Hiding the dedup tile for now
DEDUPE_RECORDS_ALLOWED_GROUP_TYPES = {None}

DOWNLOAD_DATA_ALLOWED_GROUP_TYPES = {
    GroupType.LOCAL_AUTHORITY,
    GroupType.DEVOLVED_ADMINISTRATION,
    GroupType.DEV,
    GroupType.SERVICE_SUPPORT,
    GroupType.MHCLG,
    GroupType.HOME_OFFICE,
}

ESCALATED_CHECKS_ALLOWED_GROUP_TYPES = {
    GroupType.MHCLG,
    GroupType.DEV,
    GroupType.HOME_OFFICE,
}

GUESTS_ALLOWED_GROUP_TYPES = {
    GroupType.LOCAL_AUTHORITY,
    GroupType.DEVOLVED_ADMINISTRATION,
    GroupType.MHCLG,
    GroupType.DEV,
    GroupType.SERVICE_SUPPORT,
    GroupType.HOME_OFFICE,
}

MANAGE_PERMISSIONS_ALLOWED_GROUP_TYPES = {
    GroupType.DEV,
}

SPONSORS_HOSTS_ALLOWED_GROUP_TYPES = {
    GroupType.LOCAL_AUTHORITY,
    GroupType.DEVOLVED_ADMINISTRATION,
    GroupType.MHCLG,
    GroupType.DEV,
    GroupType.SERVICE_SUPPORT,
    GroupType.HOME_OFFICE,
}

VISA_APPLICATIONS_ALLOWED_GROUP_TYPES = {
    GroupType.LOCAL_AUTHORITY,
    GroupType.DEVOLVED_ADMINISTRATION,
    GroupType.MHCLG,
    GroupType.DEV,
    GroupType.SERVICE_SUPPORT,
    GroupType.HOME_OFFICE,
}

REASSIGNMENT_REQUEST_ALLOWED_GROUP_TYPES = {
    GroupType.LOCAL_AUTHORITY,
    GroupType.DEVOLVED_ADMINISTRATION,
    GroupType.MHCLG,
    GroupType.DEV,
    GroupType.SERVICE_SUPPORT,
}

VISA_INFORMATION_REQUESTS_ALLOWED_GROUP_TYPES = {
    GroupType.LOCAL_AUTHORITY,
    GroupType.DEVOLVED_ADMINISTRATION,
    GroupType.HOME_OFFICE,
    GroupType.MHCLG,
    GroupType.DEV,
    GroupType.SERVICE_SUPPORT,
}

UAM_ALLOWED_GROUP_TYPES = {
    GroupType.DEV,
    GroupType.LOCAL_AUTHORITY,
    GroupType.MHCLG,
    GroupType.HOME_OFFICE,
}

FIX_DUPLICATE_RECORDS_ALLOWED_GROUP_TYPES = {
    GroupType.LOCAL_AUTHORITY,
    GroupType.DEVOLVED_ADMINISTRATION,
    GroupType.MHCLG,
    GroupType.DEV,
    GroupType.SERVICE_SUPPORT,
    GroupType.LOCAL_AUTHORITY_EARLY_ADOPTERS,
}

AUDIT_EVENT_TYPE_ACTION = {
    AuditEventType.ADDED: "added",
    AuditEventType.CHANGED: "changed",
    AuditEventType.DELETED: "deleted",
    AuditEventType.UNCHANGED: "unchanged",
}

INACTIVE_ACCOUNT_WARNING_DAYS = 60
INACTIVE_ACCOUNT_SUSPEND_DAYS = 90
