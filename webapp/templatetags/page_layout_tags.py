from django import template
from django.template.loader import render_to_string

register = template.Library()

GRID_ROW_TEMPLATE_PATH = "webapp/components/grid_row/grid_row.html"


@register.simple_block_tag
def grid_row(content, column="full"):
    if not content.strip():
        return ""
    return render_to_string(
        GRID_ROW_TEMPLATE_PATH, {"content": content, "column": column}
    )
