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
            created_date=datetime(1981, 6, 10, tzinfo=timezone.utc),
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
            created_date=datetime(1988, 6, 10, tzinfo=timezone.utc),
            is_principal=True,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

    def test_redirects_to_review_records_view(self):
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

    def test_renders_review_list_with_correct_layout(self):
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
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.second_sponsor.id,
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
        self.assertContains(response, "Email address")
        self.assertContains(response, "Phone number")
        self.assertContains(response, "EOI host")
        self.assertContains(response, "Date added")

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
            "<a "
            'class="govuk-link"'
            "href="
            '"/review-potential-duplicate-records-manual/sponsors/deduplicate/?reset=true">'
            "Cancel"
            "</a>",
            html=True,
        )

    def test_renders_review_list_with_selected_sponsor_info(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.client.post(
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

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.second_sponsor.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
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
        self.assertContains(
            response, self.first_sponsor.created_date.strftime("%d %b %Y")
        )
