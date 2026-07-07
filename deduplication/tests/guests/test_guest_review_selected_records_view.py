from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.views import SelectAndReviewRecordsStep
from ontology.tests.factories import MvPersonFactory
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
            gender="Female",
            date_of_birth=datetime(1989, 6, 6, tzinfo=timezone.utc),
            email=["test2@example.com"],
            passport_id=["XX99999"],
            visa_status="Arrived",
            arrival_date=datetime(2035, 9, 19, tzinfo=timezone.utc),
            visa_application_date_maximum=datetime(2032, 3, 3, tzinfo=timezone.utc),
            application_number=["9999-9999-9999-9999"],
            is_principal=True,
        )

    def test_redirects_to_review_records_view(self):
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
            "/review-potential-duplicate-records-manual/guests/deduplicate/view-selected-records/",
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
            "/review-potential-duplicate-records-manual/guests/deduplicate/review-selected-records/",
        )

    def test_renders_review_list_with_correct_layout(self):
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
        self.assertContains(
            response,
            "You confirmed the following records:",
        )
        self.assertContains(response, "Name")
        self.assertContains(response, "Sex")
        self.assertContains(response, "Date of birth")
        self.assertContains(response, "Passport number")
        self.assertContains(response, "Visa status")
        self.assertContains(response, "First arrival date")
        self.assertContains(response, "Latest visa application date")
        self.assertContains(response, "Unique Application Number (UAN)")
        self.assertContains(
            response,
            "Click 'Continue' to proceed or 'Cancel' to keep the records separate.",
        )
        self.assertContains(
            response,
            '<button class="govuk-button"type="submit">Continue deduplication</button>',
            html=True,
        )
        self.assertContains(
            response,
            '<a class="govuk-link" href="/review-potential-duplicate-records-manual'
            '/guests/deduplicate/?reset=true">Cancel</a>',
            html=True,
        )

    def test_renders_review_list_with_selected_guest_info(self):
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

        self.assertContains(
            response, f"{self.first_guest.first_name} {self.first_guest.last_name}"
        )
        self.assertContains(response, self.first_guest.gender)
        self.assertContains(
            response, self.first_guest.date_of_birth.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.first_guest.passport_id[0])
        self.assertContains(response, self.first_guest.visa_status)
        self.assertContains(
            response, self.first_guest.arrival_date.strftime("%-d %b %Y")
        )
        self.assertContains(
            response,
            self.first_guest.visa_application_date_maximum.strftime("%-d %b %Y"),
        )
        self.assertContains(response, self.first_guest.application_number[0])
        self.assertContains(
            response, f"{self.second_guest.first_name} {self.second_guest.last_name}"
        )
        self.assertContains(response, self.second_guest.gender)
        self.assertContains(
            response, self.second_guest.date_of_birth.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.second_guest.passport_id[0])
        self.assertContains(response, self.second_guest.visa_status)
        self.assertContains(
            response, self.second_guest.arrival_date.strftime("%-d %b %Y")
        )
        self.assertContains(
            response,
            self.second_guest.visa_application_date_maximum.strftime("%-d %b %Y"),
        )
        self.assertContains(response, self.second_guest.application_number[0])
