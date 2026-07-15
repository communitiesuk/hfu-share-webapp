import http.client
from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.tests.factories import SponsorDuplicateGroupFactory
from ontology.models import CheckType, DevCheckV2
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import get_admin_user, get_da_user, get_la_user
from webapp.mixins import SummaryListTestCaseMixin


class SponsorsLinkedRecordsTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()
        self.sponsor = MvVolunteerFactory(
            first_name="Test",
            last_name="Sponsor",
            date_of_birth="2002-06-03",
            sex="Female",
            email="testemail",
            phone_number=["0123456789"],
            family_situation="Single",
            passport_details=["123456"],
            is_eoi=True,
            is_sponsor=False,
            is_principal=True,
        )
        self.dup_sponsor_one = MvVolunteerFactory(is_principal=False)
        self.dup_sponsor_two = MvVolunteerFactory(is_principal=False)
        self.dup_principal_sponsor = MvVolunteerFactory(
            first_name="Test",
            last_name="Principal",
            is_principal=True,
        )
        self.dup_group = SponsorDuplicateGroupFactory(
            principal_record=self.dup_principal_sponsor,
            created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        self.dup_group.sponsors.set([self.dup_sponsor_one, self.dup_sponsor_two])
        self.dup_group.save()
        self.dbs_check = DevCheckV2Factory(
            active=True,
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        self.dbs_check.sponsor.set([self.sponsor])

        self.ltla_sponsor = MvVolunteerFactory(
            first_name="LA Sponsor",
            last_name="Spon",
        )
        self.ltla_accommodation = MvAccommodationFactory(
            full_address="Somerset LTLA Address",
            ltla_name="ltla_somerset",
        )
        self.ltla_accommodation.hosts.set([self.ltla_sponsor.id])

        self.da_sponsor = MvVolunteerFactory(
            first_name="DA Sponsor",
            last_name="Spon",
        )
        self.da_accommodation = MvAccommodationFactory(
            full_address="Scotland DA address",
            ltla_name="Aberdeenshire",
            utla_name="Aberdeenshire",
        )
        self.da_accommodation.hosts.set([self.da_sponsor.id])

        self.archived_sponsor = MvVolunteerFactory(
            first_name="Archived",
            last_name="Sponsor",
            is_principal=True,
            is_archived=True,
            archived_at=datetime(2025, 12, 25, tzinfo=timezone.utc),
        )

    def test_la_user_is_allowed_access(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.ltla_sponsor.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_denied_access_to_sponsor_with_different_ltla(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_da_user_is_allowed_access(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.da_sponsor.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_denied_access_to_other_da_accom(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_archived_sponsor_cannot_be_viewed(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.archived_sponsor.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_overview_should_display_sponsor_first_name(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(
            response, "First name", self.sponsor.first_name
        )

    def test_overview_should_display_sponsor_last_name(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(response, "Last name", self.sponsor.last_name)

    def test_overview_should_display_sponsor_date_of_birth(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(response, "Date of birth", "3 June 2002")

    def test_overview_should_display_sponsor_sex(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(response, "Sex", self.sponsor.sex)

    def test_overview_should_display_sponsor_email(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(response, "Email", self.sponsor.email)

    def test_overview_should_display_sponsor_phone_number(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(
            response, "Phone number", self.sponsor.phone_number[0]
        )

    def test_overview_should_display_sponsor_relationship_status(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(
            response, "Relationship status", self.sponsor.family_situation
        )

    def test_overview_should_display_sponsor_dbs_check_status(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(
            response, "DBS check status", self.dbs_check.check_status.label
        )

    def test_overview_should_display_sponsor_passport_number(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(
            response, "Passport number", self.sponsor.passport_details[0]
        )

    def test_overview_should_display_sponsor_is_eoi_host(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(response, "Host", "Yes")

    def test_overview_should_display_sponsor_is_sponsor(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(response, "Sponsor", "No")

    def test_overview_should_display_dbs_check_failed_if_failed_check_recorded(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.dbs_check.check_status = DevCheckV2.CheckStatus.FAILED
        self.dbs_check.save()

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(response, "DBS check status", "Failed")

    def test_should_display_dbs_check_in_progress_if_in_progress_check_recorded(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.dbs_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.dbs_check.save()

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(response, "DBS check status", "In progress")

    def test_displays_dbs_check_no_longer_needed_if_no_longer_needed_check_recorded(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        self.dbs_check.check_status = DevCheckV2.CheckStatus.NO_LONGER_NEEDED
        self.dbs_check.save()

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(
            response, "DBS check status", "No longer needed"
        )

    def test_should_display_dbs_check_passed_if_passed_check_recorded(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.dbs_check.save()

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(response, "DBS check status", "Passed")

    def test_overview_should_display_dbs_check_not_started_if_no_checks_recorded(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.dbs_check.sponsor.set([])

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Overview")
        self.assertSummaryListContainsRow(response, "DBS check status", "Not started")

    def test_overview_should_display_change_link_only_when_is_principal(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.dup_principal_sponsor.pk],
            )
        )

        self.assertContains(response, "Change", html=True)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.dup_sponsor_one.pk],
            )
        )

        self.assertNotContains(response, "Change", html=True)

    def test_duplicate_label_renders_for_duplicate_sponsors_only(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.dup_sponsor_one.pk],
            )
        )

        self.assertContains(response, "Duplicate")

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.dup_principal_sponsor.pk],
            )
        )

        self.assertNotContains(response, "Duplicate")

    def test_duplicate_message_with_principal_record_renders_for_duplicate_sponsors(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.dup_sponsor_one.pk],
            )
        )

        self.assertContains(
            response,
            "This record is a duplicate and cannot be changed. "
            "It was combined with another duplicate to create a new principal",
        )

        self.assertRegex(
            response.content.decode(),
            r"<a href=/sponsors/\d+/overview>"
            f"sponsor and host record for "
            f"{self.dup_principal_sponsor.full_name}"
            f"</a>",
        )

        # self.assertContains(
        #     response,
        #     "If this was a mistake you can undo the deduplication "
        #     "from the actions tab.",
        # )

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.dup_principal_sponsor.pk],
            )
        )

        self.assertNotContains(
            response, "This record is a duplicate and cannot be changed."
        )
