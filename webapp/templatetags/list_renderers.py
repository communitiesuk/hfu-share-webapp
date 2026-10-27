from typing import List

from django.template.loader import render_to_string

from webapp.component_builders import ListBuilder

LIST_TEMPLATES_DIR = "webapp/components/lists"
LIST_TEMPLATE_PATH = f"{LIST_TEMPLATES_DIR}/list.html"


def render_govuk_list(
    items: List[str],
    *,
    bulleted_list: bool = False,
    css_class: str = "",
    item_class: str = "",
):
    return render_to_string(
        LIST_TEMPLATE_PATH,
        {
            "list": ListBuilder(
                items,
                bulleted_list=bulleted_list,
                css_class=css_class,
                item_class=item_class,
            )
        },
    )
