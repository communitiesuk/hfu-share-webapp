from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.views import SelectAndReviewRecordsStep
from ontology.tests.factories import MvAccommodationRequestFactory, MvPersonFactory
from user_management.tests.base import get_admin_user


class DeduplicationGuestSelectedViewTests(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.first_guest = MvPersonFactory(
            first_name="test1firstname",
            last_name="test1lastname",
            gender="Female",
            date_of_birth=datetime(1999, 1, 1, tzinfo=timezone.utc),
            email=["test1@example.com"],
            phone=["07777777777"],
            passport_id=["XX88888"],
            visa_status="Issued",
            arrival_date=datetime(2025, 12, 10, tzinfo=timezone.utc),
            visa_application_date_maximum=datetime(2030, 6, 20, tzinfo=timezone.utc),
            application_number=["4242-4242-4242-4242"],
            is_principal=True,
        )

        self.second_guest = MvPersonFactory(
            first_name="test2firstname",
            last_name="test2lastname",
            gender="Male",
            date_of_birth=datetime(1989, 6, 6, tzinfo=timezone.utc),
            email=["test2@example.com"],
            phone=["07888888888"],
            passport_id=["XX99999"],
            visa_status="Pending",
            arrival_date=datetime(2035, 9, 19, tzinfo=timezone.utc),
            visa_application_date_maximum=datetime(2032, 3, 3, tzinfo=timezone.utc),
            application_number=["9999-9999-9999-9999"],
            is_principal=True,
        )

        self.multi_uan = MvPersonFactory(
            first_name="test3firstname",
            last_name="test3lastname",
            gender="Male",
            date_of_birth=datetime(1995, 6, 6, tzinfo=timezone.utc),
            email=["test3@example.com"],
            phone=["07999999999"],
            passport_id=["XX00000"],
            visa_status="Arrived",
            arrival_date=datetime(2032, 9, 19, tzinfo=timezone.utc),
            visa_application_date_maximum=datetime(2033, 3, 3, tzinfo=timezone.utc),
            application_number=["0000-0000-0000-0000", "1111-1111-1111-1111"],
            is_principal=True,
        )

        self.diff_ar_guest = MvPersonFactory(
            is_principal=True,
        )

        self.accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[self.first_guest.pk, self.second_guest.pk, self.multi_uan.pk],
            checks_status="Checks Required",
        )
        self.accommodation_request_one.save()

        self.first_guest.accommodation_request = self.accommodation_request_one
        self.second_guest.accommodation_request = self.accommodation_request_one
        self.multi_uan.accommodation_request = self.accommodation_request_one
        self.first_guest.save()
        self.second_guest.save()
        self.multi_uan.save()

        self.accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[self.diff_ar_guest.pk],
            checks_status="Checks Required",
        )
        self.diff_ar_guest.accommodation_request = self.accommodation_request_two
        self.diff_ar_guest.save()

        self.step_prefix = "select-correct-details-"

        self.new_principal_guest = {
            f"{self.step_prefix}first_name": self.first_guest.first_name,
            f"{self.step_prefix}last_name": self.first_guest.last_name,
            f"{self.step_prefix}sex": self.first_guest.gender,
            f"{self.step_prefix}date_of_birth": (
                self.first_guest.date_of_birth.strftime("%-d %B %Y")
            ),
            f"{self.step_prefix}email_address": [self.first_guest.email[0]],
            f"{self.step_prefix}phone_numbers": [self.first_guest.phone[0]],
            f"{self.step_prefix}passport_number": (self.first_guest.passport_id[0]),
            f"{self.step_prefix}application_number": [
                self.first_guest.application_number
            ],
            f"{self.step_prefix}visa_status": self.first_guest.visa_status,
            "SelectAndReviewRecordsFormWizard-current_step": (
                SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS,
            ),
        }

        self.new_principal_multi_uan_guest = {
            f"{self.step_prefix}first_name": self.first_guest.first_name,
            f"{self.step_prefix}last_name": self.first_guest.last_name,
            f"{self.step_prefix}sex": self.first_guest.gender,
            f"{self.step_prefix}date_of_birth": (
                f"{self.first_guest.date_of_birth.strftime('%-d %B %Y')}"
            ),
            f"{self.step_prefix}email_address": [self.first_guest.email[0]],
            f"{self.step_prefix}phone_numbers": [self.first_guest.phone[0]],
            f"{self.step_prefix}passport_number": (self.first_guest.passport_id[0]),
            f"{self.step_prefix}application_number": [
                self.first_guest.application_number,
                self.multi_uan.application_number[0],
                self.multi_uan.application_number[1],
            ],
            f"{self.step_prefix}visa_status": self.multi_uan.visa_status,
            "SelectAndReviewRecordsFormWizard-current_step": (
                SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS,
            ),
        }

    def test_redirects_to_check_and_complete_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.second_guest.id,
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
            "/guests/deduplicate/view-selected-records/",
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id, self.second_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/review-potential-duplicate-records-manual"
            "/guests/deduplicate/review-selected-records/",
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id, self.second_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/review-potential-duplicate-records-manual"
            "/guests/deduplicate/select-correct-details/",
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            ),
            self.new_principal_guest,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/review-potential-duplicate-records-manual/guests/deduplicate/"
            "check-and-complete/",
        )

    def test_renders_check_and_complete_view_with_correct_layout(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.second_guest.id,
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
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id, self.second_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Deduplicate selected records")

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id, self.second_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Select correct details")

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            ),
            self.new_principal_guest,
            follow=True,
        )

        self.assertContains(response, "Check details and complete deduplication")

        self.assertContains(response, "Name")
        self.assertContains(response, "Sex")
        self.assertContains(response, "Date of birth")
        self.assertContains(response, "Email address")
        self.assertContains(response, "Phone number")
        self.assertContains(response, "Passport number")
        self.assertContains(response, "Visa status")
        self.assertContains(response, "Unique Application Number (UAN)")
        self.assertContains(response, "Accommodation request")

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

        self.assertContains(
            response,
            "This will create a new principal record with the information shown. The "
            "original guest records will be marked as duplicates and you "
            "will not be able to change them, unless you first undo the "
            "deduplication.",
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

    def test_renders_check_and_complete_view_with_correct_guest_info(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.second_guest.id,
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
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id, self.second_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Deduplicate selected records")

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id, self.second_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Select correct details")

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            ),
            self.new_principal_guest,
            follow=True,
        )

        self.assertContains(
            response, f"{self.first_guest.first_name} {self.first_guest.last_name}"
        )
        self.assertContains(response, self.first_guest.gender)
        self.assertContains(
            response, self.first_guest.date_of_birth.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.first_guest.email[0])
        self.assertContains(response, self.first_guest.phone[0])
        self.assertContains(response, self.first_guest.passport_id[0])
        self.assertContains(response, self.first_guest.visa_status)
        self.assertContains(response, self.first_guest.application_number[0])
        self.assertContains(response, self.accommodation_request_one.title)

        self.assertContains(
            response, f"{self.second_guest.first_name} {self.second_guest.last_name}"
        )
        self.assertContains(response, self.second_guest.gender)
        self.assertContains(
            response, self.second_guest.date_of_birth.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.second_guest.email[0])
        self.assertContains(response, self.second_guest.phone[0])
        self.assertContains(response, self.second_guest.passport_id[0])
        self.assertContains(response, self.second_guest.visa_status)
        self.assertContains(response, self.accommodation_request_one.title)

        self.assertContains(
            response,
            self.new_principal_guest[f"{self.step_prefix}first_name"]
            + " "
            + self.new_principal_guest[f"{self.step_prefix}last_name"],
        )
        self.assertContains(
            response, self.new_principal_guest[f"{self.step_prefix}sex"]
        )
        self.assertContains(
            response,
            datetime.strptime(
                self.new_principal_guest[f"{self.step_prefix}date_of_birth"], "%d %B %Y"
            ).strftime("%-d %b %Y"),
        )
        self.assertContains(
            response,
            self.new_principal_guest[f"{self.step_prefix}email_address"][0],
        )
        self.assertContains(
            response, self.new_principal_guest[f"{self.step_prefix}phone_numbers"][0]
        )
        self.assertContains(
            response,
            self.new_principal_guest[f"{self.step_prefix}passport_number"][0],
        )
        self.assertContains(response, "Pending")
        self.assertContains(response, self.first_guest.visa_status)
        self.assertContains(response, self.second_guest.visa_status)
        self.assertContains(response, self.first_guest.application_number[0])
        self.assertContains(response, self.second_guest.application_number[0])

    def test_redirects_to_select_record_with_success_message_on_submission(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.second_guest.id,
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
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id, self.second_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Deduplicate selected records")

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id, self.second_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Select correct details")

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            ),
            self.new_principal_guest,
            follow=True,
        )

        self.assertContains(response, "Check details and complete deduplication")

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.CHECK_AND_COMPLETE},
            ),
            {
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.CHECK_AND_COMPLETE,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Fix duplicate guest records")

        self.assertContains(response, "Success")
        self.assertContains(response, "You have deduplicated 2 guest records")
        self.assertContains(response, "A new principal record has been created for")
        self.assertContains(response, "test1firstname test1lastname")
        self.assertContains(
            response,
            "You can undo the deduplication from the "
            "principal record in the actions tab.",
        )

    def test_handles_multi_uan_guests(self):
        user = get_admin_user()
        self.client.force_login(user)
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.multi_uan.id,
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
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id, self.multi_uan.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Deduplicate selected records")

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id, self.multi_uan.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Select correct details")

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            ),
            self.new_principal_multi_uan_guest,
            follow=True,
        )

        self.assertContains(response, "Check details and complete deduplication")

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.CHECK_AND_COMPLETE},
            ),
            {
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.CHECK_AND_COMPLETE,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Fix duplicate guest records")

        self.assertContains(response, "Success")
        self.assertContains(response, "You have deduplicated 2 guest records")
        self.assertContains(response, "A new principal record has been created for")
        self.assertContains(response, "test1firstname test1lastname")
        self.assertContains(
            response,
            "You can undo the deduplication from the "
            "principal record in the actions tab.",
        )

    def test_redirects_with_named_error_if_record_no_longer_principal(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.second_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id, self.second_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id, self.second_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            ),
            self.new_principal_guest,
            follow=True,
        )

        self.second_guest.is_principal = False
        self.second_guest.save()

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.CHECK_AND_COMPLETE},
            ),
            {
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.CHECK_AND_COMPLETE,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Fix duplicate guest records")
        self.assertContains(response, "There is a problem")
        self.assertContains(
            response,
            f"The {self.second_guest.get_full_name()} record has already been "
            "deduplicated. No new principal record was created.",
        )
        self.assertNotContains(response, "A new principal record has been created for")

    def test_redirects_to_select_record_with_error_message_if_system_error(self):
        user = get_admin_user()
        self.client.force_login(user)
        # In this example only one guest has been used for dedup causing the error

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-guest_record": [self.first_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "View selected record")

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Deduplicate selected records")

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.second_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Select correct details")

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            ),
            self.new_principal_guest,
            follow=True,
        )

        self.assertContains(response, "Check details and complete deduplication")

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.CHECK_AND_COMPLETE},
            ),
            {
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.CHECK_AND_COMPLETE,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Fix duplicate guest records")

        self.assertContains(response, "There is a problem")
        self.assertContains(
            response,
            "The selected records have not been marked as duplicates. "
            "No new principal record was created.",
        )
