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
            is_principal=True,
        )

        self.second_guest = MvPersonFactory(
            first_name="test2firstname",
            last_name="test2lastname",
            is_principal=True,
        )

        self.third_guest = MvPersonFactory(
            first_name="test3firstname",
            last_name="test3lastname",
            is_principal=True,
        )

        self.accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[self.first_guest.pk, self.second_guest.pk],
            checks_status="Checks completed",
            latest_application_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            number_of_people=1,
            ltla_name=["test ltla 1"],
            utla_name=["test utla 1"],
        )
        self.accommodation_request_one.save()
        self.first_guest.accommodation_request = self.accommodation_request_one
        self.second_guest.accommodation_request = self.accommodation_request_one
        self.first_guest.save()
        self.second_guest.save()

        self.accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[self.third_guest.pk],
            checks_status="Checks required",
            latest_application_date=datetime(2026, 11, 11, tzinfo=timezone.utc),
            number_of_people=3,
            ltla_name=["test ltla 2"],
            utla_name=["test utla 2"],
        )
        self.accommodation_request_two.save()
        self.third_guest.accommodation_request = self.accommodation_request_two
        self.third_guest.save()

    def test_does_not_redirect_to_select_ar_view_for_identical_ars(self):
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
            "/deduplication/guests/view-selected-records/",
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
            "/deduplication/guests/review-selected-records/",
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
        self.assertNotEqual(
            response.url,
            "/deduplication/guests/select-accommodation-request/",
        )
        self.assertEqual(
            response.url,
            "/deduplication/guests/select-correct-details/",
        )

    def test_redirects_to_select_accommodation_request_view_when_ars_are_different(
        self,
    ):
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
                    self.third_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/deduplication/guests/view-selected-records/",
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id, self.third_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/deduplication/guests/review-selected-records/",
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id, self.third_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/deduplication/guests/select-accommodation-request/",
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
                    self.third_guest.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/deduplication/guests/view-selected-records/",
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id, self.third_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/deduplication/guests/review-selected-records/",
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [self.first_guest.id, self.third_guest.id],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Select accommodation request")
        self.assertContains(
            response,
            "These guests are linked to different accommodation requests. "
            "Once they are deduplicated, the new principal guest record can only have "
            "one accommodation request.",
        )
        self.assertContains(
            response, "Review the accommodation requests by selecting the links below."
        )
        self.assertContains(response, self.accommodation_request_one.title)
        self.assertContains(response, self.accommodation_request_one.status)
        self.assertContains(response, "1 Jan 2025")
        self.assertContains(response, self.accommodation_request_one.number_of_people)
        self.assertContains(response, self.accommodation_request_one.ltla_name[0])
        self.assertContains(response, self.accommodation_request_one.utla_name[0])

        self.assertContains(response, self.accommodation_request_two.title)
        self.assertContains(response, self.accommodation_request_two.status)
        self.assertContains(response, "11 Nov 2026")
        self.assertContains(response, self.accommodation_request_two.number_of_people)
        self.assertContains(response, self.accommodation_request_two.ltla_name[0])
        self.assertContains(response, self.accommodation_request_two.utla_name[0])

        self.assertContains(
            response,
            "Accommodation request",
        )
        self.assertContains(
            response,
            "Select which accommodation request record to link to the new "
            "principal guest record, or cancel to return to the guest selection "
            "screen.",
        )
        self.assertContains(
            response,
            '<button class="govuk-button"type="submit">Continue deduplication</button>',
            html=True,
        )
        self.assertContains(
            response,
            '<a class="govuk-link" href="/deduplication/guests/?reset=true">Cancel</a>',
            html=True,
        )
