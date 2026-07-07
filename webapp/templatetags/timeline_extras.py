import re
from enum import Enum

from django import template
from django.utils.html import format_html, strip_tags

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

    html = (
        "<ul class='govuk-list govuk-list--bullet'>"
        + "".join(f"<li>{name}</li>" for name in names)
        + "</ul>"
    )

    result = sanitised_text.replace(chunk, html, 1)
    return format_html(result)
