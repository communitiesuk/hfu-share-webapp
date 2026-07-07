from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

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
            visa_status="Arrived",
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
            visa_status="Issued",
            arrival_date=datetime(2035, 9, 19, tzinfo=timezone.utc),
            visa_application_date_maximum=datetime(2032, 3, 3, tzinfo=timezone.utc),
            application_number=["9999-9999-9999-9999"],
            is_principal=True,
        )

        self.first_guest_clone = MvPersonFactory(
            first_name="test1firstname",
            last_name="test1lastname",
            gender="Female",
            date_of_birth=datetime(1999, 1, 1, tzinfo=timezone.utc),
            email=["test1@example.com"],
            passport_id=["XX88888"],
            visa_status="Arrived",
            arrival_date=datetime(2025, 12, 10, tzinfo=timezone.utc),
            visa_application_date_maximum=datetime(2030, 6, 20, tzinfo=timezone.utc),
            application_number=["4242-4242-4242-4242"],
            is_principal=True,
        )

        self.no_data_guest = MvPersonFactory(
            gender="No data",
            is_principal=True,
        )

        self.empty_guest = MvPersonFactory(
            is_principal=True,
        )

        self.empty_guest_clone = MvPersonFactory(
            is_principal=True,
        )

        self.diff_ar_guest = MvPersonFactory(
            is_principal=True,
        )

        self.accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[
                self.first_guest.pk,
                self.second_guest.pk,
                self.first_guest_clone.pk,
                self.no_data_guest.pk,
                self.empty_guest.pk,
                self.empty_guest_clone.pk,
            ],
            checks_status="Checks Required",
        )
        self.accommodation_request_one.save()

        self.accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[self.diff_ar_guest.pk],
            checks_status="Checks Required",
        )
        self.accommodation_request_two.save()

        self.first_guest.accommodation_request = self.accommodation_request_one
        self.second_guest.accommodation_request = self.accommodation_request_one
        self.first_guest_clone.accommodation_request = self.accommodation_request_one
        self.no_data_guest.accommodation_request = self.accommodation_request_one
        self.empty_guest.accommodation_request = self.accommodation_request_one
        self.empty_guest_clone.accommodation_request = self.accommodation_request_one
        self.diff_ar_guest.accommodation_request = self.accommodation_request_two
        self.first_guest.save()
        self.second_guest.save()
        self.first_guest_clone.save()
        self.no_data_guest.save()
        self.empty_guest.save()
        self.empty_guest_clone.save()
        self.diff_ar_guest.save()

    def test_redirects_to_select_correct_details_view(self):
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

    def test_renders_select_correct_details_view_with_correct_layout(self):
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
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.second_guest.id,
                ],
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
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.second_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Select correct details")

        self.assertContains(response, "Records to be deduplicated")

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
            "Deduplication will create a new principal "
            "record based on the records above. "
            "Select which details to use for the new principal "
            "guest record.",
        )
        self.assertContains(
            response,
            "Where the record details already match, these are shown for reference "
            "and no action is needed. The details will automatically appear in the "
            "new principal guest record.",
        )

        self.assertContains(
            response,
            '<button class="govuk-button"type="submit">Continue deduplication</button>',
            html=True,
        )

        self.assertContains(
            response,
            "<a "
            'class="govuk-link"'
            "href="
            '"/review-potential-duplicate-records-manual/guests/deduplicate/?reset=true">'
            "Cancel"
            "</a>",
            html=True,
        )

    def test_renders_records_to_be_deduplicated_table_with_selected_guest_info(self):
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
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.second_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.second_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
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
        self.assertContains(response, self.first_guest.accommodation_request.title)

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
        self.assertContains(response, self.second_guest.application_number[0])
        self.assertContains(response, self.second_guest.accommodation_request.title)

    def test_renders_option_fields_when_field_values_are_different(self):
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
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.second_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.second_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "First name")
        self.assertContains(response, "Select a first name.")
        self.assertContains(response, self.first_guest.first_name)
        self.assertContains(response, self.second_guest.first_name)

        self.assertContains(response, "Last name")
        self.assertContains(response, "Select a last name.")
        self.assertContains(response, self.first_guest.last_name)
        self.assertContains(response, self.second_guest.last_name)

        self.assertContains(response, "Sex")
        self.assertContains(response, "Select a sex.")
        self.assertContains(response, self.first_guest.gender)
        self.assertContains(response, self.second_guest.gender)

        self.assertContains(response, "Date of birth")
        self.assertContains(response, "Select a date of birth.")
        self.assertContains(
            response, self.first_guest.date_of_birth.strftime("%-d %B %Y")
        )
        self.assertContains(
            response,
            self.second_guest.date_of_birth.strftime("%-d %B %Y"),
        )

        self.assertContains(response, "Email address")
        self.assertContains(response, "Select one or more email addresses.")
        self.assertContains(response, self.first_guest.email[0])
        self.assertContains(response, self.second_guest.email[0])

        self.assertContains(response, "Phone number")
        self.assertContains(response, "Select one or more phone numbers.")
        self.assertContains(response, self.first_guest.phone[0])
        self.assertContains(response, self.second_guest.phone[0])

        self.assertContains(response, "Passport number")
        self.assertContains(response, "Select one or more passport numbers.")
        self.assertContains(response, self.first_guest.passport_id[0])
        self.assertContains(response, self.second_guest.passport_id[0])

        self.assertContains(response, "Visa application number and status")
        self.assertContains(
            response,
            "All visas will be linked to the new principal record. "
            "The guest will be labelled with their latest visa status.",
        )
        self.assertContains(response, self.first_guest.application_number[0])
        self.assertContains(response, self.first_guest.visa_status)
        self.assertContains(response, self.second_guest.application_number[0])
        self.assertContains(response, self.second_guest.visa_status)

        self.assertContains(response, "Accommodation request")
        self.assertContains(
            response,
            "This accommodation request you selected will be linked to the new "
            "principal guest record.",
        )
        self.assertContains(response, "test2firstname test2lastname")
        self.assertContains(response, "Checks Required")

    def test_renders_readonly_fields_when_field_values_are_the_same(self):
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
                    self.first_guest_clone.id,
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
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.first_guest_clone.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.first_guest_clone.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "First name")
        self.assertNotContains(response, "Select a first name.")
        self.assertContains(response, self.first_guest.first_name)

        self.assertContains(response, "Last name")
        self.assertNotContains(response, "Select a last name.")
        self.assertContains(response, self.first_guest.last_name)

        self.assertContains(response, "Sex")
        self.assertNotContains(response, "Select a sex.")
        self.assertContains(response, self.first_guest.gender)

        self.assertContains(response, "Date of birth")
        self.assertNotContains(
            response,
            "Select a date of birth. The age is shown in brackets for reference.",
        )
        self.assertContains(
            response, f"{self.first_guest.date_of_birth.strftime('%-d %B %Y')}"
        )

        self.assertContains(response, "Email address")
        self.assertNotContains(response, "Select an email address.")
        self.assertContains(response, self.first_guest.email[0])

        self.assertContains(response, "Phone number")
        self.assertNotContains(response, "Select one or more phone numbers.")
        self.assertContains(response, self.first_guest.phone[0])

        self.assertContains(response, "Passport number")
        self.assertNotContains(response, "Select one or more passport numbers.")
        self.assertContains(response, self.first_guest.passport_id[0])

        self.assertContains(response, "Visa application number and status")
        self.assertContains(
            response,
            "All visas will be linked to the new principal record. "
            "The guest will be labelled with their latest visa status.",
        )
        self.assertContains(response, self.first_guest.application_number[0])
        self.assertContains(response, self.first_guest.visa_status)

        self.assertContains(response, "Accommodation request")
        self.assertContains(
            response,
            "This accommodation request you selected will be linked to the new "
            "principal guest record.",
        )
        self.assertContains(response, "test2firstname test2lastname")
        self.assertContains(response, "Checks Required")

    def test_fields_are_formatted_correctly_based_on_the_values(self):
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
                    self.no_data_guest.id,
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
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.no_data_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.no_data_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Sex")
        self.assertContains(response, "Select a sex or 'no data'.")
        self.assertContains(response, self.first_guest.gender)
        self.assertContains(response, self.no_data_guest.gender)

    def test_required_fields_present_errors_when_not_selected(self):
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
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.second_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.second_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            ),
            {
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS,
                ),
            },
            follow=True,
        )

        self.assertContains(
            response,
            '<h2 class="govuk-error-summary__title" id="error-summary-title">'
            "There is a problem"
            "</h2>",
            html=True,
        )

        self.assertContains(
            response,
            '<li><a href="#id_select-correct-details-first_name">'
            "Select a first name.</a></li>",
            html=True,
        )

        self.assertContains(
            response,
            '<li><a href="#id_select-correct-details-last_name">'
            "Select a last name.</a></li>",
            html=True,
        )

        self.assertContains(
            response,
            '<li><a href="#id_select-correct-details-sex">Select a sex.</a></li>',
            html=True,
        )

        self.assertContains(
            response,
            '<li><a href="#id_select-correct-details-date_of_birth">'
            "Select a date of birth.</a></li>",
            html=True,
        )

        self.assertContains(
            response,
            '<li><a href="#id_select-correct-details-email_address">'
            "Select at least one email address.</a></li>",
            html=True,
        )

        self.assertContains(
            response,
            '<li><a href="#id_select-correct-details-phone_numbers">'
            "Select at least one phone number.</a></li>",
            html=True,
        )

        self.assertContains(
            response,
            '<li><a href="#id_select-correct-details-passport_number">'
            "Select at least one passport number.</a></li>",
            html=True,
        )

    def test_when_only_one_value_is_populated_should_be_auto_selected(self):
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
                    self.no_data_guest.id,
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
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.no_data_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.no_data_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "First name")
        self.assertNotContains(response, "Select a first name.")
        self.assertContains(response, self.first_guest.first_name)

        self.assertContains(response, "Last name")
        self.assertNotContains(response, "Select a last name.")
        self.assertContains(response, self.first_guest.last_name)

        self.assertContains(response, "Sex")
        self.assertNotContains(response, "Select a sex.")
        self.assertContains(response, self.first_guest.gender)

        self.assertContains(response, "Date of birth")
        self.assertNotContains(
            response,
            "Select a date of birth. The age is shown in brackets for reference.",
        )
        self.assertContains(
            response, f"{self.first_guest.date_of_birth.strftime('%-d %B %Y')}"
        )

        self.assertContains(response, "Email address")
        self.assertNotContains(response, "Select an email address.")
        self.assertContains(response, self.first_guest.email[0])

        self.assertContains(response, "Phone number")
        self.assertNotContains(response, "Select one or more phone numbers.")
        self.assertContains(response, self.first_guest.phone[0])

        self.assertContains(response, "Passport number")
        self.assertNotContains(response, "Select one or more passport numbers.")
        self.assertContains(response, self.first_guest.passport_id[0])

        self.assertContains(response, "Visa application number and status")
        self.assertContains(
            response,
            "All visas will be linked to the new principal record. "
            "The guest will be labelled with their latest visa status.",
        )
        self.assertContains(response, self.first_guest.application_number[0])
        self.assertContains(response, self.first_guest.visa_status)

        self.assertContains(response, "Accommodation request")
        self.assertContains(
            response,
            "This accommodation request you selected will be linked to the new "
            "principal guest record.",
        )
        self.assertContains(response, "test2firstname test2lastname")
        self.assertContains(response, "Checks Required")

    def test_application_number_and_accommodation_title_are_html_escaped(self):
        user = get_admin_user()
        self.client.force_login(user)

        malicious_application_number = "<script>alert('application-number')</script>"
        malicious_ar_title = "<script>alert('accommodation-title')</script>"

        self.first_guest.application_number = [malicious_application_number]
        self.first_guest.save()
        self.accommodation_request_one.title = malicious_ar_title
        self.accommodation_request_one.save()

        self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.no_data_guest.id,
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
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.no_data_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.no_data_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertNotContains(response, malicious_application_number)
        self.assertNotContains(response, malicious_ar_title)
        self.assertContains(response, escape(malicious_application_number))
        self.assertContains(response, escape(malicious_ar_title))

        # Trusted status tag components should still render normally.
        self.assertContains(response, self.first_guest.visa_status)
        self.assertContains(response, self.accommodation_request_one.checks_status)

    def test_should_not_render_field_info_when_no_values_available(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-guest_record": [
                    self.empty_guest.id,
                    self.empty_guest_clone.id,
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
                "select-record-guest_record": [
                    self.empty_guest.id,
                    self.empty_guest_clone.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-guest_record": [
                    self.empty_guest.id,
                    self.empty_guest_clone.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "First name")
        self.assertNotContains(response, "Select a first name.")
        self.assertContains(response, "No first name to select.")

        self.assertContains(response, "Last name")
        self.assertNotContains(response, "Select a last name.")
        self.assertContains(response, "No email address to select.")

        self.assertContains(response, "Sex")
        self.assertNotContains(response, "Select a sex.")
        self.assertNotContains(response, "Select a sex or 'no data'.")
        self.assertContains(response, "No sex to select.")

        self.assertContains(response, "Date of birth")
        self.assertNotContains(
            response,
            "Select a date of birth. The age is shown in brackets for reference.",
        )
        self.assertContains(response, "No date of birth to select.")

        self.assertContains(response, "Email address")
        self.assertNotContains(response, "Select one or more email addresses.")
        self.assertContains(response, "No email address to select.")

        self.assertContains(response, "Phone number")
        self.assertNotContains(response, "Select one or more phone numbers.")
        self.assertContains(response, "No phone number to select.")

        self.assertContains(response, "Passport number")
        self.assertNotContains(response, "Select one or more passport numbers.")
        self.assertContains(response, "No passport number to select.")

    def test_should_show_selected_ar_request_from_select_ar_view(self):
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
                    self.diff_ar_guest.id,
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
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.diff_ar_guest.id,
                ],
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
                "select-record-guest_record": [
                    self.first_guest.id,
                    self.diff_ar_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_ACCOMMODATION_REQUEST,
                },
            ),
            {
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_ACCOMMODATION_REQUEST
                ),
                "select-accommodation-request-accommodation_request": (
                    self.accommodation_request_two.pk
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Accommodation request")
        self.assertContains(
            response,
            "This accommodation request you selected will be linked to the new "
            "principal guest record.",
        )
        self.assertContains(response, "test2firstname test2lastname")
        self.assertContains(response, "Checks Required")
