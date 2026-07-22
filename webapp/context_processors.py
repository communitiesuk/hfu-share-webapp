from django.conf import settings

from accounts.enums import GroupType
from webapp.constants import (
    ACCOMMODATION_ALLOWED_GROUP_TYPES,
    ACCOMMODATION_REQUEST_ALLOWED_GROUP_TYPES,
    DEDUPE_RECORDS_ALLOWED_GROUP_TYPES,
    DOWNLOAD_DATA_ALLOWED_GROUP_TYPES,
    ESCALATED_CHECKS_ALLOWED_GROUP_TYPES,
    FIX_DUPLICATE_RECORDS_ALLOWED_GROUP_TYPES,
    GUESTS_ALLOWED_GROUP_TYPES,
    MANAGE_PERMISSIONS_ALLOWED_GROUP_TYPES,
    REASSIGNMENT_REQUEST_ALLOWED_GROUP_TYPES,
    SPONSORS_HOSTS_ALLOWED_GROUP_TYPES,
    UAM_ALLOWED_GROUP_TYPES,
    VISA_APPLICATIONS_ALLOWED_GROUP_TYPES,
    VISA_INFORMATION_REQUESTS_ALLOWED_GROUP_TYPES,
)


def available_links(request):
    return {"available_links": get_available_links(request)}


def get_available_links(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}

    # memoised on the request so repeated renders only query groups once
    if not hasattr(request, "_available_links"):
        request._available_links = _compute_available_links(user)
    return request._available_links


def _compute_available_links(user) -> dict:
    user_group_types = set(user.groups.values_list("groupinfo__group_type", flat=True))

    links = {
        "accommodation": bool(user_group_types & ACCOMMODATION_ALLOWED_GROUP_TYPES),
        "accommodation_requests": bool(
            user_group_types & ACCOMMODATION_REQUEST_ALLOWED_GROUP_TYPES
        ),
        "dedupe_records": bool(user_group_types & DEDUPE_RECORDS_ALLOWED_GROUP_TYPES),
        "download_data": bool(user_group_types & DOWNLOAD_DATA_ALLOWED_GROUP_TYPES),
        "escalated_checks": bool(
            user_group_types & ESCALATED_CHECKS_ALLOWED_GROUP_TYPES
        ),
        "guests": bool(user_group_types & GUESTS_ALLOWED_GROUP_TYPES),
        "manage_permissions": bool(
            user_group_types & MANAGE_PERMISSIONS_ALLOWED_GROUP_TYPES
        ),
        "sponsors_hosts": bool(user_group_types & SPONSORS_HOSTS_ALLOWED_GROUP_TYPES),
        "visa_applications": bool(
            user_group_types & VISA_APPLICATIONS_ALLOWED_GROUP_TYPES
        ),
        "reassignment_requests": bool(
            user_group_types & REASSIGNMENT_REQUEST_ALLOWED_GROUP_TYPES
        ),
        "visa_information_requests": bool(
            user_group_types & VISA_INFORMATION_REQUESTS_ALLOWED_GROUP_TYPES
        ),
        "uam": bool(user_group_types & UAM_ALLOWED_GROUP_TYPES),
        "fix_duplicate_records": bool(user_group_types & {GroupType.DEV})
        or (
            settings.FIX_DUPLICATE_RECORDS_ENABLED
            and bool(user_group_types & FIX_DUPLICATE_RECORDS_ALLOWED_GROUP_TYPES)
        ),
    }

    if not any(links.values()):
        return {}

    return links
