from typing import Optional

from crispy_forms.layout import TemplateNameMixin, flatatt
from crispy_forms.utils import TEMPLATE_PACK
from crispy_forms_gds.layout import ConditionalQuestion, ConditionalRadios, Size
from django.middleware.csrf import get_token
from django.template import Template
from django.template.loader import render_to_string

from visa_applications.templatetags.visa_application_extras import (
    visa_status_to_tag_colour,
)

class LinkBuilder:
    def __init__(
        self,
        text: str,
        href: str,
        css_class: str = "",
        no_visited_state: bool = False,
        opens_in_new_tab: bool = False,
    ):
        self.text = text
        self.href = href
        self.opens_in_new_tab = opens_in_new_tab
        self.classes = "govuk-link"

        if no_visited_state:
            self.classes += " govuk-link--no-visited-state"

        if css_class:
            self.classes += f" {css_class}"

class TagBuilder:
    def __init__(self, text: str, colour: Optional[str] = None, css_class: str = ""):
        self.text = text
        self.classes = "govuk-tag"

        if colour:
            self.classes += f" govuk-tag--{colour}"

        if css_class:
            self.classes += f" {css_class}"
