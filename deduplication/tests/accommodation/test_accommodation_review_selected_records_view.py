from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.views import SelectAndReviewRecordsStep
from ontology.tests.factories import MvAccommodationFactory, MvUkPostcodeFactory
from user_management.tests.base import get_admin_user


class DeduplicationAccommodationSelectedViewTests(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.first_accommodation = MvAccommodationFactory(
            full_address="A Test Address 1",
            ltla_name="ltla_somerset",
            utla_name="utla_somerset",
            postcode=MvUkPostcodeFactory(postcode="ABC123"),
            is_principal=True,
        )

        self.second_accommodation = MvAccommodationFactory(
            full_address="A Test Address 2",
            ltla_name="ltla_croydon",
            utla_name="utla_croydon",
            postcode=MvUkPostcodeFactory(postcode="CBA321"),
            is_principal=False,
        )

    def test_redirects_to_review_records_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-accommodation_record": [
                    self.first_accommodation.id,
                    self.second_accommodation.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/review-potential-duplicate-records-manual/accommodations/deduplicate/view-selected-records/",
        )

        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record": [
                    self.first_accommodation.id,
                    self.second_accommodation.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/review-potential-duplicate-records-manual/accommodations/deduplicate/review-selected-records/",
        )

    def test_renders_review_list_with_correct_layout(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-accommodation_record": [
                    self.first_accommodation.id,
                    self.second_accommodation.id,
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
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-accommodation_record": [
                    self.first_accommodation.id,
                    self.second_accommodation.id,
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

        self.assertContains(response, "Address")
        self.assertContains(response, "Postcode")
        self.assertContains(response, "Lower tier LA")
        self.assertContains(response, "Upper tier LA")

        self.assertContains(
            response,
            "Click 'Continue' to proceed or 'Cancel' to keep the records separate.",
        )
        self.assertContains(
            response,
            '<button class="govuk-button"type="submit">Continue</button>',
            html=True,
        )
        self.assertContains(
            response,
            '<a class="govuk-link" href="/review-potential-duplicate-records-manual'
            '/accommodations/deduplicate/?reset=true">Cancel</a>',
            html=True,
        )

    def test_renders_review_list_with_selected_accommodation_info(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-accommodation_record": [
                    self.first_accommodation.id,
                    self.second_accommodation.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-accommodation_record": [
                    self.first_accommodation.id,
                    self.second_accommodation.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
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

        self.assertContains(response, self.second_accommodation.full_address)
        self.assertContains(
            response, self.second_accommodation.postcode.postcode_formatted
        )
        self.assertContains(response, self.second_accommodation.ltla_name)
        self.assertContains(response, self.second_accommodation.utla_name)
