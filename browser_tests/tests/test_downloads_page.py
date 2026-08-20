import re
from datetime import datetime, timedelta, timezone
from functools import cache
from typing import Optional

import pytest

from ..pages.home_page import HomePage
from .base import BrowserTest


@pytest.fixture
def download_page(home_page: HomePage):
    home_page.click_on_card("Download data")

    home_page.assert_has_heading("Download data")

    return home_page


# So all of the tests use the same date
@cache
def today():
    return datetime.now(timezone.utc)


class TestDownloadPage(BrowserTest):
    def test_download_data_validation_messages(self, download_page: HomePage):
        download_page.click_button("Download data")

        download_page.has_the_following_error_messages("Select which data to download.")
        download_page.field_has_error_message(
            "Select data", "Select which data to download.", element="legend"
        )

    @pytest.mark.parametrize(
        ("from_date", "to_date", "from_date_error", "to_date_error"),
        (
            (
                "invalid date",
                "invalid date",
                "Enter a valid date.",
                "Enter a valid date.",
            ),
            ("29/02/2026", "29/03/2026", "Enter a valid date.", None),
            (
                "29/05/2026",
                "29/03/2026",
                None,
                "The end date must be the same as or later than the start date.",
            ),
        ),
    )
    def test_download_all_data_validation_messages(
        self,
        download_page: HomePage,
        from_date: str,
        to_date: str,
        from_date_error: Optional[str],
        to_date_error: Optional[str],
    ):
        download_page.check_field("All data")

        download_page.enter_text_into_form_field("Date from", from_date)
        download_page.enter_text_into_form_field("Date to", to_date)

        download_page.click_button("Download data")

        download_page.has_the_following_error_messages(
            *(
                error_message
                for error_message in [from_date_error, to_date_error]
                if error_message is not None
            )
        )

        for date_field, error_message in (
            ("Date from", from_date_error),
            ("Date to", to_date_error),
        ):
            if error_message is not None:
                download_page.field_has_error_message(date_field, error_message)
            else:
                download_page.field_has_no_error_message(date_field)

    @pytest.mark.parametrize(
        ("from_date", "to_date"),
        (
            (  # No dates
                None,
                None,
            ),
            (  # Only from date
                today() - timedelta(weeks=4),
                None,
            ),
            (  # Only to date
                None,
                today(),
            ),
            (  # Same date
                today() - timedelta(weeks=4),
                today() - timedelta(weeks=4),
            ),
            (  # Date range
                today() - timedelta(weeks=4),
                today(),
            ),
        ),
    )
    def test_can_download_all_data(
        self,
        download_page: HomePage,
        from_date: Optional[datetime],
        to_date: Optional[datetime],
    ):
        download_page.check_field("All data")

        for date_field, value in (
            ("Date from", from_date),
            ("Date to", to_date),
        ):
            if value is not None:
                download_page.enter_text_into_date_field(date_field, value)

        with download_page.page.expect_download() as download_info:
            download_page.click_button("Download data")

        filename = download_info.value.suggested_filename

        assert re.fullmatch(
            r"all_\d{2}-\d{2}-\d{2}_\d{2}-\d{2}\.csv",
            filename,
        )

    @pytest.mark.parametrize(
        ("selected_data", "expected_filename"),
        (
            (
                "Visa applications",
                "visa_applications",
            ),
            (
                "Guests",
                "guests",
            ),
            (
                "Sponsors and hosts",
                "sponsors",
            ),
            (
                "Accommodation",
                "accommodation",
            ),
            (
                "Applications to sponsor a child",
                "uams",
            ),
        ),
    )
    def test_can_download_other_data(
        self, download_page: HomePage, selected_data: str, expected_filename: str
    ):
        download_page.check_field(selected_data)

        with download_page.page.expect_download() as download_info:
            download_page.click_button("Download data")

        filename = download_info.value.suggested_filename

        timestamp_pattern = r"\d{2}-\d{2}-\d{2}_\d{2}-\d{2}"

        assert re.fullmatch(
            rf"{re.escape(expected_filename)}_{timestamp_pattern}\.csv",
            filename,
        )
