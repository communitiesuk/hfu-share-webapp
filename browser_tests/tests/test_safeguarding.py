from dataclasses import dataclass

import pytest

from ..pages import HomePage, SafeguardingPage
from .base import BrowserTest


@dataclass(frozen=True)
class SeededGuest:
    full_name: str
    accommodation_request_title: str
    address: str
    sponsor: str


GUEST_ONE = SeededGuest(
    full_name="Helen Walker and 2 others",
    accommodation_request_title="Helen Walker and 2 others to 6 Luke avenue,, L1 6XL",
    address="6 Luke avenue, Hobbiton",
    sponsor="Colin Khan (alice57@example.org)",
)

GUEST_TWO = SeededGuest(
    full_name="Kirsty Hawkins and 1 other",
    accommodation_request_title="Kirsty Hawkins and 1 other to "
    "Studio 83 Evan, TF57 2UR",
    address="Studio 83 Evans canyon, Hobbiton",
    sponsor="Michael Murphy (hughesjohn@example.org)",
)

GUEST_THREE = SeededGuest(
    full_name="Howard Johnson and 2 others",
    accommodation_request_title="Howard Johnson and 2 others to "
    "8 Fowler trail, PO4X 3EQ",
    address="8 Fowler trail, Hobbiton",
    sponsor="Julian Baker (vwilliams@example.com)",
)

GUEST_FOUR = SeededGuest(
    full_name="Jonathan Greenwood and 1 other",
    accommodation_request_title="Jonathan Greenwood and 1 other to "
    "35 Amelia fiel, L8 1TQ",
    address="35 Amelia field, Hobbiton",
    sponsor="Adrian Gardner (boylemandy@example.org)",
)


GUEST_FIVE = SeededGuest(
    full_name="Eileen Austin",
    accommodation_request_title="Eileen Austin to 76 Helen sprin, B8 3RS",
    address="35 Amelia field, Hobbiton",
    sponsor="June Evans (hporter@example.org)",
)


@pytest.fixture(autouse=True)
def navigate_to_accommidation_request_page(home_page: HomePage):
    home_page.sign_in()

    home_page.click_on_card("Accommodation requests")

    home_page.assert_has_heading("Accommodation requests")


def _navigate_to_add_safeguarding_check(
    safeguarding_page: SafeguardingPage, guest: SeededGuest
):
    safeguarding_page.click_link(guest.accommodation_request_title)

    safeguarding_page.assert_has_heading(
        f"Accommodation request record for {guest.accommodation_request_title}"
    )

    safeguarding_page.assert_summary_list_item("Status", "Checks Required")

    safeguarding_page.click_link("Safeguarding checks")
    safeguarding_page.assert_has_secondary_heading("Safeguarding checks", level=4)

    safeguarding_page.assert_safeguarding_check_completion_check()

    safeguarding_page.click_link("Add safeguarding check")

    safeguarding_page.assert_has_heading(
        f"Accommodation request record for {guest.accommodation_request_title}"
    )

    safeguarding_page.assert_has_secondary_heading("Add safeguarding check", level=3)

    safeguarding_page.assert_fields_are_shown_or_hidden(
        check_type_form_shown=True,
    )

    safeguarding_page.assert_submit_buttons_enabled_or_disabled(
        cancel_link_enabled=True,
    )


class TestSafeguardingAccommodationSuitible(BrowserTest):
    def test_add_not_started_checks_basic_validation_and_navigation(
        self, safeguarding_page: SafeguardingPage
    ):
        _navigate_to_add_safeguarding_check(safeguarding_page, GUEST_ONE)

        safeguarding_page.select_option_for_field(
            "Check type", "Accommodation suitable"
        )

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            accommodations_form_shown=True,
            comments_form_shown=True,
        )

        safeguarding_page.assert_submit_buttons_enabled_or_disabled(
            save_and_return_button_enabled=True,
            save_and_add_button_enabled=True,
            cancel_link_enabled=True,
        )

        safeguarding_page.save_and_return_button.click()

        safeguarding_page.assert_has_heading(
            f"Accommodation request record for {GUEST_ONE.accommodation_request_title}"
        )

        safeguarding_page.assert_has_secondary_heading(
            "Add safeguarding check", level=3
        )

        safeguarding_page.has_the_following_error_messages(
            "Accommodation is required for this check type."
        )
        safeguarding_page.field_has_error_message(
            "Accommodation", "Accommodation is required for this check type."
        )

        safeguarding_page.save_and_add_button.click()

        safeguarding_page.assert_has_heading(
            f"Accommodation request record for {GUEST_ONE.accommodation_request_title}"
        )

        safeguarding_page.assert_has_secondary_heading(
            "Add safeguarding check", level=3
        )

        safeguarding_page.has_the_following_error_messages(
            "Accommodation is required for this check type."
        )
        safeguarding_page.field_has_error_message(
            "Accommodation", "Accommodation is required for this check type."
        )

        safeguarding_page.cancel_link.click()

        safeguarding_page.assert_has_heading(
            f"Accommodation request record for {GUEST_ONE.accommodation_request_title}"
        )
        safeguarding_page.assert_has_secondary_heading("Safeguarding checks", level=4)

    def test_complete_a_passed_safeguarding_check(
        self, safeguarding_page: SafeguardingPage
    ):
        _navigate_to_add_safeguarding_check(safeguarding_page, GUEST_ONE)

        # Accommodation suitable check
        safeguarding_page.select_option_for_field(
            "Check type", "Accommodation suitable"
        )

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            accommodations_form_shown=True,
            comments_form_shown=True,
        )

        safeguarding_page.select_option_for_field("Status", "Passed")

        safeguarding_page.select_option_for_field("Accommodation", GUEST_ONE.address)

        safeguarding_page.save_and_add_button.click()

        safeguarding_page.assert_has_notification(
            "Your changes have been saved", success_banner=True
        )
        safeguarding_page.assert_has_heading(
            f"Accommodation request record for {GUEST_ONE.accommodation_request_title}"
        )
        safeguarding_page.assert_has_secondary_heading(
            "Add safeguarding check", level=3
        )

        safeguarding_page.assert_safeguarding_check_completion_check(
            accommodation_suitable_check=(
                GUEST_ONE.address,
                "Checks complete: Passed",
            )
        )

        # Accommodation exists check
        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
        )

        safeguarding_page.select_option_for_field("Check type", "Accommodation exists")

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            accommodations_form_shown=True,
            comments_form_shown=True,
        )

        safeguarding_page.select_option_for_field("Status", "Passed")

        safeguarding_page.select_option_for_field("Accommodation", GUEST_ONE.address)

        safeguarding_page.save_and_add_button.click()

        safeguarding_page.assert_has_notification(
            "Your changes have been saved", success_banner=True
        )
        safeguarding_page.assert_has_heading(
            f"Accommodation request record for {GUEST_ONE.accommodation_request_title}"
        )
        safeguarding_page.assert_has_secondary_heading(
            "Add safeguarding check", level=3
        )

        safeguarding_page.assert_safeguarding_check_completion_check(
            accommodation_suitable_check=(
                GUEST_ONE.address,
                "Checks complete: Passed",
            ),
            accommodation_exists_check=(
                GUEST_ONE.address,
                "Checks complete: Passed",
            ),
        )

        # DBS check and Sponsor suitable check
        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
        )

        safeguarding_page.select_option_for_field(
            "Check type", "DBS check and Sponsor suitable"
        )

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            sponsors_form_shown=True,
            comments_form_shown=True,
        )

        safeguarding_page.select_option_for_field("Status", "Passed")

        safeguarding_page.select_option_for_field("Sponsor", GUEST_ONE.sponsor)

        safeguarding_page.save_and_add_button.click()

        safeguarding_page.assert_has_notification(
            "Your changes have been saved", success_banner=True
        )
        safeguarding_page.assert_has_heading(
            f"Accommodation request record for {GUEST_ONE.accommodation_request_title}"
        )
        safeguarding_page.assert_has_secondary_heading(
            "Add safeguarding check", level=3
        )

        safeguarding_page.assert_safeguarding_check_completion_check(
            accommodation_suitable_check=(
                GUEST_ONE.address,
                "Checks complete: Passed",
            ),
            accommodation_exists_check=(
                GUEST_ONE.address,
                "Checks complete: Passed",
            ),
            dbs_check=(
                GUEST_ONE.sponsor,
                "Checks complete: Passed",
            ),
        )

        # Guests have arrived in their accommodation
        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
        )

        safeguarding_page.select_option_for_field(
            "Check type", "Guests have arrived in their accommodation"
        )

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            comments_form_shown=True,
        )

        safeguarding_page.select_option_for_field("Status", "Passed")

        safeguarding_page.save_and_return_button.click()

        safeguarding_page.assert_has_notification(
            "Your changes have been saved", success_banner=True
        )
        safeguarding_page.assert_has_heading(
            f"Accommodation request record for {GUEST_ONE.accommodation_request_title}"
        )
        safeguarding_page.assert_has_secondary_heading("Safeguarding checks", level=4)

        safeguarding_page.assert_safeguarding_check_completion_check(
            accommodation_suitable_check=(
                GUEST_ONE.address,
                "Checks complete: Passed",
            ),
            accommodation_exists_check=(
                GUEST_ONE.address,
                "Checks complete: Passed",
            ),
            dbs_check=(
                GUEST_ONE.sponsor,
                "Checks complete: Passed",
            ),
            guests_have_arrived_check=(
                GUEST_ONE.full_name,
                "Edit Guests have arrived in their accommodation check for "
                f"{GUEST_ONE.full_name}",
                "Checks complete: Passed",
            ),
        )

        safeguarding_page.click_link("Overview")
        safeguarding_page.assert_has_secondary_heading("Overview", level=4)

        safeguarding_page.assert_summary_list_item("Status", "Checks Completed")

    def test_move_a_safeguarding_check_to_in_progress(
        self, safeguarding_page: SafeguardingPage
    ):
        _navigate_to_add_safeguarding_check(safeguarding_page, GUEST_TWO)

        # Accommodation suitable check
        safeguarding_page.select_option_for_field(
            "Check type", "Accommodation suitable"
        )

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            accommodations_form_shown=True,
            comments_form_shown=True,
        )

        safeguarding_page.select_option_for_field("Status", "Passed")

        safeguarding_page.select_option_for_field("Accommodation", GUEST_TWO.address)

        safeguarding_page.save_and_return_button.click()

        safeguarding_page.assert_has_notification(
            "Your changes have been saved", success_banner=True
        )
        safeguarding_page.assert_has_heading(
            f"Accommodation request record for {GUEST_TWO.accommodation_request_title}"
        )
        safeguarding_page.assert_has_secondary_heading("Safeguarding checks", level=4)

        safeguarding_page.assert_safeguarding_check_completion_check(
            accommodation_suitable_check=(
                GUEST_TWO.address,
                f"Edit Accommodation suitable check for {GUEST_TWO.address}",
                "Checks complete: Passed",
            ),
        )

        safeguarding_page.click_link("Overview")
        safeguarding_page.assert_has_secondary_heading("Overview", level=4)

        safeguarding_page.assert_summary_list_item(
            "Status", "Checks Partially Completed"
        )

    def test_edit_a_check_and_make_it_failed(self, safeguarding_page: SafeguardingPage):
        safeguarding_page.click_link(GUEST_THREE.accommodation_request_title)

        safeguarding_page.assert_has_heading(
            "Accommodation request record for "
            f"{GUEST_THREE.accommodation_request_title}"
        )

        safeguarding_page.assert_summary_list_item(
            "Status", "Checks Partially Completed"
        )

        safeguarding_page.click_link("Safeguarding checks")
        safeguarding_page.assert_has_secondary_heading("Safeguarding checks", level=4)

        safeguarding_page.assert_safeguarding_check_completion_check(
            accommodation_exists_check=(
                GUEST_THREE.address,
                f"Edit Accommodation exists check for {GUEST_THREE.address}",
                "Checks complete: Passed",
            ),
        )

        safeguarding_page.click_link(
            f"Edit Accommodation exists check for {GUEST_THREE.address}"
        )

        safeguarding_page.assert_has_heading(
            "Accommodation request record for "
            f"{GUEST_THREE.accommodation_request_title}"
        )

        safeguarding_page.assert_has_secondary_heading(
            "Edit safeguarding check", level=3
        )

        safeguarding_page.assert_safeguarding_check_completion_check(
            accommodation_exists_check=(
                GUEST_THREE.address,
                "Checks complete: Passed",
            ),
        )

        safeguarding_page.select_option_for_field("Status", "Failed")

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            accommodation_exists_failure_form_shown=True,
            accommodations_form_shown=True,
            comments_form_shown=True,
        )

        safeguarding_page.select_option_for_field(
            "AR exists Failure reason", "This is not a residential address"
        )

        safeguarding_page.enter_text_into_form_field(
            "Comments", "I think it may be next door"
        )

        safeguarding_page.save_and_return_button.click()

        safeguarding_page.assert_has_notification(
            "Your changes have been saved", success_banner=True
        )
        safeguarding_page.assert_has_heading(
            "Accommodation request record for "
            f"{GUEST_THREE.accommodation_request_title}"
        )
        safeguarding_page.assert_has_secondary_heading("Safeguarding checks", level=4)

        safeguarding_page.assert_safeguarding_check_completion_check(
            accommodation_exists_check=(
                GUEST_THREE.address,
                f"Edit Accommodation exists check for {GUEST_THREE.address}",
                "This is not a residential address",
                "I think it may be next door",
                "Checks complete: Failed",
            ),
        )

        safeguarding_page.click_link("Overview")
        safeguarding_page.assert_has_secondary_heading("Overview", level=4)

        safeguarding_page.assert_summary_list_item("Status", "Some Checks Failed")

    def test_try_adding_existing_check(self, safeguarding_page: SafeguardingPage):
        safeguarding_page.click_link(GUEST_FOUR.accommodation_request_title)

        safeguarding_page.assert_has_heading(
            f"Accommodation request record for {GUEST_FOUR.accommodation_request_title}"
        )

        safeguarding_page.assert_summary_list_item(
            "Status", "Checks Partially Completed"
        )

        safeguarding_page.click_link("Safeguarding checks")
        safeguarding_page.assert_has_secondary_heading("Safeguarding checks", level=4)

        safeguarding_page.assert_safeguarding_check_completion_check(
            accommodation_suitable_check=(
                GUEST_FOUR.address,
                f"Edit Accommodation suitable check for {GUEST_FOUR.address}",
                "Checks complete: Passed",
            ),
        )

        safeguarding_page.click_link("Add safeguarding check")

        safeguarding_page.assert_has_heading(
            f"Accommodation request record for {GUEST_FOUR.accommodation_request_title}"
        )

        safeguarding_page.assert_has_secondary_heading(
            "Add safeguarding check", level=3
        )

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
        )

        safeguarding_page.assert_safeguarding_check_completion_check(
            accommodation_suitable_check=(
                GUEST_FOUR.address,
                "Checks complete: Passed",
            ),
        )

        safeguarding_page.select_option_for_field(
            "Check type", "Accommodation suitable"
        )

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            accommodations_form_shown=True,
            comments_form_shown=True,
        )

        safeguarding_page.select_option_for_field("Status", "Passed")

        safeguarding_page.select_option_for_field("Accommodation", GUEST_FOUR.address)

        safeguarding_page.save_and_add_button.click()

        safeguarding_page.assert_has_heading(
            f"Accommodation request record for {GUEST_FOUR.accommodation_request_title}"
        )

        safeguarding_page.assert_has_secondary_heading(
            "Add safeguarding check", level=3
        )

        safeguarding_page.has_the_following_error_messages(
            "This check already exists. Please edit the existing check instead."
        )

        safeguarding_page.cancel_link.click()

        safeguarding_page.assert_has_heading(
            f"Accommodation request record for {GUEST_FOUR.accommodation_request_title}"
        )
        safeguarding_page.assert_has_secondary_heading("Safeguarding checks", level=4)

    def test_javascript_functionality_accommodation_exists(
        self, safeguarding_page: SafeguardingPage
    ):
        _navigate_to_add_safeguarding_check(safeguarding_page, GUEST_FIVE)

        # Accommodation Exists Failed
        safeguarding_page.select_option_for_field("Check type", "Accommodation exists")

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            accommodations_form_shown=True,
            comments_form_shown=True,
        )

        safeguarding_page.assert_submit_buttons_enabled_or_disabled(
            save_and_return_button_enabled=True,
            save_and_add_button_enabled=True,
            cancel_link_enabled=True,
        )

        safeguarding_page.select_option_for_field("Status", "Failed")

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            accommodation_exists_failure_form_shown=True,
            accommodations_form_shown=True,
            comments_form_shown=True,
        )

        # Accommodation Exists Passed
        safeguarding_page.select_option_for_field("Status", "Passed")

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            accommodations_form_shown=True,
            comments_form_shown=True,
        )

        # Sponsor DBS Passed
        safeguarding_page.select_option_for_field(
            "Check type", "DBS check and Sponsor suitable"
        )

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            sponsors_form_shown=True,
            sponsor_dbs_passed_form_shown=True,
            comments_form_shown=True,
        )

    def test_javascript_functionality_dbs_visibility(
        self, safeguarding_page: SafeguardingPage
    ):
        _navigate_to_add_safeguarding_check(safeguarding_page, GUEST_FIVE)

        # Sponsor DBS Passed
        safeguarding_page.select_option_for_field(
            "Check type", "DBS check and Sponsor suitable"
        )

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            sponsors_form_shown=True,
            comments_form_shown=True,
        )

        # Sponsor DBS No longer required
        safeguarding_page.select_option_for_field("Status", "No longer needed")

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            sponsors_form_shown=True,
            comments_form_shown=True,
        )

        # Sponsor DBS Failed
        safeguarding_page.select_option_for_field("Status", "Failed")

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            sponsor_dbs_failure_form_shown=True,
            sponsors_form_shown=True,
            comments_form_shown=True,
        )

        safeguarding_page.field_has_hint_text(
            "Comments",
            "You can add any reason for the option you selected, if needed. "
            "The text you enter should be short and clear. (optional)",
        )

        # Sponsor DBS Failed - Sponsor not suitable
        safeguarding_page.select_option_for_field(
            "Sponsor DBS Failure reason", "Sponsor is not suitable - other reasons"
        )

        safeguarding_page.field_has_hint_text(
            "Comments",
            "You must add a reason if you select 'Sponsor is not suitable - "
            "other reasons' from the list for UKVI to review the comments. "
            "For any other reason selected adding a comment is optional.",
        )

        safeguarding_page.save_and_return_button.click()

        safeguarding_page.has_the_following_error_messages("You must enter a reason.")
        safeguarding_page.field_has_error_message(
            "Comments", "You must enter a reason."
        )
        safeguarding_page.select_option_for_field(
            "Sponsor DBS Failure reason", "DBS check failed"
        )

        safeguarding_page.field_has_hint_text(
            "Comments",
            "You can add any reason for the option you selected, if needed. "
            "The text you enter should be short and clear. (optional)",
        )

        safeguarding_page.assert_page_has_no_error_messages()
        safeguarding_page.field_has_no_error_message("Comments")

    def test_javascript_functionality_dbs_error_messages(
        self, safeguarding_page: SafeguardingPage
    ):
        _navigate_to_add_safeguarding_check(safeguarding_page, GUEST_FIVE)

        safeguarding_page.select_option_for_field(
            "Check type", "DBS check and Sponsor suitable"
        )

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            sponsors_form_shown=True,
            comments_form_shown=True,
        )

        safeguarding_page.select_option_for_field("Status", "Failed")

        safeguarding_page.assert_fields_are_shown_or_hidden(
            check_type_form_shown=True,
            status_form_shown=True,
            sponsor_dbs_failure_form_shown=True,
            sponsors_form_shown=True,
            comments_form_shown=True,
        )

        safeguarding_page.select_option_for_field(
            "Sponsor DBS Failure reason", "DBS check failed"
        )

        safeguarding_page.field_has_hint_text(
            "Comments",
            "You can add any reason for the option you selected, if needed. "
            "The text you enter should be short and clear. (optional)",
        )

        safeguarding_page.save_and_return_button.click()

        safeguarding_page.has_the_following_error_messages(
            "Sponsor is required for this check type."
        )
        safeguarding_page.field_has_error_message(
            "Sponsor", "Sponsor is required for this check type."
        )

        safeguarding_page.select_option_for_field(
            "Sponsor DBS Failure reason", "Sponsor is not suitable - other reasons"
        )

        safeguarding_page.field_has_hint_text(
            "Comments",
            "You must add a reason if you select 'Sponsor is not suitable - "
            "other reasons' from the list for UKVI to review the comments. "
            "For any other reason selected adding a comment is optional.",
        )

        safeguarding_page.save_and_return_button.click()

        safeguarding_page.has_the_following_error_messages(
            "Sponsor is required for this check type.", "You must enter a reason."
        )

        safeguarding_page.field_has_error_message(
            "Sponsor", "Sponsor is required for this check type."
        )
        safeguarding_page.field_has_error_message(
            "Comments", "You must enter a reason."
        )

        safeguarding_page.select_option_for_field(
            "Sponsor DBS Failure reason",
            "This person has not consented to being a sponsor",
        )

        safeguarding_page.field_has_hint_text(
            "Comments",
            "You can add any reason for the option you selected, if needed. "
            "The text you enter should be short and clear. (optional)",
        )

        safeguarding_page.save_and_return_button.click()

        safeguarding_page.has_the_following_error_messages(
            "Sponsor is required for this check type.",
        )

        safeguarding_page.field_has_error_message(
            "Sponsor", "Sponsor is required for this check type."
        )
        safeguarding_page.field_has_no_error_message("Comments")
