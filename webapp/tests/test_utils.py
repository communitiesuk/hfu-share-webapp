from freezegun import freeze_time

from test_utils.base import BaseTestCase
from webapp.utils import date_hint_text


@freeze_time("2026/9/14")
class TestDateHintText(BaseTestCase):
    def test_returns_date_seven_days_ago(self):
        assert date_hint_text(7) == "For example, 7/9/2026."

    def test_returns_today_when_days_is_zero(self):
        assert date_hint_text(0) == "For example, 14/9/2026."

    def test_formats_single_digit_day_and_month_without_leading_zeros(self):
        assert date_hint_text(252) == "For example, 5/1/2026."
