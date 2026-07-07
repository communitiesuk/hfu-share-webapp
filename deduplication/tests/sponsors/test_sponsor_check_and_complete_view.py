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
            age=26,
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

        self.step_prefix = "select-correct-details-"

        self.new_principal_sponsor = {
            f"{self.step_prefix}first_name": self.second_sponsor.first_name,
            f"{self.step_prefix}last_name": self.second_sponsor.last_name,
            f"{self.step_prefix}sex": self.second_sponsor.sex,
            f"{self.step_prefix}date_of_birth": (
                self.second_sponsor.date_of_birth.strftime("%-d %B %Y")
            ),
            f"{self.step_prefix}email_address": self.second_sponsor.email,
            f"{self.step_prefix}phone_numbers": self.second_sponsor.phone_number,
            f"{self.step_prefix}residential_postcodes": (
                self.second_sponsor.residential_postcodes
            ),
            f"{self.step_prefix}flag_unsuitable": False,
            "SelectAndReviewRecordsFormWizard-current_step": (
                SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS,
            ),
        }

    def test_redirects_to_check_and_complete_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.second_sponsor.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/review-potential-duplicate-records-manual"
            "/sponsors/deduplicate/view-selected-records/",
        )

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_sponsor.id, self.second_sponsor.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/review-potential-duplicate-records-manual"
            "/sponsors/deduplicate/review-selected-records/",
        )

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_sponsor.id, self.second_sponsor.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/review-potential-duplicate-records-manual"
            "/sponsors/deduplicate/select-correct-details/",
        )

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            ),
            self.new_principal_sponsor,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/review-potential-duplicate-records-manual/sponsors/deduplicate/"
            "check-and-complete/",
        )

    def test_renders_check_and_complete_view_with_correct_layout(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.second_sponsor.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "View selected record")

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_sponsor.id, self.second_sponsor.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Deduplicate selected records")

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_sponsor.id, self.second_sponsor.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Select correct details")

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            ),
            self.new_principal_sponsor,
            follow=True,
        )

        self.assertContains(response, "Check details and complete deduplication")

        self.assertContains(response, "Original records to be deduplicated")
        self.assertContains(response, "Name")
        self.assertContains(response, "Sex")
        self.assertContains(response, "Date of birth")
        self.assertContains(response, "Email address")
        self.assertContains(response, "Phone number")
        self.assertContains(response, "Residential postcode")

        self.assertContains(
            response,
            "Check that the correct details are selected for the new principal record",
        )

        self.assertContains(
            response, "Are you sure you want to complete the deduplication?"
        )
        self.assertContains(
            response,
            "Check that the correct details are selected for the new principal record",
        )

        # self.assertContains(
        #     response,
        #     "This will create a new principal record with the information shown. The "
        #     "original sponsor and host records will be marked as duplicates and you "
        #     "will not be able to change them, unless you first undo the "
        #     "deduplication.",
        # ) TODO: replace below when undo deduplication is re-enabled

        self.assertContains(
            response,
            "This will create a new principal record with the information shown. The "
            "original sponsor and host records will be marked as duplicates and you "
            "will not be able to change them.",
        )

        self.assertContains(
            response,
            '<button class="govuk-button"type="submit">'
            "Yes, confirm and deduplicate"
            "</button>",
            html=True,
        )

        self.assertContains(
            response,
            '<button type="submit"class="govuk-button govuk-button--secondary"'
            'name="wizard_goto_step"type="submit"value="select-correct-details">'
            "No, go back to select correct information"
            "</button>",
            html=True,
        )

    def test_renders_check_and_complete_view_with_correct_sponsor_info(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.second_sponsor.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "View selected record")

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_sponsor.id, self.second_sponsor.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Deduplicate selected records")

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_sponsor.id, self.second_sponsor.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Select correct details")

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            ),
            self.new_principal_sponsor,
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
        self.assertContains(response, self.first_sponsor.residential_postcodes[0])
        self.assertContains(response, "No")

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
        self.assertContains(response, self.second_sponsor.residential_postcodes[0])
        self.assertContains(response, "No")

        self.assertContains(
            response,
            self.new_principal_sponsor[f"{self.step_prefix}first_name"]
            + " "
            + self.new_principal_sponsor[f"{self.step_prefix}last_name"],
        )
        self.assertContains(
            response, self.new_principal_sponsor[f"{self.step_prefix}sex"]
        )
        self.assertContains(
            response,
            datetime.strptime(
                self.new_principal_sponsor[f"{self.step_prefix}date_of_birth"],
                "%d %B %Y",
            ).strftime("%-d %b %Y"),
        )
        self.assertContains(
            response,
            self.new_principal_sponsor[f"{self.step_prefix}email_address"],
        )
        self.assertContains(
            response, self.new_principal_sponsor[f"{self.step_prefix}phone_numbers"][0]
        )
        self.assertContains(
            response,
            self.new_principal_sponsor[f"{self.step_prefix}residential_postcodes"][0],
        )
        self.assertContains(response, "No")

    def test_redirects_to_select_record_with_success_message_on_submission(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.second_sponsor.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "View selected record")

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_sponsor.id, self.second_sponsor.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Deduplicate selected records")

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_sponsor.id, self.second_sponsor.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Select correct details")

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            ),
            self.new_principal_sponsor,
            follow=True,
        )

        self.assertContains(response, "Check details and complete deduplication")

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.CHECK_AND_COMPLETE},
            ),
            {
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.CHECK_AND_COMPLETE,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Fix duplicate sponsor and host records")

        self.assertContains(response, "Success")
        self.assertContains(
            response, "You have deduplicated 2 sponsor and host records"
        )
        self.assertContains(response, "A new principal record has been created for")
        self.assertContains(response, "test2firstname test2lastname")
        # self.assertContains(
        #     response,
        #     "You can undo the deduplication from the "
        #     "principal record in the actions tab.",
        # ) TODO: put back in when undo deduplication is re-enabled

    def test_redirects_to_select_record_with_error_message_if_system_error(self):
        user = get_admin_user()
        self.client.force_login(user)
        # In this example only one sponsor has been used for dedup causing the error

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-sponsor_record": [self.second_sponsor.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "View selected record")

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.second_sponsor.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Deduplicate selected records")

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.second_sponsor.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Select correct details")

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            ),
            self.new_principal_sponsor,
            follow=True,
        )

        self.assertContains(response, "Check details and complete deduplication")

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.CHECK_AND_COMPLETE},
            ),
            {
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.CHECK_AND_COMPLETE,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Fix duplicate sponsor and host records")

        self.assertContains(response, "There is a problem")
        self.assertContains(
            response,
            "The selected records have not been marked as duplicates. "
            "No new principal record was created.",
        )
