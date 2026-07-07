import html

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.views import SelectAndReviewRecordsStep
from ontology.tests.factories import MvAccommodationFactory, MvUkPostcodeFactory
from user_management.tests.base import get_admin_user


class DeduplicationAccommodationSelectCorrectDetailsViewTestCase(
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
        self.accommodation_with_special_character = MvAccommodationFactory(
            full_address="2 AA'Q Road, JJ2 EE1",
            ltla_name="ltla_somerset",
            utla_name="ltla_somerset",
            postcode=MvUkPostcodeFactory(postcode="JJ2EE1"),
            is_principal=False,
        )

    def test_renders_select_correct_details_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Go through the steps to reach select correct details
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
        response = self.client.get(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            )
        )

        self.assertContains(response, "Select correct details")
        self.assertContains(response, "Address")
        self.assertContains(response, "Postcode")
        self.assertContains(response, "Lower tier LA")
        self.assertContains(response, "Upper tier LA")
        self.assertContains(response, self.first_accommodation.full_address)
        self.assertContains(response, self.second_accommodation.full_address)
        self.assertContains(
            response, self.first_accommodation.postcode.postcode_formatted
        )
        self.assertContains(
            response, self.second_accommodation.postcode.postcode_formatted
        )
        self.assertContains(response, self.first_accommodation.ltla_name)
        self.assertContains(response, self.second_accommodation.ltla_name)
        self.assertContains(response, self.first_accommodation.utla_name)
        self.assertContains(response, self.second_accommodation.utla_name)

    def test_renders_select_correct_details_view_when_address_has_special_character(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        # Go through the steps to reach select correct details
        self.client.post(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-accommodation_record": [
                    self.first_accommodation.id,
                    self.accommodation_with_special_character.id,
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
                    self.accommodation_with_special_character.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )
        response = self.client.get(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS},
            )
        )

        self.assertContains(response, "Select correct details")
        self.assertContains(response, "Address")
        self.assertContains(response, "Postcode")
        self.assertContains(response, "Lower tier LA")
        self.assertContains(response, "Upper tier LA")
        self.assertContains(response, self.first_accommodation.full_address)
        self.assertContains(
            response,
            html.escape(self.accommodation_with_special_character.full_address),
        )
        self.assertContains(
            response, self.first_accommodation.postcode.postcode_formatted
        )
        self.assertContains(
            response,
            self.accommodation_with_special_character.postcode.postcode_formatted,
        )
        self.assertContains(response, self.first_accommodation.ltla_name)
        self.assertContains(
            response, self.accommodation_with_special_character.ltla_name
        )
        self.assertContains(response, self.first_accommodation.utla_name)
        self.assertContains(
            response, self.accommodation_with_special_character.utla_name
        )
