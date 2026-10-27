from enum import Enum
from typing import Optional

from django.template.loader import render_to_string
from django.utils.safestring import SafeString

TYPOGRAPHY_TEMPLATES_DIR = "webapp/components/typography"
CONCATENATED_TEXT_TEMPLATE_PATH = f"{TYPOGRAPHY_TEMPLATES_DIR}/concatenated_text.html"


class ConcatenatedTextSeparator(Enum):
    SPACE = " "
    COMMA_SPACE = ", "
    NEW_LINE = None


def render_app_concatenated_text(
    *items: str | SafeString,
    separator: ConcatenatedTextSeparator = ConcatenatedTextSeparator.SPACE,
    wrapper_class: Optional[str] = None,
):
    return render_to_string(
        CONCATENATED_TEXT_TEMPLATE_PATH,
        {
            "items": items,
            "separator": separator.value,
            "wrapper_class": wrapper_class,
            "multi_line": separator is ConcatenatedTextSeparator.NEW_LINE,
        },
    )
