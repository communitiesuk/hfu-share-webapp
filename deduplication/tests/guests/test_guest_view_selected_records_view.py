import datetime

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.views import SelectAndReviewRecordsStep
from ontology.tests.factories import MvPersonFactory
from user_management.tests.base import get_admin_user


class DeduplicationSponsorSelectedViewTests(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.first_guest = MvPersonFactory(
            first_name="test1firstname",
            last_name="test1lastname",
            gender="Female",
            date_of_birth=datetime.date(1999, 1, 1),
            passport_id=["XX88888"],
            visa_status="Arrived",
            arrival_date=datetime.date(2025, 12, 10),
            visa_application_date_maximum=datetime.date(2030, 6, 20),
            application_number=["4242-4242-4242-4242"],
            is_principal=True,
        )

        self.second_guest = MvPersonFactory(
            first_name="test2firstname",
            last_name="test2lastname",
            gender="Female",
            date_of_birth=datetime.date(1989, 6, 6),
            passport_id=["XX88888"],
            visa_status="Arrived",
            arrival_date=datetime.date(2035, 9, 19),
            visa_application_date_maximum=datetime.date(2032, 3, 3),
            application_number=["9999-9999-9999-9999"],
            is_principal=True,
        )

    def test_redirects_to_selected_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-guest_record": self.first_guest.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            response.url,
            "/review-potential-duplicate-records-manual"
            "/guests/deduplicate/view-selected-records/",
        )

    def test_renders_selected_list_with_correct_layout(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-guest_record": self.first_guest.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.assertNotContains(response, "View selected records")
        self.assertContains(response, "View selected record")

        self.assertContains(response, "Name")
        self.assertContains(response, "Sex")
        self.assertContains(response, "Date of birth")
        self.assertContains(response, "Passport number")
        self.assertContains(response, "Visa status")
        self.assertContains(response, "First arrival date")
        self.assertContains(response, "Latest visa application date")
        self.assertContains(response, "Unique Application Number (UAN)")

        self.assertNotContains(response, "You can now review the selected records.")
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
            'href="/review-potential-duplicate-records-manual/'
            'guests/deduplicate/?reset=true">'
            "Cancel"
            "</a>",
            html=True,
        )

    def test_renders_selected_list_with_selected_guest_info(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-guest_record": self.first_guest.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.assertContains(response, self.first_guest.get_full_name())
        self.assertContains(response, self.first_guest.gender)
        self.assertContains(
            response, self.first_guest.date_of_birth.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.first_guest.passport_id[0])
        self.assertContains(response, self.first_guest.visa_status)
        self.assertContains(
            response, self.first_guest.arrival_date.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.first_guest.visa_status)
        self.assertContains(
            response,
            self.first_guest.visa_application_date_maximum.strftime("%-d %b %Y"),
        )
        self.assertContains(response, self.first_guest.application_number[0])

    def test_select_another_record_button_links_to_select_list_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
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
            "/review-potential-duplicate-records-manual/guests/deduplicate/select-record/",
        )

    def test_selected_record_does_not_show_on_return_to_select_guest_list(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Select a guest for dedup
        self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-guest_record": self.first_guest.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        # Select another record button submission
        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
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

        self.assertNotContains(response, self.first_guest.get_full_name())

    def test_remove_button_removes_record_from_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-guest_record": self.first_guest.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.assertContains(response, self.first_guest.get_full_name())

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                },
            ),
            {
                "review-selected-records-guest_record_to_remove": (self.first_guest.id),
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertNotContains(response, self.first_guest.get_full_name())

    def test_removing_all_records_renders_conditional_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-guest_record": self.first_guest.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.assertContains(response, self.first_guest.get_full_name())

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                },
            ),
            {
                "review-selected-records-guest_record_to_remove": (self.first_guest.id),
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertNotContains(response, self.first_guest.get_full_name())

        self.assertContains(response, "All selected records have been removed.")

    def test_can_select_and_view_multiple_records(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Select a guest for dedup
        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-guest_record": self.first_guest.id,
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
                "deduplication:guests:select-and-review-records-manual-step",
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

        # Select a second guest for dedup
        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.second_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD
                ),
            },
            follow=True,
        )

        # Assert both records are on the page
        self.assertContains(response, self.first_guest.get_full_name())
        self.assertContains(response, self.first_guest.gender)
        self.assertContains(
            response, self.first_guest.date_of_birth.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.first_guest.passport_id[0])
        self.assertContains(response, self.first_guest.visa_status)
        self.assertContains(
            response, self.first_guest.arrival_date.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.first_guest.visa_status)
        self.assertContains(
            response,
            self.first_guest.visa_application_date_maximum.strftime("%-d %b %Y"),
        )
        self.assertContains(response, self.first_guest.application_number[0])

        self.assertContains(response, self.second_guest.get_full_name())
        self.assertContains(response, self.second_guest.gender)
        self.assertContains(
            response, self.second_guest.date_of_birth.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.second_guest.passport_id[0])
        self.assertContains(response, self.second_guest.visa_status)
        self.assertContains(
            response, self.second_guest.arrival_date.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.second_guest.visa_status)
        self.assertContains(
            response,
            self.second_guest.visa_application_date_maximum.strftime("%-d %b %Y"),
        )
        self.assertContains(response, self.second_guest.application_number[0])

    def test_correct_layout_when_more_than_one_guest_selected(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Select a guest for dedup
        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-guest_record": self.first_guest.id,
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
                "deduplication:guests:select-and-review-records-manual-step",
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

        # Select a second guest for dedup
        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.second_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD
                ),
            },
            follow=True,
        )

        self.assertContains(response, "View selected records")

        self.assertNotContains(
            response,
            "Select another record from the same lower tier local authority to review.",
        )
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
