from datetime import date, datetime, timezone

from test_utils.base import BaseTestCase
from webapp.utils import CustomDateColumn, CustomDateTimeColumn


class CustomDateColumnTests(BaseTestCase):
    def setUp(self):
        self.column = CustomDateColumn()

    def test_renders_a_dash_when_there_is_no_value(self):
        self.assertEqual(self.column.render(value=None), "—")

    def test_renders_a_datetime_as_a_date_with_no_time(self):
        afternoon = datetime(2026, 9, 1, 14, 30, tzinfo=timezone.utc)

        self.assertEqual(self.column.render(value=afternoon), "1 Sep 2026")

    def test_converts_aware_datetimes_to_uk_time_before_taking_the_date(self):
        late_evening_in_utc = datetime(2026, 9, 1, 23, 22, tzinfo=timezone.utc)

        self.assertEqual(self.column.render(value=late_evening_in_utc), "2 Sep 2026")

    def test_renders_every_value_type_a_table_can_supply(self):
        examples = [
            ("a date", date(2026, 9, 1), "1 Sep 2026"),
            ("a date in winter", date(2026, 12, 4), "4 Dec 2026"),
            (
                "a datetime with no time zone",
                datetime(2026, 9, 1, 14, 30),
                "1 Sep 2026",
            ),
            (
                "a datetime during British Summer Time",
                datetime(2026, 9, 1, 14, 30, tzinfo=timezone.utc),
                "1 Sep 2026",
            ),
            (
                "a datetime that becomes the next day once in British Summer Time",
                datetime(2026, 9, 1, 23, 22, tzinfo=timezone.utc),
                "2 Sep 2026",
            ),
            (
                "a datetime during Greenwich Mean Time",
                datetime(2026, 12, 4, 23, 22, tzinfo=timezone.utc),
                "4 Dec 2026",
            ),
            ("no value at all", None, "—"),
        ]

        for description, value, expected_output in examples:
            with self.subTest(description):
                self.assertEqual(self.column.render(value=value), expected_output)


class CustomDateTimeColumnTests(BaseTestCase):
    def setUp(self):
        self.column = CustomDateTimeColumn()

    def test_renders_a_dash_when_there_is_no_value(self):
        self.assertEqual(self.column.render(value=None), "—")

    def test_renders_am_and_pm_in_lower_case_without_full_stops(self):
        late_morning = datetime(2026, 9, 1, 11, 22)

        self.assertEqual(self.column.render(value=late_morning), "1 Sep 2026, 11:22am")

    def test_converts_aware_datetimes_to_uk_time(self):
        afternoon_in_utc = datetime(2026, 9, 1, 14, 30, tzinfo=timezone.utc)

        self.assertEqual(
            self.column.render(value=afternoon_in_utc), "1 Sep 2026, 3:30pm"
        )

    def test_renders_every_value_type_a_table_can_supply(self):
        examples = [
            (
                "a datetime with no time zone",
                datetime(2026, 9, 1, 14, 30),
                "1 Sep 2026, 2:30pm",
            ),
            (
                "a datetime during British Summer Time",
                datetime(2026, 9, 1, 14, 30, tzinfo=timezone.utc),
                "1 Sep 2026, 3:30pm",
            ),
            (
                "a datetime that becomes the next day once in British Summer Time",
                datetime(2026, 9, 1, 23, 22, tzinfo=timezone.utc),
                "2 Sep 2026, 12:22am",
            ),
            (
                "a datetime during Greenwich Mean Time",
                datetime(2026, 12, 4, 23, 22, tzinfo=timezone.utc),
                "4 Dec 2026, 11:22pm",
            ),
            ("no value at all", None, "—"),
        ]

        for description, value, expected_output in examples:
            with self.subTest(description):
                self.assertEqual(self.column.render(value=value), expected_output)
