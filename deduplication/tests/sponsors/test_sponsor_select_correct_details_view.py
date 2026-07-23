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
            first_name="testfirstname1",
            last_name="testlastname1",
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
            first_name="testfirstname2",
            last_name="testlastname2",
            sex="Male",
            date_of_birth=datetime(1981, 6, 10, tzinfo=timezone.utc),
            age=44,
            email="test2@example.com",
            phone_number=["04467123455"],
            residential_postcodes=["NW1 1WN"],
            flag_unsuitable=False,
            is_principal=True,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

        self.first_sponsor_clone = MvVolunteerFactory(
            first_name="testfirstname1",
            last_name="testlastname1",
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

        self.no_data_sponsor = MvVolunteerFactory(
            first_name="testfirstname3",
            last_name="testlastname3",
            sex="No data",
            date_of_birth=datetime(1991, 11, 11, tzinfo=timezone.utc),
            age=30,
            flag_unsuitable=False,
            is_principal=True,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

        self.empty_sponsor = MvVolunteerFactory(
            flag_unsuitable=False,
            is_principal=True,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

        self.empty_sponsor_clone = MvVolunteerFactory(
            flag_unsuitable=False,
            is_principal=True,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

    def test_redirects_to_select_correct_details_view(self):
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
            "/deduplication/sponsors/view-selected-records/",
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
            "/deduplication/sponsors/review-selected-records/",
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
            "/deduplication/sponsors/select-correct-details/",
        )

    def test_renders_select_correct_details_view_with_correct_layout(self):
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

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.second_sponsor.id,
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
        self.assertContains(response, "Residential postcode")

        self.assertContains(
            response,
            "Deduplication will create a new principal "
            "record based on the records above. "
            "Select which details to use for the new principal "
            "sponsor and host record.",
        )
        self.assertContains(
            response,
            "Where the record details already match, these are shown for reference "
            "and no action is needed. The details will automatically appear in the "
            "new principal sponsor and host record.",
        )

        self.assertContains(
            response,
            '<button class="govuk-button"type="submit">Continue deduplication</button>',
            html=True,
        )

        self.assertContains(
            response,
            "<a "
            'class="govuk-link govuk-link--no-visited-state"'
            "href="
            '"/deduplication/sponsors/?reset=true">'
            "Cancel"
            "</a>",
            html=True,
        )

    def test_renders_records_to_be_deduplicated_table_with_selected_sponsor_info(self):
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

        self.client.post(
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

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.second_sponsor.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
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
        self.assertContains(response, self.first_sponsor.residential_postcodes[0])

    def test_renders_option_fields_when_field_values_are_different(self):
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

        self.client.post(
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

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.second_sponsor.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "First name")
        self.assertContains(response, "Select a first name.")
        self.assertContains(response, self.first_sponsor.first_name)
        self.assertContains(response, self.second_sponsor.first_name)

        self.assertContains(response, "Last name")
        self.assertContains(response, "Select a last name.")
        self.assertContains(response, self.first_sponsor.last_name)
        self.assertContains(response, self.second_sponsor.last_name)

        self.assertContains(response, "Sex")
        self.assertContains(response, "Select a sex.")
        self.assertContains(response, self.first_sponsor.sex)
        self.assertContains(response, self.second_sponsor.sex)

        self.assertContains(response, "Date of birth")
        self.assertContains(
            response,
            "Select a date of birth.",
        )
        self.assertContains(
            response, self.first_sponsor.date_of_birth.strftime("%-d %B %Y")
        )
        self.assertContains(
            response,
            self.second_sponsor.date_of_birth.strftime("%-d %B %Y"),
        )

        self.assertContains(response, "Email address")
        self.assertContains(response, "Select an email address.")
        self.assertContains(response, self.first_sponsor.email[0])
        self.assertContains(response, self.second_sponsor.email[0])

        self.assertContains(response, "Phone number")
        self.assertContains(response, "Select one or more phone numbers.")
        self.assertContains(response, self.first_sponsor.phone_number[0])
        self.assertContains(response, self.second_sponsor.phone_number[0])

        self.assertContains(response, "Residential postcode")
        self.assertContains(response, "Select one or more postcodes.")
        self.assertContains(response, self.first_sponsor.residential_postcodes[0])
        self.assertContains(response, self.second_sponsor.residential_postcodes[0])

    def test_renders_readonly_fields_when_field_values_are_the_same(self):
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
                    self.first_sponsor_clone.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.first_sponsor_clone.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.first_sponsor_clone.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "First name")
        self.assertNotContains(response, "Select a first name.")
        self.assertContains(response, self.first_sponsor.first_name)

        self.assertContains(response, "Last name")
        self.assertNotContains(response, "Select a last name.")
        self.assertContains(response, self.first_sponsor.last_name)

        self.assertContains(response, "Sex")
        self.assertNotContains(response, "Select a sex.")
        self.assertContains(response, self.first_sponsor.sex)

        self.assertContains(response, "Date of birth")
        self.assertNotContains(
            response,
            "Select a date of birth. The age is shown in brackets for reference.",
        )
        self.assertContains(response, "11 November 1999")

        self.assertContains(response, "Email addresses")
        self.assertNotContains(response, "Select one or more email addresses.")
        self.assertContains(response, self.first_sponsor.email[0])

        self.assertContains(response, "Phone numbers")
        self.assertNotContains(response, "Select one or more phone numbers.")
        self.assertContains(response, self.first_sponsor.phone_number[0])

        self.assertContains(response, "Residential postcodes")
        self.assertNotContains(response, "Select one or more postcodes.")
        self.assertContains(response, self.first_sponsor.residential_postcodes[0])

    def test_fields_are_formatted_correctly_based_on_the_values(self):
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
                    self.no_data_sponsor.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.no_data_sponsor.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.no_data_sponsor.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Sex")
        self.assertContains(response, "Select a sex or 'no data'.")
        self.assertContains(response, self.first_sponsor.sex)
        self.assertContains(response, self.no_data_sponsor.sex)

    def test_required_fields_present_errors_when_not_selected(self):
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

        self.client.post(
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

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.second_sponsor.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
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
            '<li><a href="#id_select-correct-details-last_name">'
            "Select a last name.</a></li>",
            html=True,
        )

        self.assertContains(
            response,
            '<li><a href="#id_select-correct-details-email_address">'
            "Select an email address.</a></li>",
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
            '<li><a href="#id_select-correct-details-residential_postcodes">'
            "Select at least one residential postcode.</a></li>",
            html=True,
        )

    def test_when_only_one_value_is_populated_should_be_auto_selected(self):
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
                    self.no_data_sponsor.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.no_data_sponsor.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-sponsor_record": [
                    self.first_sponsor.id,
                    self.no_data_sponsor.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Email addresses")
        self.assertNotContains(response, "Select one or more email addresses.")
        self.assertContains(response, self.first_sponsor.email[0])

        self.assertContains(response, "Phone numbers")
        self.assertNotContains(response, "Select one or more phone numbers.")
        self.assertContains(response, self.first_sponsor.phone_number[0])

        self.assertContains(response, "Residential postcodes")
        self.assertNotContains(response, "Select one or more postcodes.")
        self.assertContains(response, self.first_sponsor.residential_postcodes[0])

    def test_should_not_render_field_info_when_no_values_available(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.SELECT_RECORD},
            ),
            {
                "select-record-sponsor_record": [
                    self.empty_sponsor.id,
                    self.empty_sponsor_clone.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD,
                ),
            },
            follow=True,
        )

        self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-sponsor_record": [
                    self.empty_sponsor.id,
                    self.empty_sponsor_clone.id,
                ],
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={"step": SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS},
            ),
            {
                "select-record-sponsor_record": [
                    self.empty_sponsor.id,
                    self.empty_sponsor_clone.id,
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

        self.assertContains(response, "Residential postcode")
        self.assertNotContains(response, "Select one or more postcodes.")
        self.assertContains(response, "No postcode to select.")
