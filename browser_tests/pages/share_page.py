import os
from datetime import datetime
from typing import Optional, Tuple, cast

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

        # This fixes an issue when running the tests locally
        # It will close the config panel that is restricting visibility of links
        self.close_django_tool_bar()

        self.assert_has_heading_with_status("Sign in", "Status: Entra ID disabled")

        self.enter_text_into_form_field("Email address", self.user.email)
        self.enter_text_into_form_field("Password", self.user.password)

        self.click_button("Sign in")

    def close_django_tool_bar(self):
        close_button = self.page.locator("#djHideToolBarButton")

        if close_button.is_visible():
            close_button.click()

    def assert_has_heading(self, heading_text: str):
        expect(self.page_heading).to_have_text(heading_text)

    def assert_has_heading_with_status(self, heading_text: str, status_text: str):
        expect(self.page_heading_with_status_heading).to_have_text(heading_text)
        expect(self.page_heading_with_status_status).to_have_text(status_text)

    def assert_has_secondary_heading(self, heading_text: str, level: int = 2):
        expect(
            self.find_secondary_page_heading(heading_text=heading_text, level=level)
        ).to_be_visible()

    def assert_summary_list(
        self, *summary_list_items: Tuple[str, str | Tuple[str, ...]]
    ):
        for row, (summary_list_key, summary_list_values) in zip(
            self.summary_list_rows.all(), summary_list_items, strict=True
        ):
            expect(row.locator("dt.govuk-summary-list__key")).to_have_text(
                summary_list_key
            )

            if isinstance(summary_list_values, str):
                expect(row.locator("dd.govuk-summary-list__value")).to_have_text(
                    summary_list_values
                )
            else:
                for summary_list_value in summary_list_values:
                    expect(row.locator("dd.govuk-summary-list__value")).to_contain_text(
                        summary_list_value
                    )

    def assert_summary_list_item(self, summary_list_key: str, summary_list_value: str):
        expect(self.find_summary_list_value_for_row(summary_list_key)).to_have_text(
            summary_list_value
        )

    def assert_has_notification(
        self, notification_text: str, success_banner: bool = False
    ):
        if success_banner:
            self.assert_element_has_class(
                self.notification_banner, "govuk-notification-banner--success"
            )

        expect(
            self.notification_banner.locator("div.govuk-notification-banner__content")
        ).to_have_text(notification_text)

    def element_has_class(self, element: Locator, class_name: str) -> bool:
        return class_name in (element.get_attribute("class") or "").split()

    def assert_element_has_class(self, element: Locator, class_name: str):
        assert self.element_has_class(element, class_name)

    def assert_element_does_not_have_class(self, element: Locator, class_name: str):
        assert self.element_has_class(element, class_name) is False

    def check_field(self, label: str):
        self.main_page.get_by_label(label).check()

    def enter_text_into_form_field(self, label: str, text: str):
        self.main_page.get_by_label(label).fill(text)

    def enter_text_into_date_field(self, label: str, date: datetime):
        self.main_page.get_by_label(label).fill(date.strftime("%d/%m/%Y"))

    def click_button(self, button_text: str):
        self.main_page.get_by_role("button", name=button_text).click()

    def click_link(self, link_text: str, element: Optional[Locator] = None):
        (self.main_page if element is None else element).get_by_role(
            "link", name=link_text
        ).click()

    def click_breadcrumb_link(self, link_text: str):
        self.click_link(link_text, element=self.page.locator(".govuk-breadcrumbs"))

    def click_footer_link(self, link_text: str):
        self.click_link(link_text, element=self.page.locator(".govuk-footer"))

    def field_has_hint_text(self, label: str, hint_text: str, element: str = "label"):
        expect(self.find_hint_text(label, element=element)).to_have_text(hint_text)

    def has_the_following_error_messages(self, *error_messages: str):
        expect(self.error_summary_title).to_have_text("There is a problem")

        for error_summary_element, error_message in zip(
            self.error_summary_items.all(), error_messages, strict=False
        ):
            expect(error_summary_element).to_have_text(error_message)

    def assert_page_has_no_error_messages(self):
        expect(self.error_summary_title).not_to_be_visible()

    def field_has_error_message(
        self, label: str, error_message: str, element: str = "label"
    ):
        expect(self.find_error_message(label, element=element)).to_have_text(
            f"Error: {error_message}"
        )

    def field_has_no_error_message(self, label: str, element: str = "label"):
        expect(self.find_error_message(label, element=element)).to_have_count(0)

    @property
    def main_page(self) -> Locator:
        return self.page.locator("main#main-content")

    @property
    def page_heading(self) -> Locator:
        return self.main_page.get_by_role("heading", level=1)

    @property
    def page_heading_with_status_heading(self) -> Locator:
        return self.page_heading.locator("span > span")

    @property
    def page_heading_with_status_status(self) -> Locator:
        return self.page_heading.locator("span > strong")

    def find_secondary_page_heading(self, heading_text: str, level: int = 2) -> Locator:
        return self.main_page.get_by_role("heading", level=level, name=heading_text)

    def assert_page_contains_text(self, text: str):
        expect(self.page.get_by_text(text).first).to_be_visible()

    def find_hint_text(self, label: str, element: str = "label") -> Locator:
        return (
            self.main_page.locator(element, has_text=label)
            .locator("xpath=ancestor::*[contains(@class, 'govuk-form-group')]")
            .locator(".govuk-hint:not(.govuk-character-count__message)")
        )

    @property
    def error_summary_title(self) -> Locator:
        return self.main_page.locator(".govuk-error-summary__title")

    @property
    def error_summary_items(self) -> Locator:
        return self.main_page.locator("ul.govuk-error-summary__list > li")

    def find_error_message(self, label: str, element: str = "label") -> Locator:
        return (
            self.main_page.locator(element, has_text=label)
            .locator("xpath=ancestor::*[contains(@class, 'govuk-form-group--error')]")
            .locator(".govuk-error-message")
        )

    @property
    def summary_list_rows(self) -> Locator:
        return self.main_page.locator(
            "dl.govuk-summary-list > div.govuk-summary-list__row"
        )

    def find_summary_list_value_for_row(self, summary_list_key: str) -> Locator:
        return self.main_page.locator(
            "dt.govuk-summary-list__key", has_text=summary_list_key
        ).locator('xpath=../dd[@class="govuk-summary-list__value"]')

    @property
    def notification_banner(self) -> Locator:
        return self.main_page.locator("div.govuk-notification-banner")
