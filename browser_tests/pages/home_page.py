from .share_page import SharePage


class HomePage(SharePage):
    def click_on_card(self, card_text):
        self.main_page.get_by_role("heading", level=3, name=card_text).click()
