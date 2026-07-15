from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.views import SelectAndReviewRecordsStep
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvUkPostcodeFactory,
)
from user_management.tests.base import get_admin_user


class DeduplicationAccommodationSelectedViewTests(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.first_accommodation = MvAccommodationFactory(
            full_address="[Test] Address 1",
            ltla_name="ltla_somerset",
            utla_name="utla_somerset",
            postcode=MvUkPostcodeFactory(postcode="ABC123"),
            is_principal=True,
        )

        self.second_accommodation = MvAccommodationFactory(
            full_address="[Test] Address 2",
            ltla_name="ltla_somerset",
            utla_name="utla_somerset",
            postcode=MvUkPostcodeFactory(postcode="ABC123"),
            is_principal=True,
        )

    def test_redirects_to_selected_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-accommodation_record": self.first_accommodation.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            response.url,
            "/review-potential-duplicate-records-manual"
            "/accommodations"
            "/deduplicate"
            "/view-selected-records/",
        )

    def test_renders_selected_list_with_correct_layout(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-accommodation_record": self.first_accommodation.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.assertNotContains(response, "View selected records")
        self.assertContains(response, "View selected record")

        self.assertContains(response, "Address")
        self.assertContains(response, "Postcode")
        self.assertContains(response, "Lower tier LA")
        self.assertContains(response, "Upper tier LA")

        self.assertNotContains(response, "You can now review your selected records.")
        self.assertContains(
            response,
            "Select another record from the same lower tier local authority to review.",
        )

        self.assertContains(
            response,
            "<button "
            'class="govuk-button govuk-button--secondary"'
            'name="wizard_goto_step"'
            'type="submit"'
            'value="select-record">'
            "Select another record"
            "</button>",
            html=True,
        )

        self.assertContains(
            response,
            "<button "
            'class="govuk-button"'
            'type="submit"'
            "disabled>"
            "Confirm selection"
            "</button>",
            html=True,
        )

        self.assertContains(
            response,
            "<a "
            'class="govuk-link govuk-link--no-visited-state "'
            "href="
            '"/review-potential-duplicate-records-manual/accommodations/deduplicate/?reset=true">'
            "Cancel"
            "</a>",
            html=True,
        )

    def test_renders_selected_list_with_selected_accommodation_info(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-accommodation_record": self.first_accommodation.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.assertContains(response, self.first_accommodation.full_address)
        self.assertContains(
            response, self.first_accommodation.postcode.postcode_formatted
        )
        self.assertContains(response, self.first_accommodation.ltla_name)
        self.assertContains(response, self.first_accommodation.utla_name)

    def test_select_another_record_button_links_to_select_list_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                },
            ),
            {
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
                "wizard_goto_step": SelectAndReviewRecordsStep.SELECT_RECORD,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/review-potential-duplicate-records-manual"
            "/accommodations"
            "/deduplicate"
            "/select-record/",
        )

    def test_selected_record_does_not_show_on_return_to_select_accommodation_list(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Select a accommodation for dedup
        self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-accommodation_record": self.first_accommodation.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        # Select another record button submission
        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                },
            ),
            {
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
                "wizard_goto_step": SelectAndReviewRecordsStep.SELECT_RECORD,
            },
            follow=True,
        )

        self.assertContains(response, "Select next record")

        self.assertNotContains(response, self.first_accommodation.full_address)

    def test_remove_button_removes_record_from_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-accommodation_record": self.first_accommodation.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.assertContains(response, self.first_accommodation.full_address)

        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                },
            ),
            {
                "review-selected-records-accommodation_record_to_remove": (
                    self.first_accommodation.id
                ),
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertNotContains(response, self.first_accommodation.full_address)

    def test_removing_all_records_renders_conditional_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-accommodation_record": self.first_accommodation.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.assertContains(response, self.first_accommodation.full_address)

        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                },
            ),
            {
                "review-selected-records-accommodation_record_to_remove": (
                    self.first_accommodation.id
                ),
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertNotContains(response, self.first_accommodation.full_address)

        self.assertContains(response, "All selected records have been removed.")

    def test_can_select_and_view_multiple_records(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Select a accommodation for dedup
        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-accommodation_record": self.first_accommodation.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD
                ),
            },
            follow=True,
        )

        self.assertContains(response, "View selected record")
        self.assertContains(
            response,
            "Select another record from the same lower tier local authority to review.",
        )

        # Select another record button submission
        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                },
            ),
            {
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS
                ),
                "wizard_goto_step": SelectAndReviewRecordsStep.SELECT_RECORD,
            },
            follow=True,
        )

        self.assertContains(response, "Select next record")
        self.assertContains(
            response,
            "Select a record to review and deduplicate. "
            "You can use the filter panel to find records.",
        )

        # Select second accommodation for dedup
        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-accommodation_record": [
                    self.first_accommodation.id,
                    self.second_accommodation.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD
                ),
            },
            follow=True,
        )

        # Assert both records are on the page
        self.assertContains(response, self.first_accommodation.full_address)
        self.assertContains(
            response, self.first_accommodation.postcode.postcode_formatted
        )
        self.assertContains(response, self.first_accommodation.ltla_name)
        self.assertContains(response, self.first_accommodation.utla_name)
        self.assertContains(response, "Remove")

        self.assertContains(response, self.second_accommodation.full_address)
        self.assertContains(
            response, self.second_accommodation.postcode.postcode_formatted
        )
        self.assertContains(response, self.second_accommodation.ltla_name)
        self.assertContains(response, self.second_accommodation.utla_name)
        self.assertContains(response, "Remove")

    def test_correct_layout_when_more_than_one_accommodation_selected(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Select a accommodation for dedup
        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-accommodation_record": self.first_accommodation.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD
                ),
            },
            follow=True,
        )

        self.assertContains(response, "View selected record")
        self.assertContains(
            response,
            "Select another record from the same lower tier local authority to review.",
        )

        # Select another record button submission
        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                },
            ),
            {
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS
                ),
                "wizard_goto_step": SelectAndReviewRecordsStep.SELECT_RECORD,
            },
            follow=True,
        )

        self.assertContains(response, "Select next record")
        self.assertContains(
            response,
            "Select a record to review and deduplicate. "
            "You can use the filter panel to find records.",
        )

        # Select second accommodation for dedup
        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-accommodation_record": [
                    self.first_accommodation.id,
                    self.second_accommodation.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD
                ),
            },
            follow=True,
        )

        self.assertContains(response, "View selected records")

        self.assertNotContains(response, "Select another record to review.")
        self.assertContains(response, "You can now review your selected records.")

        self.assertContains(
            response,
            "<button "
            'class="govuk-button govuk-button--secondary"'
            'name="wizard_goto_step"'
            'type="submit"'
            'value="select-record"'
            "disabled>"
            "Select another record"
            "</button>",
            html=True,
        )

        self.assertContains(
            response,
            '<button class="govuk-button" type="submit">Confirm selection</button>',
            html=True,
        )
