from django.template.loader import render_to_string

TYPOGRAPHY_TEMPLATES_DIR = "webapp/components/typography"


def render_app_concatenated_text(*items):
    return render_to_string(
        f"{TYPOGRAPHY_TEMPLATES_DIR}/concatenated_text.html",
        {"items": items},
    )


def render_app_concatenated_text_with_wrapper(*items, wrapper_class=None):
    return render_to_string(
        f"{TYPOGRAPHY_TEMPLATES_DIR}/concatenated_text_with_wrapper.html",
        {
            "items": items,
            "wrapper_class": wrapper_class,
        },
    )


def render_app_concatenated_text_multi_line(*items):
    return render_to_string(
        f"{TYPOGRAPHY_TEMPLATES_DIR}/concatenated_text_multi_line.html",
        {"items": items},
    )


def render_app_concatenated_text_list(*items):
    return render_to_string(
        f"{TYPOGRAPHY_TEMPLATES_DIR}/concatenated_text_list.html",
        {"items": items},
    )
