import os

from playwright.sync_api import Page, expect


class SharePage:
    def __init__(self, page: Page):
        self.page = page
        self.base_url = os.environ.get("BROWSER_TEST_URL")
        self.user_email = os.environ.get("BROWSER_TEST_USER_EMAIL")
        self.user_password = os.environ.get("BROWSER_TEST_USER_PASSWORD")

    def open(self):
        self.page.goto(self.base_url)

    def sign_in(self):
        self.page.goto(self.base_url)

        self.assert_has_heading_with_status("Sign in", "Status: Entra ID disabled")

        self.enter_text_into_form_field("Email address", self.user_email)
        self.enter_text_into_form_field("Password", self.user_password)

        self.click_button("Sign in")

    def assert_has_heading(self, heading_text):
        expect(self._page_heading).to_have_text(heading_text)

    def assert_has_heading_with_status(self, heading_text, status_text):
        expect(self._page_heading_with_status_heading).to_have_text(heading_text)
        expect(self._page_heading_with_status_status).to_have_text(status_text)

    def assert_has_secondary_heading(self, heading_text):
        expect(
            self.find_secondary_page_heading(heading_text=heading_text)
        ).to_be_visible()

    def enter_text_into_form_field(self, label, text):
        self.page.get_by_label(label).fill(text)

    def click_button(self, button_text):
        self.page.get_by_role("button", name=button_text).click()

    def click_link(self, link_text, element=None):
        (self.page if element is None else element).get_by_role(
            "link", name=link_text
        ).click()

    def click_breadcrumb_link(self, link_text):
        self.click_link(link_text, element=self.page.locator(".govuk-breadcrumbs"))

    def click_footer_link(self, link_text):
        self.click_link(link_text, element=self.page.locator(".govuk-footer"))

    @property
    def _page_heading(self):
        return self.page.get_by_role("heading", level=1)

    @property
    def _page_heading_with_status_heading(self):
        return self._page_heading.locator("span > span")

    @property
    def _page_heading_with_status_status(self):
        return self._page_heading.locator("span > strong")

    def find_secondary_page_heading(self, heading_text):
        return self.page.get_by_role("heading", level=2, name=heading_text)
