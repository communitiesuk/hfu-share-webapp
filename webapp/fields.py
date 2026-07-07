from django import forms
from django_filters.fields import DateRangeField, RangeField

from webapp.validators import validate_range
from webapp.widgets import ConditionalRadioWidget


class ConditionalRadioField(forms.ChoiceField):
    def __init__(self, *args, conditional_inputs=None, **kwargs):
        self.conditional_inputs = conditional_inputs or {}
        super().__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if isinstance(widget, ConditionalRadioWidget):
            widget.conditional_inputs = self.conditional_inputs
        return attrs


class CustomDateRangeField(DateRangeField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.validators.append(validate_range)


class CustomRangeField(RangeField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.validators.append(validate_range)
