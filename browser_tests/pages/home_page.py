from .share_page import SharePage


class HomePage(SharePage):
    # TODO: Replace when we have the card updated
    def click_on_card(self, card_text):
        self.page.get_by_role("heading", level=3, name=card_text).locator(
            "xpath=../../../../a"
        ).click()
