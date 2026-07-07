from django import template
from django.contrib.auth.models import Group

from accounts.enums import GroupType
from accounts.models import AccessRequest, GroupInfo
from webapp.constants import access_request_status_tag_colours

register = template.Library()


@register.filter
def access_request_status_to_tag_colour(value: AccessRequest.Status) -> str:
    return access_request_status_tag_colours[value]


@register.filter
def access_request_status_label_to_tag_colour(value: str) -> str:
    for status in AccessRequest.Status.choices:
        if status[1] == value:
            return access_request_status_to_tag_colour(AccessRequest.Status(status[0]))
    return ""


@register.filter
def render_name_label_from_group_info(group: GroupInfo) -> str:
    match group.group_type:
        case GroupType.LOCAL_AUTHORITY:
            if group.is_utla:
                return f"{group.utla_name} (UTLA)"
            return f"{group.ltla_name} (LTLA)"
        case GroupType.DEVOLVED_ADMINISTRATION:
            return group.da_name
        case GroupType.HOME_OFFICE:
            return "Home Office"
        case GroupType.MHCLG:
            return "MHCLG"
        case GroupType.SERVICE_SUPPORT:
            return "Service support"
        case GroupType.DEV:
            return "Dev"
        case _:
            return group.group.name


@register.filter
def render_name_label_from_group(group: Group) -> str:
    group_info = GroupInfo.objects.get(group=group)
    return render_name_label_from_group_info(group_info)
