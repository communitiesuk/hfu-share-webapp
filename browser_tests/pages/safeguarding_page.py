from typing import Optional, Tuple, cast

from playwright.sync_api import Locator, expect

from .share_page import SharePage

QUESTION_TO_FORM_GROUP = {
    "Check type": "check_type_form_group",
    "Status": "status_form_group",
    "AR exists Failure reason": "accommodation_exists_failure_form_group",
    "AR suitibal Failure reason": "accommodation_suitable_failure_form_group",
    "Sponser DBS Failure reason": "sponsor_dbs_failure_form_group",
    "Accommodation": "accommodations_form_group",
    "Sponsor": "sponsors_form_group",
    "Sponsor DBS type": "sponsor_dbs_passed_form_group",
    "Comments": "comments_form_group",
}


class SafeguardingPage(SharePage):
    def assert_fields_are_shown_or_hidden(
        self,
        check_type_form_shown: bool = False,
        status_form_shown: bool = False,
        accommodation_exists_failure_form_shown: bool = False,
        accommodation_suitable_failure_form_shown: bool = False,
        sponsor_dbs_failure_form_shown: bool = False,
        accommodations_form_shown: bool = False,
        sponsors_form_shown: bool = False,
        sponsor_dbs_passed_form_shown: bool = False,
        comments_form_shown: bool = False,
    ):
        for form_property, is_shown in (
            ("check_type_form_group", check_type_form_shown),
            ("status_form_group", status_form_shown),
            (
                "accommodation_exists_failure_form_group",
                accommodation_exists_failure_form_shown,
            ),
            (
                "accommodation_suitable_failure_form_group",
                accommodation_suitable_failure_form_shown,
            ),
            ("sponsor_dbs_failure_form_group", sponsor_dbs_failure_form_shown),
            ("accommodations_form_group", accommodations_form_shown),
            ("sponsors_form_group", sponsors_form_shown),
            ("sponsor_dbs_passed_form_group", sponsor_dbs_passed_form_shown),
            ("comments_form_group", comments_form_shown),
        ):
            assert (
                self.element_has_class(
                    self._get_locator_property(form_property), "govuk-visually-hidden"
                )
                is not is_shown
            ), f"Expected {form_property} to be {'shown' if is_shown else 'hidden'}"

    def assert_submit_buttons_enabled_or_disabled(
        self,
        save_and_return_button_enabled: bool = False,
        save_and_add_button_enabled: bool = False,
        cancel_link_enabled: bool = False,
    ):
        for button_property, is_enabled in (
            ("save_and_return_button", save_and_return_button_enabled),
            ("save_and_add_button", save_and_add_button_enabled),
            ("cancel_link", cancel_link_enabled),
        ):
            button = self._get_locator_property(button_property)

            if is_enabled:
                expect(button).to_be_enabled()
            else:
                expect(button).to_be_disabled()

    def assert_safeguarding_check_completion_check(
        self,
        accommodation_suitable_check: Optional[Tuple[str, ...]] = None,
        accommodation_exists_check: Optional[Tuple[str, ...]] = None,
        dbs_check: Optional[Tuple[str, ...]] = None,
        guests_have_arrived_check: Optional[Tuple[str, ...]] = None,
    ):
        DEFAULT_VALUE = "Checks not started"

        self.assert_summary_list(
            (
                "Accommodation suitable",
                accommodation_suitable_check
                if accommodation_suitable_check
                else DEFAULT_VALUE,
            ),
            (
                "Accommodation exists",
                accommodation_exists_check
                if accommodation_exists_check
                else DEFAULT_VALUE,
            ),
            (
                "DBS check and Sponsor suitable",
                dbs_check if dbs_check else DEFAULT_VALUE,
            ),
            (
                "Guests have arrived in their accommodation",
                guests_have_arrived_check
                if guests_have_arrived_check
                else DEFAULT_VALUE,
            ),
        )

    def select_option_for_field(self, question, value):
        self._get_locator_property(QUESTION_TO_FORM_GROUP[question]).locator(
            "select"
        ).select_option(value)

    def _get_locator_property(self, attribute: str) -> Locator:
        return cast(Locator, getattr(self, attribute))

    @property
    def check_type_form_group(self) -> Locator:
        return self.main_page.locator("#div_id_check_type")

    @property
    def status_form_group(self) -> Locator:
        return self.main_page.locator("#div_id_status")

    @property
    def accommodation_exists_failure_form_group(self) -> Locator:
        return self.main_page.locator("#div_id_accommodation_exists_failure")

    @property
    def accommodation_suitable_failure_form_group(self) -> Locator:
        return self.main_page.locator("#div_id_accommodation_suitable_failure")

    @property
    def sponsor_dbs_failure_form_group(self) -> Locator:
        return self.main_page.locator("#div_id_sponsor_dbs_failure")

    @property
    def accommodations_form_group(self) -> Locator:
        return self.main_page.locator("#div_id_accommodations")

    @property
    def sponsors_form_group(self) -> Locator:
        return self.main_page.locator("#div_id_sponsors")

    @property
    def sponsor_dbs_passed_form_group(self) -> Locator:
        return self.main_page.locator("#div_id_sponsor_dbs_passed")

    @property
    def comments_form_group(self) -> Locator:
        return self.main_page.locator("#div_id_notes")

    @property
    def save_and_return_button(self) -> Locator:
        return self.main_page.get_by_role(
            "button", name="Submit and return to safeguarding checks"
        )

    @property
    def save_and_add_button(self) -> Locator:
        return self.main_page.get_by_role("button", name="Save and add another check")

    @property
    def cancel_link(self) -> Locator:
        return self.main_page.get_by_role("link", name="Cancel")
