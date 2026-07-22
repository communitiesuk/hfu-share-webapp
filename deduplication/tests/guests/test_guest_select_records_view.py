import datetime

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.views import SelectAndReviewRecordsStep
from ontology.models import ReassignmentRequest
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvPersonFactory,
    ReassignmentRequestFactory,
)
from user_management.tests.base import get_admin_user


class DeduplicationSponsorListViewTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.guest = MvPersonFactory(
            first_name="testfirstname",
            last_name="testlastname",
            gender="Female",
            date_of_birth=datetime.date(1999, 1, 1),
            passport_id=["XX88888"],
            visa_status="Arrived",
            arrival_date=datetime.date(2025, 12, 10),
            visa_application_date_maximum=datetime.date(2030, 6, 20),
            application_number=["4242-4242-4242-4242"],
            is_principal=True,
        )

        self.same_ltla_guest = MvPersonFactory(
            first_name="testmatchfirstname",
            last_name="testmatchlastname",
            gender="Female",
            date_of_birth=datetime.date(1999, 1, 1),
            passport_id=["XX88888"],
            visa_status="Arrived",
            arrival_date=datetime.date(2025, 12, 10),
            visa_application_date_maximum=datetime.date(2030, 6, 20),
            application_number=["4242-4242-4242-4242"],
            is_principal=True,
        )

        self.non_principal_guest = MvPersonFactory(
            first_name="nonprincipal",
            last_name="guest",
            is_principal=False,
        )

        self.other_la_guest = MvPersonFactory(
            first_name="other_la",
            last_name="guest",
            is_principal=True,
        )

        self.ar_1 = MvAccommodationRequestFactory(
            ltla_name=["ltla_somerset"],
            person_id=[self.guest.id],
        )

        self.ar_2 = MvAccommodationRequestFactory(
            ltla_name=["other_ltla"],
            person_id=[self.other_la_guest.id],
        )

        self.ar_3 = MvAccommodationRequestFactory(
            ltla_name=["ltla_somerset"],
            person_id=[self.same_ltla_guest.id],
        )

        self.multi_ltla_guest = MvPersonFactory(
            first_name="multi",
            last_name="ltla",
            gender="Female",
            date_of_birth=datetime.date(1999, 1, 1),
            passport_id=["XX99999"],
            visa_status="Arrived",
            arrival_date=datetime.date(2025, 12, 10),
            visa_application_date_maximum=datetime.date(2030, 6, 20),
            application_number=["9999-9999-9999-9999"],
            is_principal=True,
        )

        self.multi_ltla_ar = MvAccommodationRequestFactory(
            ltla_name=["ltla_somerset", "another_ltla"],
            person_id=[self.multi_ltla_guest.id],
        )

        self.no_ar_guest = MvPersonFactory(
            first_name="no",
            last_name="ar",
            is_principal=True,
            accommodation_request=None,
        )

        self.empty_ltla_guest = MvPersonFactory(
            first_name="empty",
            last_name="ltla",
            is_principal=True,
        )

        self.empty_ltla_ar = MvAccommodationRequestFactory(
            ltla_name=[],
            person_id=[self.empty_ltla_guest.id],
        )

        self.null_ltla_guest = MvPersonFactory(
            first_name="null",
            last_name="ltla",
            is_principal=True,
        )

        self.null_ltla_ar = MvAccommodationRequestFactory(
            ltla_name=None,
            person_id=[self.null_ltla_guest.id],
        )

        self.pending_rr_guest = MvPersonFactory(
            first_name="pending",
            last_name="rr_guest",
            is_principal=True,
        )
        self.pending_rr_guest.save()

        self.ar_4 = MvAccommodationRequestFactory(
            ltla_name=["ltla_somerset"],
            person_id=[self.pending_rr_guest.id],
        )
        self.ar_4.save()

        rr = ReassignmentRequestFactory(outcome=ReassignmentRequest.Outcome.PENDING)
        rr.guests.set([self.pending_rr_guest])
        rr.save()

        self.guest.accommodation_request = self.ar_1
        self.other_la_guest.accommodation_request = self.ar_2
        self.same_ltla_guest.accommodation_request = self.ar_3
        self.multi_ltla_guest.accommodation_request = self.multi_ltla_ar
        self.empty_ltla_guest.accommodation_request = self.empty_ltla_ar
        self.null_ltla_guest.accommodation_request = self.null_ltla_ar
        self.guest.save()
        self.other_la_guest.save()
        self.same_ltla_guest.save()
        self.multi_ltla_guest.save()
        self.empty_ltla_guest.save()
        self.null_ltla_guest.save()

    def test_redirects_to_list_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:select-and-review-records-manual",
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/deduplication/guests/select-record/",
        )

    def test_renders_guest_list_with_correct_layout(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            )
        )

        self.assertContains(response, "Fix duplicate guest records")

        self.assertContains(
            response,
            "Select a record to review and deduplicate. "
            "You can use the filter panel to find records.",
        )

        self.assertContains(response, "Name")
        self.assertContains(response, "Sex")
        self.assertContains(response, "Date of birth")
        self.assertContains(response, "Passport number")
        self.assertContains(response, "Visa status")
        self.assertContains(response, "First arrival date")
        self.assertContains(response, "Latest visa application date")
        self.assertContains(response, "Unique Application Number (UAN)")
        self.assertNotContains(response, self.multi_ltla_guest.get_full_name())

    def test_renders_guest_list_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            )
        )

        self.assertContains(response, self.guest.get_full_name())
        self.assertContains(response, self.guest.gender)
        self.assertContains(response, self.guest.date_of_birth.strftime("%-d %b %Y"))
        self.assertContains(response, self.guest.passport_id[0])
        self.assertContains(response, self.guest.visa_status)
        self.assertContains(response, self.guest.arrival_date.strftime("%-d %b %Y"))
        self.assertContains(response, self.guest.visa_status)
        self.assertContains(
            response, self.guest.visa_application_date_maximum.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.guest.application_number[0])

    def test_does_not_render_non_principal_guest(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            )
        )

        self.assertNotContains(
            response,
            self.non_principal_guest.first_name
            + " "
            + self.non_principal_guest.last_name,
        )

    def test_renders_guest_with_no_accommodation_request(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            )
        )

        self.assertContains(response, self.no_ar_guest.get_full_name())

    def test_renders_guest_with_empty_ltla_name(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            )
        )

        self.assertContains(response, self.empty_ltla_guest.get_full_name())

    def test_renders_guest_with_null_ltla_name(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            )
        )

        self.assertContains(response, self.null_ltla_guest.get_full_name())

    def test_renders_only_ltla_records_matching_selected_guest(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
        )

        self.assertContains(
            response,
            self.guest.get_full_name(),
        )
        self.assertContains(
            response,
            self.same_ltla_guest.get_full_name(),
        )
        self.assertContains(
            response,
            self.other_la_guest.get_full_name(),
        )

        self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {
                "select-record-guest_record": self.guest.id,
                "SelectAndReviewRecordsFormWizard-current_step": (
                    SelectAndReviewRecordsStep.SELECT_RECORD
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
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

        self.assertContains(
            response,
            self.same_ltla_guest.get_full_name(),
        )
        self.assertNotContains(
            response,
            self.other_la_guest.get_full_name(),
        )

    def test_does_not_render_guest_with_pending_reassignment_request(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            )
        )

        self.assertNotContains(response, self.pending_rr_guest.get_full_name())
