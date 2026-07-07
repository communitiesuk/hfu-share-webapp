from django import template

from webapp.constants import (
    message_level_to_notification_banner_title_override,
    message_level_to_notification_banner_variant_override,
)

register = template.Library()


@register.filter
def message_level_to_notification_banner_variant(value: int | None) -> str | None:
    if value in message_level_to_notification_banner_variant_override:
        return message_level_to_notification_banner_variant_override[value]
    return None


@register.filter
def message_level_to_notification_banner_title(value: int | None) -> str:
    if value in message_level_to_notification_banner_title_override:
        return message_level_to_notification_banner_title_override[value]
    return "Important"
