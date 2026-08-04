from datetime import date, datetime, timezone

from django.template import Context, Template
from django.test import TestCase

from webapp.formatting import format_date_value


class FormatDateValueTests(TestCase):
    def test_date_uses_detail_format_by_default(self):
        self.assertEqual(format_date_value(date(2026, 9, 1)), "1 September 2026")

    def test_date_uses_list_format_when_list_view(self):
        self.assertEqual(
            format_date_value(date(2026, 9, 1), list_view=True), "1 Sep 2026"
        )

    def test_datetime_uses_detail_format_by_default(self):
        value = datetime(2026, 12, 4, 10, 22, tzinfo=timezone.utc)

        self.assertEqual(format_date_value(value), "4 December 2026 at 10:22am")

    def test_datetime_uses_list_format_when_list_view(self):
        value = datetime(2026, 12, 4, 10, 22, tzinfo=timezone.utc)

        self.assertEqual(
            format_date_value(value, list_view=True), "4 Dec 2026, 10:22am"
        )

    def test_aware_datetime_is_converted_to_local_time(self):
        value = datetime(2026, 9, 1, 23, 22, tzinfo=timezone.utc)

        self.assertEqual(format_date_value(value), "2 September 2026 at 12:22am")

    def test_naive_datetime_is_formatted_as_given(self):
        value = datetime(2026, 9, 1, 23, 22)

        self.assertEqual(format_date_value(value), "1 September 2026 at 11:22pm")

    def test_midday_uses_lowercase_pm(self):
        value = datetime(2026, 12, 4, 12, 0)

        self.assertEqual(format_date_value(value), "4 December 2026 at 12:00pm")

    def test_none_is_returned_unchanged(self):
        self.assertIsNone(format_date_value(None))

    def test_non_date_value_is_returned_unchanged(self):
        self.assertEqual(format_date_value("Not a date"), "Not a date")


class FormatDateFilterTests(TestCase):
    def render(self, template, value):
        return (
            Template("{% load filters %}" + template)
            .render(Context({"value": value}))
            .strip()
        )

    def test_filter_uses_detail_format_by_default(self):
        rendered = self.render("{{ value|format_date }}", date(2026, 9, 1))

        self.assertEqual(rendered, "1 September 2026")

    def test_filter_uses_list_format_when_asked(self):
        rendered = self.render('{{ value|format_date:"list" }}', date(2026, 9, 1))

        self.assertEqual(rendered, "1 Sep 2026")

    def test_filter_formats_datetimes(self):
        value = datetime(2026, 12, 4, 10, 22, tzinfo=timezone.utc)

        rendered = self.render("{{ value|format_date }}", value)

        self.assertEqual(rendered, "4 December 2026 at 10:22am")

    def test_filter_leaves_non_dates_unchanged(self):
        rendered = self.render("{{ value|format_date }}", "Not a date")

        self.assertEqual(rendered, "Not a date")
