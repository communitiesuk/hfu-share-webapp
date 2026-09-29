from django.template.loader import render_to_string


def render_app_concatenated_text(*items):
    return render_to_string(
        "webapp/components/typography/concatenated_text.html",
        {"items": items},
    )


def render_app_concatenated_text_with_wrapper(*items, wrapper_class=None):
    return render_to_string(
        "webapp/components/typography/concatenated_text_with_wrapper.html",
        {
            "items": items,
            "wrapper_class": wrapper_class,
        },
    )
