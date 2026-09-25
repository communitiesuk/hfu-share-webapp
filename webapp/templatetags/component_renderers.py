from django import template
from django.template.loader import render_to_string

register = template.Library()


@register.filter
def render_app_concatenated_text(*items):
    return render_to_string(
        "webapp/components/typography/concatenated_text.html",
        {"items": items},
    )
