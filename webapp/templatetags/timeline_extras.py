import re
from enum import Enum
from typing import Optional

from django import template
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

from webapp.templatetags.list_renderers import render_govuk_list

TIMELINE_TEMPLATES_DIR = "webapp/components/timeline"
TIMELINE_ITEM_TEMPLATE_PATH = f"{TIMELINE_TEMPLATES_DIR}/timeline_change_item.html"


register = template.Library()


class TimelineEventType(Enum):
    INTERACTION = "Interaction"
    COMMENT = "Comment"
    LOG_ENTRY = "Log Entry"


class AuditEventType(Enum):
    ADDED = "Added"
    CHANGED = "Changed"
    DELETED = "Deleted"
    UNCHANGED = "Unchanged"


@register.simple_tag
def timeline_event_is_interaction(event_type):
    return event_type == TimelineEventType.INTERACTION


@register.simple_tag
def timeline_event_is_comment(event_type):
    return event_type == TimelineEventType.COMMENT


@register.simple_tag
def timeline_event_is_log_entry(event_type):
    return event_type == TimelineEventType.LOG_ENTRY


@register.simple_tag
def timeline_event_has_attached_file(event):
    from webapp.mixins import TimelineItem

    return isinstance(event, TimelineItem) and event.attached_file is not None


@register.inclusion_tag("webapp/components/timeline/timeline_list.html")
def timeline(request, events, event_type, events_with_files=None):
    return {
        "events": events,
        "request": request,
        "events_with_files": events_with_files or [],
        "event_type": event_type,
    }


@register.filter
def format_interaction_content(text):
    # first strips out any html injected into the string
    # then looks for a list of names e.g.
    # person1 and person2
    # person1, person2 and person3
    # up to any number of people
    # converts to a html unordered list

    sanitised_text = strip_tags(text)
    without_reason = sanitised_text.split("Reason", 1)[0]

    pattern = (
        r"\[names_list\]((?=[\w'’\- ]+(?:,| and ))[\w'’\- ]+(?:, [\w'’\- ]+)*(?: and "
        r"[\w'’\- ](.?)+)?)\[names_list_end\]"
    )

    match = re.search(pattern, without_reason)

    sanitised_text = sanitised_text.replace("[names_list]", "")
    sanitised_text = sanitised_text.replace("[names_list_end]", "")

    if not match:
        return sanitised_text

    chunk = match.group(1)

    names = chunk.rstrip(".").replace(" and ", ", ").split(", ")

    html = render_govuk_list(names, bulleted_list=True)

    result = sanitised_text.replace(chunk, html, 1)
    return mark_safe(result)  # noqa:S308


def render_app_timeline_change_item(
    field_name: str,
    audit_event_type_action: str,
    *,
    old: Optional[str] = None,
    new: Optional[str] = None,
):
    changes = []

    if old:
        changes.append(f"was {old}")

    if new:
        changes.append(f"now {new}")

    return render_to_string(
        TIMELINE_ITEM_TEMPLATE_PATH,
        {
            "field_name": field_name,
            "audit_event_type_action": audit_event_type_action,
            "changes": changes,
        },
    )
