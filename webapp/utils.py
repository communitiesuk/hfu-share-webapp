from datetime import datetime
from typing import Callable

import django_tables2 as tables
from django.utils import timezone
from django.utils.formats import date_format
from django_filters import ChoiceFilter, MultipleChoiceFilter, RangeFilter
from django_filters.conf import settings

from webapp.fields import CustomDateRangeField, CustomRangeField


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
    format = "j M Y"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("default", "—")
        super().__init__(*args, **kwargs)

    def render(self, value):
        if value is None:
            return self.default
        if isinstance(value, str):
            value_str = value.strip()
            value = datetime.strptime(value_str, "%d %b %Y")

        return date_format(value, format=self.format)


class CustomDateTimeColumn(tables.Column):
    format = "j M Y, g:ia"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("default", "—")
        super().__init__(*args, **kwargs)

    def render(self, value):
        if value is None:
            return self.default

        if timezone.is_aware(value):
            value = timezone.localtime(value)

        formatted = date_format(value, format=self.format)
        return formatted.replace("a.m.", "am").replace("p.m.", "pm")


def normalize_empty_to_none(value):
    return value or None
