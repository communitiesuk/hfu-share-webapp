import http.client
from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.tests.factories import AccommodationDuplicateGroupFactory
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvUkPostcodeFactory,
)
from user_management.tests.base import get_admin_user, get_da_user, get_la_user
from webapp.mixins import SummaryListTestCaseMixin


class AccommodationOverviewTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()
        self.accommodation = MvAccommodationFactory(
            full_address="Street name, City, County",
            postcode=MvUkPostcodeFactory(
                postcode="A123BC", postcode_formatted="A12 3BC"
            ),
            current_capacity="6",
            availability_start_date="2025-01-01",
            availability_end_date="2026-01-01",
            wheelchair_accessible=True,
            ltla_name="LTLA",
            utla_name="UTLA",
        )
        self.ltla_accommodation = MvAccommodationFactory(
            full_address="Somerset LTLA Address",
            ltla_name="ltla_somerset",
        )
        self.da_accommodation = MvAccommodationFactory(
            full_address="Scotland DA address",
            ltla_name="Aberdeenshire",
            utla_name="Aberdeenshire",
        )

        self.dup_record_one = MvAccommodationFactory(is_principal=False)
        self.dup_record_two = MvAccommodationFactory(is_principal=False)
        self.dup_principal_record = MvAccommodationFactory(
            full_address="123 Street",
            is_principal=True,
        )
        self.dup_group = AccommodationDuplicateGroupFactory(
            principal_record=self.dup_principal_record,
            created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        self.dup_group.accommodations.set([self.dup_record_one, self.dup_record_two])
        self.dup_group.save()

        self.archived_accommodation = MvAccommodationFactory(
            full_address="Archived address",
            is_principal=True,
            is_archived=True,
            archived_at=datetime(2025, 12, 25, tzinfo=timezone.utc),
        )

    def test_archived_accommodation_cannot_be_viewed(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.archived_accommodation.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_overview_should_display_accomm_full_address(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(
            response, "Address", self.accommodation.full_address
        )

    def test_overview_should_display_accomm_postcode_formatted(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(
            response, "Postcode", self.accommodation.postcode.postcode_formatted
        )

    def test_overview_should_handle_accomm_with_no_postcode_formatted(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.accommodation.postcode = MvUkPostcodeFactory(
            postcode="A123BC", postcode_formatted=None
        )
        self.accommodation.save()

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(
            response, "Postcode", self.accommodation.postcode.postcode
        )

    def test_overview_should_handle_accomm_with_no_postcode(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.accommodation.postcode = MvUkPostcodeFactory(
            postcode=None, postcode_formatted=None
        )
        self.accommodation.save()

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(response, "Postcode", "No value")

    def test_overview_should_handle_accomm_with_none_postcode(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.accommodation.postcode = None
        self.accommodation.save()

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(response, "Postcode", "No value")

    def test_overview_should_display_accomm_current_capacity(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(
            response, "Current capacity", self.accommodation.current_capacity
        )

    def test_overview_should_display_accomm_availability_start_date(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(
            response,
            "Availability start date",
            "1 January 2025",
        )

    def test_overview_should_display_accomm_availability_end_date(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(
            response, "Availability end date", "1 January 2026"
        )

    def test_overview_should_display_accomm_wheelchair_accessible(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(response, "Wheelchair accessible", "Yes")

    def test_overview_should_display_accomm_ltla_name(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(
            response, "Lower tier LA", self.accommodation.ltla_name
        )

    def test_overview_should_display_accomm_utla_name(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(
            response, "Upper tier LA", self.accommodation.utla_name
        )

    def test_la_user_is_allowed_access(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                kwargs={"pk": self.ltla_accommodation.id},
            )
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_denied_access_to_accom_with_different_ltla(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                kwargs={"pk": self.da_accommodation.id},
            )
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_da_user_is_allowed_access(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                kwargs={"pk": self.da_accommodation.id},
            )
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_denied_access_to_other_da_accom(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                kwargs={"pk": self.ltla_accommodation.id},
            )
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_overview_should_display_change_link_only_when_is_principal(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.dup_principal_record.pk],
            )
        )

        self.assertContains(response, "Change", html=True)

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.dup_record_one.pk],
            )
        )

        self.assertNotContains(response, "Change", html=True)

    def test_duplicate_label_renders_for_duplicate_guests_only(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.dup_record_one.pk],
            )
        )

        self.assertContains(response, "Duplicate")

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.dup_principal_record.pk],
            )
        )

        self.assertNotContains(response, "Duplicate")

    def test_duplicate_message_with_principal_record_renders_for_duplicate_guests(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.dup_record_one.pk],
            )
        )

        self.assertContains(
            response,
            "This record is a duplicate and cannot be changed. "
            "It was combined with another duplicate to create a new principal",
        )

        self.assertRegex(
            response.content.decode(),
            r"<a class=\"govuk-link\" href=/accommodations/\d+/overview>"
            f"accommodation record for "
            f"{self.dup_principal_record.full_address}"
            f"</a>",
        )

        self.assertContains(
            response,
            "If this was a mistake you can undo the deduplication "
            "from the actions tab.",
        )

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.dup_principal_record.pk],
            )
        )

        self.assertNotContains(
            response, "This record is a duplicate and cannot be changed."
        )
