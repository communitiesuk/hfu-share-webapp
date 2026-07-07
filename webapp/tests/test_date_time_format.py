from datetime import datetime, timezone

from django.test import TestCase
from freezegun import freeze_time

from webapp.utils import CustomDateColumn, CustomDateTimeColumn


class CustomDateColumnTests(TestCase):
    def setUp(self):
        self.column = CustomDateColumn()

    def test_table_date_column_removes_dots_from_am_pm(self):
        value = datetime(2026, 9, 1, tzinfo=timezone.utc)

        rendered = self.column.render(value=value)

        self.assertEqual(rendered, "1 Sep 2026")

    def test_table_date_column_handles_no_value(self):
        not_rendered = self.column.render(value=None)

        self.assertEqual(not_rendered, "—")


class CustomDateTimeColumnTests(TestCase):
    def setUp(self):
        self.column = CustomDateTimeColumn()

    def test_table_date_time_column_removes_dots_from_am_pm(self):
        with freeze_time(datetime(2026, 9, 1, 11, 22, tzinfo=timezone.utc)):
            value = datetime.now()

            rendered = self.column.render(value=value)

            self.assertEqual(rendered, "1 Sep 2026, 11:22am")

    def test_table_date_time_column_handles_no_value(self):
        not_rendered = self.column.render(value=None)

        self.assertEqual(not_rendered, "—")
