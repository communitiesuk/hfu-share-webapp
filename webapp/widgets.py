from typing import Callable

from django.forms import MultiWidget, TextInput
from django.forms.widgets import ChoiceWidget, DateInput, Select, Widget
from django.template.loader import render_to_string


class DatePicker(DateInput):
    template_name = "webapp/widgets/datepicker.html"


RANGE_INPUT_ATTR_MAPPING: dict[str, str] = {
    "input_size": "size",
    "from_label": "label",
    "to_label": "label",
    "from_hint": "hint",
    "to_hint": "hint",
    "unit_hint": "unit_hint",
}


class RangeInput(MultiWidget):
    template_name = "webapp/widgets/stackedrangeinput.html"

    def __init__(self, attrs=None, sub_widget=TextInput):
        widgets = (
            sub_widget({"label": "Minimum", "type": "number", "min": 0}),
            sub_widget({"label": "Maximum", "type": "number", "min": 0}),
        )

        if attrs:
            for attr_name, attr_value in attrs.items():
                widgets_to_apply_attr_to = []
                if attr_name.startswith("from_"):
                    widgets_to_apply_attr_to = [widgets[0]]
                elif attr_name.startswith("to"):
                    widgets_to_apply_attr_to = [widgets[1]]
                else:
                    widgets_to_apply_attr_to = widgets

                for widget in widgets_to_apply_attr_to:
                    widget.attrs.update(
                        {RANGE_INPUT_ATTR_MAPPING[attr_name]: attr_value}
                    )

        super().__init__(widgets, attrs=attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]


class StackedRangeInput(RangeInput):
    template_name = "webapp/widgets/stackedrangeinput.html"


class InlineRangeInput(RangeInput):
    template_name = "webapp/widgets/inlinerangeinput.html"


class CheckboxSelectMultipleWithTags(ChoiceWidget):
    allow_multiple_selected = True
    use_fieldset = True
    input_type = "checkbox"
    template_name = "webapp/widgets/checkboxes_with_tags.html"

    def __init__(
        self, label_to_tag_colour: Callable[[str], str], attrs=None, choices=()
    ):
        super().__init__(attrs=attrs, choices=choices)
        self.label_to_tag_colour = label_to_tag_colour

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        for _, options, _ in context["widget"]["optgroups"]:
            for option in options:
                option["label_tag_colour_class"] = (
                    f"govuk-tag--{self.label_to_tag_colour(option['label'])}"
                )
        return context


class ConditionalRadioWidget(Widget):
    template_name = "webapp/widgets/conditional_radio.html"

    def __init__(self, attrs=None, choices=(), conditional_inputs=None):
        super().__init__(attrs)
        self.choices = list(choices)
        self.conditional_inputs = conditional_inputs or {}

    def get_context(self, name, value, attrs):
        return {
            "name": name,
            "value": value,
            "choices": self.choices,
            "conditional_inputs": self.conditional_inputs,
        }

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        return render_to_string(self.template_name, context)


class SearchableSelect(Select):
    template_name = "webapp/widgets/searchable_select.html"


class SearchableSelectLazy(Select):
    template_name = "webapp/widgets/searchable_select_lazy.html"


class MultiValueWidget(Widget):
    template_name = "webapp/widgets/multi_value_text_input.html"

    def __init__(self, attrs=None, max_values=5):
        default_attrs = {"class": "array-input-widget", "input_type": "text"}
        self.max_values = max_values
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value or [], attrs)
        context["widget"]["values"] = value or [""]
        context["widget"]["name"] = name
        context["widget"]["max_values"] = self.max_values
        return context

    def value_from_datadict(self, data, files, name):
        values = [
            v for k, v in data.items() if k.startswith(f"{name}-") and v.strip() != ""
        ]
        return values
