import pytest
from playwright.sync_api import expect

from ..pages.home_page import HomePage
from .base import BrowserTest

GUEST_FULL_NAME = "Deduplication Browser_test"


@pytest.fixture
def guest_deduplication_page(home_page: HomePage) -> HomePage:
    home_page.click_on_card("Fix duplicate records")
    home_page.assert_has_heading("Fix duplicate records")

    home_page.check_field("Guests")
    home_page.click_button("Continue")
    home_page.assert_has_heading("Fix duplicate guest records")

    return home_page


def _search_for_guest_pair(guest_deduplication_page: HomePage):
    guest_deduplication_page.click_button("Show filters")
    guest_deduplication_page.enter_text_into_form_field("Search", "Deduplication")
    guest_deduplication_page.click_button("Apply filters")


def _select_guest_record(guest_deduplication_page: HomePage):
    guest_deduplication_page.page.get_by_role(
        "button", name=f"Select {GUEST_FULL_NAME}"
    ).first.click()


class TestGuestDeduplicationJourney(BrowserTest):
    def test_guest_deduplication_journey_and_removes_duplicate_from_list(
        self, guest_deduplication_page: HomePage
    ):
        # Filter the list
        _search_for_guest_pair(guest_deduplication_page)
        expect(
            guest_deduplication_page.page.get_by_role(
                "button", name=f"Select {GUEST_FULL_NAME}"
            )
        ).to_have_count(2)

        # Select the first record
        _select_guest_record(guest_deduplication_page)
        guest_deduplication_page.assert_has_heading("View selected record")

        guest_deduplication_page.click_button("Select another record")
        guest_deduplication_page.assert_has_heading("Select next record")

        # Search again and select the second (only remaining) record
        _search_for_guest_pair(guest_deduplication_page)
        expect(
            guest_deduplication_page.page.get_by_role(
                "button", name=f"Select {GUEST_FULL_NAME}"
            )
        ).to_have_count(1)
        _select_guest_record(guest_deduplication_page)
        guest_deduplication_page.assert_has_heading("View selected records")

        # Review the selection
        guest_deduplication_page.click_button("Confirm selection")
        guest_deduplication_page.assert_has_heading("Deduplicate selected records")
        guest_deduplication_page.assert_page_contains_text(GUEST_FULL_NAME)

        # Complete the deduplication
        guest_deduplication_page.click_button("Continue")
        guest_deduplication_page.assert_has_heading("Select correct details")

        guest_deduplication_page.click_button("Continue deduplication")
        guest_deduplication_page.assert_has_heading(
            "Check details and complete deduplication"
        )

        guest_deduplication_page.click_button("Yes, confirm and deduplicate")
        guest_deduplication_page.assert_page_contains_text(
            "You have deduplicated 2 guest records"
        )

        # The non-principal (duplicate) record is no longer shown as a
        # standalone record in the guest list
        guest_deduplication_page.goto("/guests/")
        _search_for_guest_pair(guest_deduplication_page)
        expect(
            guest_deduplication_page.page.get_by_role("link", name=GUEST_FULL_NAME)
        ).to_have_count(1)
