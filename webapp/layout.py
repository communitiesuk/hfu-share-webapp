from crispy_forms.utils import TEMPLATE_PACK
from crispy_forms_gds.layout import ConditionalRadios, Size


class ConditionalRadiosWithLegend(ConditionalRadios):
    def __init__(self, field: str, *choices, legend_size: str | None = None):
        super().__init__(field, *choices)
        self.legend_size = legend_size

    def render(self, form, context, template_pack=TEMPLATE_PACK, **kwargs) -> str:
        if self.legend_size:
            context.update({"legend_size": Size.for_legend(self.legend_size)})
        return super().render(form, context, template_pack, **kwargs)
