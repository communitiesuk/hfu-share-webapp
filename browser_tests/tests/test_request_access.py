from .base import BrowserTest


class TestRequestAccessJourney(BrowserTest):
    def test_request_access_journey_and_pending_status(self, home_page):
        home_page.goto_path("/request-access/intro")
        home_page.assert_has_heading("Request access to data")

        home_page.click_button("Start")
        home_page.assert_has_heading("Select user group")

        home_page.select_radio_option("Home Office operations team")
        home_page.click_button("Next")
        home_page.assert_has_heading("Tell us why you need access")

        home_page.fill_textarea("Browser testing")
        home_page.click_button("Next")
        home_page.assert_has_heading("Check your answers")

        home_page.click_button("Confirm and submit")
        home_page.assert_has_heading("Request submitted")

        home_page.click_link("Return to homepage")
        home_page.assert_has_heading("Welcome")
        home_page.assert_page_contains_text("Pending requests")

        home_page.click_link("Home Office")
        home_page.assert_has_heading("Your request")

        home_page.assert_page_contains_text("Request date")
        home_page.assert_page_contains_text("Name")
        home_page.assert_page_contains_text("User group")
        home_page.assert_page_contains_text("Home Office operations team")
        home_page.assert_page_contains_text("Tell us why access is needed")
        home_page.assert_page_contains_text("Browser testing")
