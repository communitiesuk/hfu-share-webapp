from typing import Any

from django.template.loader import render_to_string


def render_app_hidden_input(name: str, value: Any):
    return render_to_string(
        "webapp/components/fields/hidden_input.html",
        {
            "name": name,
            "value": value,
        },
    )
