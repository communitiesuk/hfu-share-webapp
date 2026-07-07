from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.views import SelectAndReviewRecordsStep
from ontology.models import MvVolunteer
from ontology.tests.factories import MvAccommodationFactory, MvVolunteerFactory
from user_management.tests.base import get_admin_user


class DeduplicationSponsorListViewTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.sponsor = MvVolunteerFactory(
            first_name="test firstname",
            last_name="test lastname",
            sex="Female",
            date_of_birth=datetime(1999, 1, 1, tzinfo=timezone.utc),
            email="test@example.com",
            phone_number=["01134960698"],
            residential_postcodes=["OX1 1OX"],
            flag_unsuitable=False,
            created_date=datetime(1981, 6, 10, tzinfo=timezone.utc),
            is_principal=True,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

        self.other_la_sponsor = MvVolunteerFactory(
            first_name="test other",
            last_name="la",
            is_principal=True,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

        self.multi_la_sponsor = MvVolunteerFactory(
            first_name="test multi",
            last_name="la",
            is_principal=True,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

        self.non_principal_sponsor = MvVolunteerFactory(
            first_name="Non Principal Sponsor",
            last_name="Spon",
            is_principal=False,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

        self.somerset_ltla_accommodation = MvAccommodationFactory(
            full_address="Somerset LTLA Address",
            ltla_name="ltla_somerset",
        )
        self.somerset_ltla_accommodation.hosts.set([self.sponsor.id])
        self.sponsor.accommodations.set([self.somerset_ltla_accommodation.id])

        self.other_la_accommodation = MvAccommodationFactory(
            full_address="Other accommodation",
            ltla_name="Other LTLA",
        )
        self.other_la_accommodation.hosts.set([self.other_la_sponsor])
        self.other_la_sponsor.accommodations.set([self.other_la_accommodation])

        self.multi_la_accommodation = MvAccommodationFactory(
            full_address="Multi accommodation",
            ltla_name="Multi LTLA",
        )
        self.somerset_ltla_accommodation.hosts.set([self.multi_la_sponsor.id])
        self.multi_la_accommodation.hosts.set([self.multi_la_sponsor])
        self.multi_la_sponsor.accommodations.set(
            [self.somerset_ltla_accommodation, self.multi_la_accommodation]
        )

    def test_redirects_to_list_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual",
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/review-potential-duplicate-records-manual"
            "/sponsors"
            "/deduplicate"
            "/select-record/",
        )

    def test_renders_sponsor_list_with_correct_layout(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            )
        )

        self.assertContains(response, "Fix duplicate sponsor and host records")

        self.assertContains(
            response,
            "Select a record to review and deduplicate. You can use the filter "
            "panel to find records.",
        )
        self.assertContains(
            response,
            "You cannot deduplicate records across lower tier local authorities "
            "(LAs). Records with links to multiple LAs are hidden from the list.",
        )

        self.assertContains(response, "Name")
        self.assertContains(response, "Sex")
        self.assertContains(response, "Date of birth")
        self.assertContains(response, "Email address")
        self.assertContains(response, "Phone number")
        self.assertContains(response, "EOI host")
        self.assertContains(response, "Date added")
        self.assertContains(response, "False")

    def test_renders_sponsor_list_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            )
        )

        self.assertContains(
            response, self.sponsor.first_name + " " + self.sponsor.last_name
        )
        self.assertContains(response, self.sponsor.sex)
        self.assertContains(response, self.sponsor.date_of_birth.strftime("%-d %b %Y"))
        self.assertContains(response, self.sponsor.email)
        self.assertContains(response, self.sponsor.phone_number[0])
        self.assertContains(response, "False")
        self.assertContains(response, self.sponsor.created_date.strftime("%d %b %Y"))

    def test_does_not_render_non_principal_sponsor(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            )
        )

        self.assertNotContains(
            response,
            self.non_principal_sponsor.first_name
            + " "
            + self.non_principal_sponsor.last_name,
        )

    def test_renders_only_non_multi_la_sponsors(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual",
            ),
            follow=True,
        )

        self.assertContains(
            response,
            self.sponsor.full_name,
        )

        self.assertNotContains(
            response,
            self.multi_la_sponsor.full_name,
        )

    def test_renders_only_ltla_records_matching_selected_sponsor(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-sponsor_record": self.sponsor.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:sponsors:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                },
            ),
            {
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS,
                ),
                "wizard_goto_step": SelectAndReviewRecordsStep.SELECT_RECORD,
            },
            follow=True,
        )

        self.assertContains(response, "Select next record")
        self.assertContains(
            response,
            "You cannot deduplicate records across lower tier local authorities "
            "(LAs). Records with links to multiple LAs are hidden from the list.",
        )

        self.assertNotContains(
            response,
            self.other_la_sponsor.full_name,
        )
