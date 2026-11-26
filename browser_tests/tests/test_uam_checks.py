import pytest

from ..pages import HomePage
from ..seeded_data import SeededUam
from .base import BrowserTest

UAM_WAITING_FOR_LA_CHECKS = SeededUam(
    reference="browser-test-uam-00002",
    sponsor_full_name="Kayleigh Jones",
)
RECORD_HEADING = (
    "Application to sponsor a child record for "
    f"{UAM_WAITING_FOR_LA_CHECKS.sponsor_full_name}"
)
LA_CHECKS = (
    "Sponsor and household members enhanced DBS",
    "Accommodation exists",
    "Accommodation suitable",
    "Sponsor role and expectations",
    "Sponsor arrangements suitable",
)


@pytest.fixture
def uam_checks_page(home_page: HomePage) -> HomePage:
    home_page.sign_in()
    home_page.click_on_card("Applications to sponsor a child")
    home_page.assert_has_heading("Applications to sponsor a child")

    home_page.click_link(UAM_WAITING_FOR_LA_CHECKS.sponsor_full_name)
    home_page.assert_has_heading(RECORD_HEADING)

    home_page.click_record_tab("Checks")
    home_page.assert_has_secondary_heading("Local authority checks")

    return home_page


class TestUamChecksJourney(BrowserTest):
    def test_mark_all_la_checks_as_passed_and_code_as_sent(
        self, uam_checks_page: HomePage
    ):
        for check in LA_CHECKS:
            uam_checks_page.click_link(check)
            uam_checks_page.check_field("Passed")
            uam_checks_page.click_button("Save check")

        uam_checks_page.click_link("Code sent to sponsor")
        uam_checks_page.check_field("Sponsor certification code emailed to sponsor.")
        uam_checks_page.click_button("Save check")

        uam_checks_page.click_record_tab("Overview")
        uam_checks_page.assert_summary_list_item(
            "Sponsor suitability checks status", "Completed"
        )
