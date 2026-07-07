from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.views import SelectAndReviewRecordsStep
from ontology.models import MvVolunteer
from ontology.tests.factories import MvVolunteerFactory
from user_management.tests.base import get_admin_user


class DeduplicationSponsorSelectedViewTests(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.first_sponsor = MvVolunteerFactory(
            first_name="testfirstname",
            last_name="testlastname",
            sex="Female",
            date_of_birth=datetime(1999, 11, 11, tzinfo=timezone.utc),
            email="test@example.com",
            phone_number=["01134960698"],
            residential_postcodes=["OX1 1OX"],
            flag_unsuitable=False,
            is_principal=True,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

        self.second_sponsor = MvVolunteerFactory(
            first_name="test2firstname",
            last_name="test2lastname",
            sex="Male",
            date_of_birth=datetime(1981, 6, 10, tzinfo=timezone.utc),
            email="test2@example.com",
            phone_number=["04467123455"],
            residential_postcodes=["NW1 1WN"],
            flag_unsuitable=False,
            is_principal=True,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

    def test_redirects_to_selected_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-sponsor_record": self.first_sponsor.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            response.url,
            "/review-potential-duplicate-records-manual"
            "/sponsors"
            "/deduplicate"
            "/view-selected-records/",
        )

    def test_renders_selected_list_with_correct_layout(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-sponsor_record": self.first_sponsor.id,
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
        self.assertContains(response, "Email address")
        self.assertContains(response, "Phone number")
        self.assertContains(response, "EOI host")
        self.assertContains(response, "Date added")
        self.assertContains(response, "False")

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
            "href="
            '"/review-potential-duplicate-records-manual/sponsors/deduplicate/?reset=true">'
            "Cancel"
            "</a>",
            html=True,
        )

    def test_renders_selected_list_with_selected_sponsor_info(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-sponsor_record": self.first_sponsor.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.assertContains(
            response,
            self.first_sponsor.first_name + " " + self.first_sponsor.last_name,
        )
        self.assertContains(response, self.first_sponsor.sex)
        self.assertContains(
            response, self.first_sponsor.date_of_birth.strftime("%d %b %Y")
        )
        self.assertContains(response, self.first_sponsor.email)
        self.assertContains(response, self.first_sponsor.phone_number[0])
        self.assertContains(response, "False")
        self.assertContains(response, "Remove")

    def test_select_another_record_button_links_to_select_list_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
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
            "/sponsors"
            "/deduplicate"
            "/select-record/",
        )

    def test_selected_record_does_not_show_on_return_to_select_sponsor_list(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Select a sponsor for dedup
        self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-sponsor_record": self.first_sponsor.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        # Select another record button submission
        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
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

        self.assertNotContains(
            response,
            self.first_sponsor.first_name + " " + self.first_sponsor.last_name,
        )

    def test_remove_button_removes_record_from_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-sponsor_record": self.first_sponsor.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.assertContains(
            response,
            self.first_sponsor.first_name + " " + self.first_sponsor.last_name,
        )

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                },
            ),
            {
                "review-selected-records-sponsor_record_to_remove": (
                    self.first_sponsor.id
                ),
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertNotContains(
            response,
            self.first_sponsor.first_name + " " + self.first_sponsor.last_name,
        )

    def test_removing_all_records_renders_conditional_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-sponsor_record": self.first_sponsor.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.assertContains(
            response,
            self.first_sponsor.first_name + " " + self.first_sponsor.last_name,
        )

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                },
            ),
            {
                "review-selected-records-sponsor_record_to_remove": (
                    self.first_sponsor.id
                ),
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertNotContains(
            response,
            self.first_sponsor.first_name + " " + self.first_sponsor.last_name,
        )

        self.assertContains(response, "All selected records have been removed.")

    def test_can_select_and_view_multiple_records(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Select a sponsor for dedup
        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-sponsor_record": self.first_sponsor.id,
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
                "deduplication:sponsors:select-and-review-records-manual-step",
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

        # Select a second sponsor for dedup
        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.second_sponsor.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD
                ),
            },
            follow=True,
        )

        # Assert both records are on the page
        self.assertContains(
            response,
            self.first_sponsor.first_name + " " + self.first_sponsor.last_name,
        )
        self.assertContains(response, self.first_sponsor.sex)
        self.assertContains(
            response, self.first_sponsor.date_of_birth.strftime("%d %b %Y")
        )
        self.assertContains(response, self.first_sponsor.email)
        self.assertContains(response, self.first_sponsor.phone_number[0])
        self.assertContains(response, "False")
        self.assertContains(response, "Remove")

        self.assertContains(
            response,
            self.second_sponsor.first_name + " " + self.second_sponsor.last_name,
        )
        self.assertContains(response, self.second_sponsor.sex)
        self.assertContains(
            response, self.second_sponsor.date_of_birth.strftime("%d %b %Y")
        )
        self.assertContains(response, self.second_sponsor.email)
        self.assertContains(response, self.second_sponsor.phone_number[0])
        self.assertContains(response, "False")
        self.assertContains(response, "Remove")

    def test_correct_layout_when_more_than_one_sponsor_selected(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Select a sponsor for dedup
        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-sponsor_record": self.first_sponsor.id,
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
                "deduplication:sponsors:select-and-review-records-manual-step",
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

        # Select a second sponsor for dedup
        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.second_sponsor.id,
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
        self.assertContains(response, "You can now review the selected records.")

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
