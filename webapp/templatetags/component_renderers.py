from typing import Optional, Tuple

from django.template.loader import render_to_string
from django.utils.safestring import SafeString, mark_safe

TYPOGRAPHY_TEMPLATES_DIR = "webapp/components/typography"
CONCATENATED_TEXT_TEMPLATE_PATH = f"{TYPOGRAPHY_TEMPLATES_DIR}/concatenated_text.html"


def render_app_concatenated_text(
    *items: Tuple[str | SafeString, ...],
    separator: str = " ",
    wrapper_class: Optional[str] = None,
):
    return render_to_string(
        CONCATENATED_TEXT_TEMPLATE_PATH,
        {
            "items": items,
            "separator": mark_safe(separator),
            "wrapper_class": wrapper_class,
        },
    )
