import pytest
from playwright.sync_api import expect

from ..pages import HomePage
from ..seeded_data import SeededAccommodationRequest
from .base import BrowserTest

DESTINATION_COUNTRY = "England"
DESTINATION_LA_SEARCH_TEXT = "Isles of Scilly"
DESTINATION_LA_OPTION_LABEL = "Isles of Scilly (LTLA)"

ACCOMMODATION_REQUEST = SeededAccommodationRequest(
    id="browser-test-ar-00006",
    full_name="Edward Schofield and 2 others",
    accommodation_request_title=(
        "Edward Schofield and 2 others to 582 Gerald thr, W02 6TR"
    ),
    address="582 Gerald throughway, Hobbiton",
    sponsor="",
    guest_full_names=("Edward Schofield", "Barbara Reid", "Kerry Lowe"),
)


@pytest.fixture
def reassignment_request_page(home_page: HomePage) -> HomePage:
    home_page.sign_in()

    home_page.click_on_card("Accommodation requests")
    home_page.assert_has_heading("Accommodation requests")

    return home_page


class TestReassignmentRequestJourney(BrowserTest):
    def test_reassignment_request_journey(
        self, reassignment_request_page: HomePage
    ) -> None:
        home_page = reassignment_request_page

        # Open the accommodation request and start "Reassign guests"
        home_page.search(ACCOMMODATION_REQUEST.guest_full_names[0])
        home_page.click_link(ACCOMMODATION_REQUEST.accommodation_request_title)
        home_page.assert_has_heading(
            f"Accommodation request record for "
            f"{ACCOMMODATION_REQUEST.accommodation_request_title}"
        )

        home_page.click_link("Actions")
        home_page.click_link("Start Move guests (rematch or reassign)")

        # Are the guests remaining within your local authority? No
        home_page.check_field("No")
        home_page.click_button("Continue")

        # Select guests
        for guest_full_name in ACCOMMODATION_REQUEST.guest_full_names:
            home_page.check_field(guest_full_name)
        home_page.click_button("Continue")

        # Select country
        home_page.check_field(DESTINATION_COUNTRY)
        home_page.click_button("Continue")

        # Select local authority
        home_page.enter_text_into_form_field(
            "Select local authority", DESTINATION_LA_SEARCH_TEXT
        )
        home_page.main_page.get_by_role(
            "option", name=DESTINATION_LA_OPTION_LABEL
        ).click()
        home_page.click_button("Continue")

        # Reason
        home_page.enter_text_into_form_field(
            "Reason for moving guests", "Browser test reassignment request"
        )
        home_page.click_button("Continue")

        # Confirmation step
        for guest_full_name in ACCOMMODATION_REQUEST.guest_full_names:
            home_page.assert_page_contains_text(guest_full_name)
        home_page.assert_page_contains_text(DESTINATION_LA_SEARCH_TEXT)

        home_page.check_field("Yes, send the request")
        home_page.click_button("Send request")
        home_page.assert_page_contains_text("You sent a request to move")

        # It appears on the sending LA's "Made" list as Pending
        home_page.goto("/reassignment-requests/made/")
        row = home_page.main_page.locator(
            "tr", has_text=ACCOMMODATION_REQUEST.guest_full_names[0]
        )
        expect(row).to_contain_text("Pending")

        # Confirm it's correctly destined for the receiving LA.
        home_page.click_link(ACCOMMODATION_REQUEST.guest_full_names[0], element=row)
        home_page.assert_has_heading(
            "Request to move guests to a different local authority"
        )
        home_page.assert_page_contains_text(DESTINATION_LA_SEARCH_TEXT)
