from django import template

from webapp.constants import alerted_status_tag_colours

register = template.Library()


@register.filter
def alerted_status_to_tag_colour(value):
    return alerted_status_tag_colours.get(value, "grey")
