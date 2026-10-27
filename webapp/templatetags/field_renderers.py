from typing import Any

from django.template.loader import render_to_string

FIELDS_TEMPLATES_DIR = "webapp/components/fields"
HIDDEN_INPUT_TEMPLATE_PATH = f"{FIELDS_TEMPLATES_DIR}/hidden_input.html"


def render_app_hidden_input(name: str, value: Any):
    return render_to_string(
        HIDDEN_INPUT_TEMPLATE_PATH,
        {
            "name": name,
            "value": value,
        },
    )
