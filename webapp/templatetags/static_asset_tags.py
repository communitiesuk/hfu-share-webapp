from functools import cache
from pathlib import Path
from typing import Literal

from django import template
from django.templatetags.static import static

register = template.Library()

FRONTENDS = Literal["govuk", "moj"]
STATIC_FILE_TYPES = Literal["js", "css"]

BASE_DIR = Path(__file__).resolve().parent.parent.parent


@cache
def _frontend_version(frontend: FRONTENDS) -> str:
    with open(
        BASE_DIR / "static" / f"{frontend}-frontend" / "VERSION.txt"
    ) as version_file:
        return version_file.read().strip()


@cache
def _frontend_path(frontend: FRONTENDS, file_type: STATIC_FILE_TYPES) -> str:
    return static(
        f"{frontend}-frontend/{frontend}-frontend-{_frontend_version(frontend)}.min.{file_type}"
    )


@register.simple_tag
def govuk_frontend_css_path():
    return _frontend_path("govuk", "css")


@register.simple_tag
def govuk_frontend_js_path():
    return _frontend_path("govuk", "js")


@register.simple_tag
def moj_frontend_css_path():
    return _frontend_path("moj", "css")


@register.simple_tag
def moj_frontend_js_path():
    return _frontend_path("moj", "js")
