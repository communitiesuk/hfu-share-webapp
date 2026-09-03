from dataclasses import dataclass

import pytest
from playwright.sync_api import expect

from ..pages.home_page import HomePage
from .base import BrowserTest


@dataclass(frozen=True)
class SeededGuest:
    full_name: str
    first_name: str
    last_name: str
    date_of_birth: str
    email: str
    phone: str
    passport_id: str
    accommodation_request_title: str


GUEST_ONE = SeededGuest(
    full_name="Ian Yates",
    first_name="Ian",
    last_name="Yates",
    date_of_birth="12 February 1968",
    email="cliffordgreen@example.org",
    phone="01214960497",
    passport_id="36DSA4XOW",
    accommodation_request_title="Ian Yates and 1 other to Flat 32J Bates, SW0Y 7AR",
)
GUEST_TWO = SeededGuest(
    full_name="Martyn Field",
    first_name="Martyn",
    last_name="Field",
    date_of_birth="24 September 2005",
    email="eileenstanley@example.org",
    phone="(0306)9990909",
    passport_id="B53RZIT9A",
    accommodation_request_title="Martyn Field and 1 other to 79 Owen stream, N4J 5SJ",
)
SEARCH_TERM = "yates field"


@pytest.fixture
def guest_deduplication_page(home_page: HomePage) -> HomePage:
    home_page.click_on_card("Fix duplicate records")
    home_page.assert_has_heading("Fix duplicate records")

    home_page.check_field("Guests")
    home_page.click_button("Continue")
    home_page.assert_has_heading("Fix duplicate guest records")

    return home_page


def _search(guest_deduplication_page: HomePage, text: str) -> None:
    show_filters_button = guest_deduplication_page.main_page.get_by_role(
        "button", name="Show filters"
    )
    if show_filters_button.count() > 0:
        show_filters_button.click()
    guest_deduplication_page.enter_text_into_form_field("Search", text)
    guest_deduplication_page.click_button("Apply filters")


def _select_guest_record(guest_deduplication_page: HomePage, full_name: str) -> None:
    guest_deduplication_page.page.get_by_role(
        "button", name=f"Select {full_name}"
    ).click()


def _choose_correct_details(guest_deduplication_page: HomePage) -> None:
    guest_deduplication_page.check_field(GUEST_ONE.first_name)
    guest_deduplication_page.check_field(GUEST_TWO.last_name)
    guest_deduplication_page.check_field(GUEST_ONE.date_of_birth)
    guest_deduplication_page.check_field(GUEST_ONE.email)
    guest_deduplication_page.check_field(GUEST_TWO.phone)
    guest_deduplication_page.check_field(GUEST_TWO.passport_id)


class TestGuestDeduplicationJourney(BrowserTest):
    def test_guest_deduplication_journey_and_removes_duplicate_from_list(
        self, guest_deduplication_page: HomePage
    ) -> None:
        # Filter the list
        _search(guest_deduplication_page, SEARCH_TERM)
        for full_name in (GUEST_ONE.full_name, GUEST_TWO.full_name):
            expect(
                guest_deduplication_page.page.get_by_role(
                    "button", name=f"Select {full_name}"
                )
            ).to_have_count(1)

        # Select the first record
        _select_guest_record(guest_deduplication_page, GUEST_ONE.full_name)
        guest_deduplication_page.assert_has_heading("View selected record")

        guest_deduplication_page.click_button("Select another record")
        guest_deduplication_page.assert_has_heading("Select next record")

        # Search again and select the second (only remaining) record
        _search(guest_deduplication_page, SEARCH_TERM)
        _select_guest_record(guest_deduplication_page, GUEST_TWO.full_name)
        guest_deduplication_page.assert_has_heading("View selected records")

        # Review the selection
        guest_deduplication_page.click_button("Confirm selection")
        guest_deduplication_page.assert_has_heading("Deduplicate selected records")
        guest_deduplication_page.assert_page_contains_text(GUEST_ONE.full_name)
        guest_deduplication_page.assert_page_contains_text(GUEST_TWO.full_name)
        guest_deduplication_page.click_button("Continue")

        # Select accommodation request
        guest_deduplication_page.assert_has_heading("Select accommodation request")
        guest_deduplication_page.check_field(GUEST_ONE.accommodation_request_title)
        guest_deduplication_page.click_button("Continue deduplication")

        # Choose the correct details for the new principal record
        guest_deduplication_page.assert_has_heading("Select correct details")
        _choose_correct_details(guest_deduplication_page)
        guest_deduplication_page.click_button("Continue deduplication")

        # Final confirmation page
        guest_deduplication_page.assert_has_heading(
            "Check details and complete deduplication"
        )
        guest_deduplication_page.click_button("Yes, confirm and deduplicate")

        # Confirm success page
        guest_deduplication_page.assert_page_contains_text(
            "You have deduplicated 2 guest records"
        )
