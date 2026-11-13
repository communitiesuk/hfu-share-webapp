import pytest
from playwright.sync_api import expect

from ..pages import HomePage
from ..seeded_data import SeededGuest
from .base import BrowserTest

GUEST_CONFIRMED_VISA_CHECKS_REQUIRED = SeededGuest(
    id="browser-test-person-00026",
    full_name="Bruce James",
    first_name="Bruce",
    last_name="James",
    date_of_birth="5 November 1970",
    email="sylviabowen@example.org",
    phone="(020)74960853",
    passport_id="J36LQNND9",
    accommodation_request_title="Bruce James and 1 other to Flat 32J Bates, SW0Y 7AR",
)
GUEST_ARRIVED_VISA_CHECKS_REQUIRED = SeededGuest(
    id="browser-test-person-00032",
    full_name="Rita Price",
    first_name="Rita",
    last_name="Price",
    date_of_birth="6 August 2004",
    email="brownamber@example.org",
    phone="01632 960004",
    passport_id="Y6B5L0BCB",
    accommodation_request_title="Rita Price and 1 other to Studio 3 Aimee, OX3M 9AQ",
)
SEARCH_TERM = "james price"


@pytest.fixture
def guest_deduplication_page(home_page: HomePage) -> HomePage:
    home_page.sign_in()
    home_page.click_on_card("Fix duplicate records")
    home_page.assert_has_heading("Fix duplicate records")

    home_page.check_field("Guests")
    home_page.click_button("Continue")
    home_page.assert_has_heading("Fix duplicate guest records")

    return home_page


def _select_guest_record(guest_deduplication_page: HomePage, full_name: str) -> None:
    guest_deduplication_page.main_page.get_by_role(
        "button", name=f"Select {full_name}"
    ).click()


def _choose_correct_details(guest_deduplication_page: HomePage) -> None:
    guest_deduplication_page.check_field(
        GUEST_CONFIRMED_VISA_CHECKS_REQUIRED.first_name
    )
    guest_deduplication_page.check_field(GUEST_ARRIVED_VISA_CHECKS_REQUIRED.last_name)
    guest_deduplication_page.check_field(
        GUEST_CONFIRMED_VISA_CHECKS_REQUIRED.date_of_birth
    )
    guest_deduplication_page.check_field(GUEST_CONFIRMED_VISA_CHECKS_REQUIRED.email)
    guest_deduplication_page.check_field(GUEST_ARRIVED_VISA_CHECKS_REQUIRED.phone)
    guest_deduplication_page.check_field(GUEST_ARRIVED_VISA_CHECKS_REQUIRED.passport_id)


class TestGuestDeduplicationJourney(BrowserTest):
    def test_guest_deduplication_journey(
        self, guest_deduplication_page: HomePage
    ) -> None:
        # Filter the list
        guest_deduplication_page.search(SEARCH_TERM)
        for full_name in (
            GUEST_CONFIRMED_VISA_CHECKS_REQUIRED.full_name,
            GUEST_ARRIVED_VISA_CHECKS_REQUIRED.full_name,
        ):
            expect(
                guest_deduplication_page.main_page.get_by_role(
                    "button", name=f"Select {full_name}"
                )
            ).to_have_count(1)

        # Select the first record
        _select_guest_record(
            guest_deduplication_page, GUEST_CONFIRMED_VISA_CHECKS_REQUIRED.full_name
        )
        guest_deduplication_page.assert_has_heading("View selected record")

        guest_deduplication_page.click_button("Select another record")
        guest_deduplication_page.assert_has_heading("Select next record")

        # Search again and select the second (only remaining) record
        guest_deduplication_page.search(SEARCH_TERM)
        _select_guest_record(
            guest_deduplication_page, GUEST_ARRIVED_VISA_CHECKS_REQUIRED.full_name
        )
        guest_deduplication_page.assert_has_heading("View selected records")

        # Review the selection
        guest_deduplication_page.click_button("Confirm selection")
        guest_deduplication_page.assert_has_heading("Deduplicate selected records")
        guest_deduplication_page.assert_page_contains_text(
            GUEST_CONFIRMED_VISA_CHECKS_REQUIRED.full_name
        )
        guest_deduplication_page.assert_page_contains_text(
            GUEST_ARRIVED_VISA_CHECKS_REQUIRED.full_name
        )
        guest_deduplication_page.click_button("Continue")

        # Select accommodation request
        guest_deduplication_page.assert_has_heading("Select accommodation request")
        guest_deduplication_page.check_field(
            GUEST_CONFIRMED_VISA_CHECKS_REQUIRED.accommodation_request_title
        )
        guest_deduplication_page.click_button("Continue")

        # Choose the correct details for the new principal record
        guest_deduplication_page.assert_has_heading("Select correct details")
        _choose_correct_details(guest_deduplication_page)
        guest_deduplication_page.click_button("Continue")

        # Final confirmation page
        guest_deduplication_page.assert_has_heading(
            "Check details and complete deduplication"
        )
        guest_deduplication_page.click_button("Yes, confirm and deduplicate")

        # Confirm success page
        guest_deduplication_page.assert_page_contains_text(
            "You have deduplicated 2 guest records"
        )
