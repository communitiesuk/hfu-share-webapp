import os
from datetime import datetime
from typing import Optional, cast

from playwright.sync_api import Locator, Page, expect

from ..test_users import BrowserTestUser


class SharePage:
    def __init__(self, page: Page, user: BrowserTestUser):
        self.page = page
        self.base_url = cast(str, os.environ.get("BROWSER_TEST_URL")).rstrip("/")
        self.user = user

    def open(self):
        return self.page.goto(self.base_url)

    def goto(self, path: str):
        return self.page.goto(self.base_url + path)

    def sign_in(self):
        self.page.goto(self.base_url)

        self.assert_has_heading_with_status("Sign in", "Status: Entra ID disabled")

        self.enter_text_into_form_field("Email address", self.user.email)
        self.enter_text_into_form_field("Password", self.user.password)

        self.click_button("Sign in")

    def assert_has_heading(self, heading_text: str):
        expect(self.page_heading).to_have_text(heading_text)

    def assert_has_heading_with_status(self, heading_text: str, status_text: str):
        expect(self.page_heading_with_status_heading).to_have_text(heading_text)
        expect(self.page_heading_with_status_status).to_have_text(status_text)

    def assert_has_secondary_heading(self, heading_text: str):
        expect(
            self.find_secondary_page_heading(heading_text=heading_text)
        ).to_be_visible()

    def check_field(self, label: str):
        self.page.get_by_label(label).check()

    def enter_text_into_form_field(self, label: str, text: str):
        self.page.get_by_label(label).fill(text)

    def fill_textarea(self, text):
        self.page.locator("textarea").fill(text)

    def select_radio_option(self, label):
        self.page.get_by_label(label).check()

    def enter_text_into_date_field(self, label: str, date: datetime):
        self.page.get_by_label(label).fill(date.strftime("%d/%m/%Y"))

    def click_button(self, button_text: str):
        self.page.get_by_role("button", name=button_text).click()

    def click_link(self, link_text: str, element: Optional[Locator] = None):
        (self.page if element is None else element).get_by_role(
            "link", name=link_text
        ).click()

    def click_breadcrumb_link(self, link_text: str):
        self.click_link(link_text, element=self.page.locator(".govuk-breadcrumbs"))

    def click_footer_link(self, link_text: str):
        self.click_link(link_text, element=self.page.locator(".govuk-footer"))

    def has_the_following_error_messages(self, *error_messages: str):
        expect(self.error_summary_title).to_have_text("There is a problem")

        for error_summary_element, error_message in zip(
            self.error_summary_items.all(), error_messages, strict=False
        ):
            expect(error_summary_element).to_have_text(error_message)

    def field_has_error_message(
        self, label: str, error_message: str, element: str = "label"
    ):
        expect(self.find_error_message(label, element=element)).to_have_text(
            f"Error: {error_message}"
        )

    def field_has_no_error_message(self, label: str, element: str = "label"):
        expect(self.find_error_message(label, element=element)).to_have_count(0)

    @property
    def page_heading(self) -> Locator:
        return self.page.get_by_role("heading", level=1)

    @property
    def page_heading_with_status_heading(self) -> Locator:
        return self.page_heading.locator("span > span")

    @property
    def page_heading_with_status_status(self) -> Locator:
        return self.page_heading.locator("span > strong")

    def find_secondary_page_heading(self, heading_text: str) -> Locator:
        return self.page.get_by_role("heading", level=2, name=heading_text)

    def assert_page_contains_text(self, text):
        expect(self.page.get_by_text(text).first).to_be_visible()

    @property
    def error_summary_title(self) -> Locator:
        return self.page.locator(".govuk-error-summary__title")

    @property
    def error_summary_items(self) -> Locator:
        return self.page.locator("ul.govuk-error-summary__list > li")

    def find_error_message(self, label: str, element: str = "label") -> Locator:
        return (
            self.page.locator(element, has_text=label)
            .locator("xpath=ancestor::*[contains(@class, 'govuk-form-group--error')]")
            .locator(".govuk-error-message")
        )
