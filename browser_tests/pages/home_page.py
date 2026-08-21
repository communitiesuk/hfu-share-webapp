from .share_page import SharePage


class HomePage(SharePage):
    # TODO: Replace when we have the card updated HFURB-3979
    def click_on_card(self, card_text):
        self.main_page.get_by_role("heading", level=3, name=card_text).locator(
            "xpath=../../../../a"
        ).click()
