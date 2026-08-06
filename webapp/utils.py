from typing import Callable

import django_tables2 as tables
from django_filters import ChoiceFilter, MultipleChoiceFilter, RangeFilter
from django_filters.conf import settings

from webapp.fields import CustomDateRangeField, CustomRangeField
from webapp.formatting import format_date_value, to_local_date


class LazyMultipleChoiceFilter(MultipleChoiceFilter):
    def get_field_choices(self):
        choices = self.extra.get("choices", [])
        if isinstance(choices, Callable):
            choices = choices()
        return choices

    @property
    def field(self):
        if not hasattr(self, "_field"):
            field_kwargs = self.extra.copy()

            if settings.DISABLE_HELP_TEXT:
                field_kwargs.pop("help_text", None)

            field_kwargs.update(choices=self.get_field_choices())

            self._field = self.field_class(label=self.label, **field_kwargs)
        return self._field


class LazyChoiceFilter(ChoiceFilter):
    def get_field_choices(self):
        choices = self.extra.get("choices", [])
        if isinstance(choices, Callable):
            choices = choices()
        return choices

    @property
    def field(self):
        if not hasattr(self, "_field"):
            field_kwargs = self.extra.copy()

            if settings.DISABLE_HELP_TEXT:
                field_kwargs.pop("help_text", None)

            field_kwargs.update(choices=self.get_field_choices())
            self._field = self.field_class(label=self.label, **field_kwargs)
        return self._field


class CustomDateFromToRangeFilter(RangeFilter):
    field_class = CustomDateRangeField


class CustomRangeFilter(RangeFilter):
    field_class = CustomRangeField


class CustomDateColumn(tables.Column):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("default", "—")
        super().__init__(*args, **kwargs)

    def render(self, value):
        if value is None:
            return self.default

        return format_date_value(to_local_date(value), list_view=True)


class CustomDateTimeColumn(tables.Column):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("default", "—")
        super().__init__(*args, **kwargs)

    def render(self, value):
        if value is None:
            return self.default

        return format_date_value(value, list_view=True)


def normalize_empty_to_none(value):
    return value or None
