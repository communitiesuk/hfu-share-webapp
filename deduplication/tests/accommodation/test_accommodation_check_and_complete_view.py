from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.views import SelectAndReviewRecordsStep
from ontology.models import MvAccommodation
from ontology.tests.factories import MvAccommodationFactory, MvUkPostcodeFactory
from user_management.tests.base import get_admin_user


class DeduplicationAccommodationCheckAndCompleteViewTestCase(
    TestSessionTokenMixin, TestCase
):
    def setUp(self):
        super().setUp()
        self.first_accommodation = MvAccommodationFactory(
            full_address="1 ABC Road, AB1 CD3",
            ltla_name="ltla_somerset",
            utla_name="utla_somerset",
            postcode=MvUkPostcodeFactory(postcode="AB1CD3"),
            is_principal=True,
        )
        self.second_accommodation = MvAccommodationFactory(
            full_address="2 DEQ Road, PP2 EE1",
            ltla_name="ltla_somerset",
            utla_name="ltla_somerset",
            postcode=MvUkPostcodeFactory(postcode="PP2EE1"),
            is_principal=False,
        )
        self.step_prefix = "select-correct-details-"
        self.new_principal_accommodation = {
            f"{self.step_prefix}full_address": self.second_accommodation.id,
            f"{self.step_prefix}postcode": str(self.second_accommodation.postcode.id),
            f"{self.step_prefix}ltla_name": self.second_accommodation.ltla_name,
            f"{self.step_prefix}utla_name": self.second_accommodation.utla_name,
            "SelectAndReviewRecordsFormWizard-current_step": (
                SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS,
            ),
        }

    def test_redirects_to_check_and_complete_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Go through the wizard steps to reach check and complete
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
        )
        self.client.post(
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
        )
        self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-accommodation_record": [
                    self.first_accommodation.id,
                    self.second_accommodation.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
        )
        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            ),
            self.new_principal_accommodation,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/review-potential-duplicate-records-manual/accommodations/deduplicate/check-and-complete/",
        )

    def test_renders_check_and_complete_view_with_correct_layout(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Go through the wizard steps to reach check and complete
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
        self.client.post(
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
        self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-accommodation_record": [
                    self.first_accommodation.id,
                    self.second_accommodation.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )
        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            ),
            self.new_principal_accommodation,
            follow=True,
        )

        self.assertContains(response, "Check details and complete deduplication")
        self.assertContains(response, "Original records to be deduplicated")
        self.assertContains(response, "Address")
        self.assertContains(response, "Postcode")
        self.assertContains(response, "Lower tier LA")
        self.assertContains(response, "Upper tier LA")
        self.assertContains(
            response, "Check the details are correct for the new principal record"
        )
        self.assertContains(
            response, "Are you sure you want to complete the deduplication?"
        )
        # self.assertContains(
        #     response,
        #     "This will create a new principal record with the information shown. The "
        #     "original accommodation records will be marked as duplicates and you "
        #     "will not be able to change them, unless you first undo the "
        #     "deduplication.",
        # ) TODO: replace below when undo deduplication is re-enabled
        self.assertContains(
            response,
            "This will create a new principal record with the information shown. The "
            "original accommodation records will be marked as duplicates and you "
            "will not be able to change them.",
        )
        self.assertContains(
            response,
            '<button type="submit"class="govuk-button">'
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

    def test_renders_check_and_complete_view_with_correct_accommodation_info(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Go through the wizard steps to reach check and complete
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
        self.client.post(
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
        self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-accommodation_record": [
                    self.first_accommodation.id,
                    self.second_accommodation.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )
        response = self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            ),
            self.new_principal_accommodation,
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

        full_address_id = self.new_principal_accommodation[
            f"{self.step_prefix}full_address"
        ]
        full_address = MvAccommodation.objects.get(id=full_address_id).full_address
        self.assertContains(response, full_address)

        self.assertContains(
            response, self.second_accommodation.postcode.postcode_formatted
        )
        self.assertContains(response, self.second_accommodation.ltla_name)
        self.assertContains(response, self.second_accommodation.utla_name)
