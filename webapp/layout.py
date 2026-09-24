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

class PlainRadioChoice(ConditionalQuestion):
    template = "%s/layout/radio_item.html"


class ConditionalRadiosWithLegend(ConditionalRadios):
    def __init__(self, field: str, *choices, legend_size: str | None = None):
        wrapped = [
            PlainRadioChoice(choice) if isinstance(choice, str) else choice
            for choice in choices
        ]
        super().__init__(field, *wrapped)
        self.legend_size = legend_size

    def render(self, form, context, template_pack=TEMPLATE_PACK, **kwargs) -> str:
        if self.legend_size:
            context.update({"legend_size": Size.for_legend(self.legend_size)})
        return super().render(form, context, template_pack, **kwargs)


class BaseLink(TemplateNameMixin):
    template = "%s/layout/link.html"

    def __init__(
        self,
        text: str,
        href: str,
        css_class: str = "",
        template: Optional[str] = None,
        **kwargs,
    ):
        self.text = text
        self.href = href

        if css_class:
            self.field_classes += f" {css_class.strip()}"

        self.template = template or self.template
        self.flat_attrs = flatatt(kwargs)

    def render(self, form, context, template_pack=TEMPLATE_PACK, **kwargs):
        template = self.get_template_name(template_pack)

        href = Template(self.href).render(context)

        context.update(
            {
                "text": self.text,
                "href": href,
                "field_classes": self.field_classes,
                "flat_attrs": self.flat_attrs,
            }
        )
        return render_to_string(template, context.flatten())


class Link(BaseLink):
    field_classes = "govuk-link"

    @staticmethod
    def cancel(text: str = "Cancel", **kwargs):
        return Link(text, "{{ cancel_url }}", no_visited_state=True, **kwargs)

    def __init__(
        self,
        text: str,
        href: str,
        css_class: str = "",
        no_visited_state: bool = False,
        template: Optional[str] = None,
        **kwargs,
    ):
        if no_visited_state:
            css_class += " govuk-link--no-visited-state"

        super().__init__(text, href, css_class, template, **kwargs)


class ButtonAsLink(BaseLink):
    field_classes = "govuk-button"

    def __init__(
        self,
        text: str,
        href: str,
        css_class: str = "",
        type: str = "primary",
        template: Optional[str] = None,
        **kwargs,
    ):
        match type:
            case "secondary":
                css_class += " govuk-button--secondary"
            case "warning":
                css_class += " govuk-button--warning"

        super().__init__(text, href, css_class, template, data_module="govuk-button")


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
