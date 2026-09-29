from typing import Optional, Type

from crispy_forms.layout import TemplateNameMixin
from crispy_forms.utils import TEMPLATE_PACK
from crispy_forms_gds.layout import ConditionalQuestion, ConditionalRadios, Size
from django.template import Template
from django.template.loader import render_to_string

from webapp.component_builders import LinkAsButtonBuilder, LinkBuilder, LinkBuilderBase


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


class Link(TemplateNameMixin):
    template = "webapp/components/typography/link.html"

    @staticmethod
    def cancel(text: str = "Cancel", **kwargs):
        return Link(text, "{{ cancel_url }}", no_visited_state=True, **kwargs)

    @staticmethod
    def as_button(
        text: str,
        href: str,
        *,
        css_class: str = "",
        type: str = "primary",
        template: Optional[str] = None,
        **kwargs,
    ):
        return Link(
            text,
            href,
            css_class=css_class,
            type=type,
            template=template,
            builder=LinkAsButtonBuilder,
            **kwargs,
        )

    def __init__(
        self,
        text: str,
        href: str,
        css_class: str = "",
        visually_hidden_text: Optional[str] = None,
        no_visited_state: bool = False,
        opens_in_new_tab: bool = False,
        template: Optional[str] = None,
        builder: Type[LinkBuilderBase] = LinkBuilder,
        **kwargs,
    ):
        self.link_buidler = builder(
            text,
            href,
            css_class=css_class,
            visually_hidden_text=visually_hidden_text,
            no_visited_state=no_visited_state,
            opens_in_new_tab=opens_in_new_tab,
            **kwargs,
        )
        self.template = template or self.template

    def render(self, form, context, template_pack=TEMPLATE_PACK, **kwargs):
        template = self.get_template_name(template_pack)

        self.link_buidler.href = Template(self.link_buidler.href).render(context)

        context.update(
            {
                "link": self.link_buidler,
            }
        )
        return render_to_string(template, context.flatten())
