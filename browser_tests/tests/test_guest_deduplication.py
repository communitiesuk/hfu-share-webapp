import pytest
from playwright.sync_api import expect

from ..pages.home_page import HomePage
from .base import BrowserTest

GUEST_ONE_FULL_NAME = "Valerie Poole"
GUEST_TWO_FULL_NAME = "Philip Berry"
SEARCH_TERM = "poole berry"

@pytest.fixture
def guest_deduplication_page(home_page: HomePage) -> HomePage:
    home_page.click_on_card("Fix duplicate records")
    home_page.assert_has_heading("Fix duplicate records")

    home_page.check_field("Guests")
    home_page.click_button("Continue")
    home_page.assert_has_heading("Fix duplicate guest records")

    return home_page


def _search(guest_deduplication_page: HomePage, text: str):
    show_filters_button = guest_deduplication_page.main_page.get_by_role(
        "button", name="Show filters"
    )
    if show_filters_button.count() > 0:
        show_filters_button.click()
    guest_deduplication_page.enter_text_into_form_field("Search", text)
    guest_deduplication_page.click_button("Apply filters")


def _select_guest_record(guest_deduplication_page: HomePage, full_name: str):
    guest_deduplication_page.page.get_by_role(
        "button", name=f"Select {full_name}"
    ).click()


def _choose_correct_details(guest_deduplication_page: HomePage):
    guest_deduplication_page.check_field("Valerie")
    guest_deduplication_page.check_field("Poole")
    guest_deduplication_page.check_field("31 May 1965")
    guest_deduplication_page.check_field("joycejackson@example.org")
    guest_deduplication_page.check_field("0808 157 0233")
    guest_deduplication_page.check_field("9T8NIK1PW")


class TestGuestDeduplicationJourney(BrowserTest):
    def test_guest_deduplication_journey_and_removes_duplicate_from_list(
        self, guest_deduplication_page: HomePage
    ):
        # Filter the list
        _search(guest_deduplication_page, SEARCH_TERM)
        for full_name in (GUEST_ONE_FULL_NAME, GUEST_TWO_FULL_NAME):
            expect(
                guest_deduplication_page.page.get_by_role(
                    "button", name=f"Select {full_name}"
                )
            ).to_have_count(1)

        # Select the first record
        _select_guest_record(guest_deduplication_page, GUEST_ONE_FULL_NAME)
        guest_deduplication_page.assert_has_heading("View selected record")

        guest_deduplication_page.click_button("Select another record")
        guest_deduplication_page.assert_has_heading("Select next record")

        # Search again and select the second (only remaining) record
        _search(guest_deduplication_page, SEARCH_TERM)
        _select_guest_record(guest_deduplication_page, GUEST_TWO_FULL_NAME)
        guest_deduplication_page.assert_has_heading("View selected records")

        # Review the selection
        guest_deduplication_page.click_button("Confirm selection")
        guest_deduplication_page.assert_has_heading("Deduplicate selected records")
        guest_deduplication_page.assert_page_contains_text(GUEST_ONE_FULL_NAME)
        guest_deduplication_page.assert_page_contains_text(GUEST_TWO_FULL_NAME)

        guest_deduplication_page.click_button("Continue")
        guest_deduplication_page.assert_has_heading("Select correct details")
        _choose_correct_details(guest_deduplication_page)

        guest_deduplication_page.click_button("Continue deduplication")
        guest_deduplication_page.assert_has_heading(
            "Check details and complete deduplication"
        )

        guest_deduplication_page.click_button("Yes, confirm and deduplicate")
        guest_deduplication_page.assert_page_contains_text(
            "You have deduplicated 2 guest records"
        )

