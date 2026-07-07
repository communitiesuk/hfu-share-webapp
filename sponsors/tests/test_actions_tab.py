import http
from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.tests.factories import SponsorDuplicateGroupFactory
from ontology.models import MvVolunteer
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import get_admin_user
from webapp.mixins import SummaryListTestCaseMixin


class SponsorsActionsTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()
        self.sponsor = MvVolunteerFactory(
            first_name="LA Sponsor",
            last_name="Spon",
        )

        self.first_sponsor = MvVolunteerFactory(
            first_name="testfirstname",
            last_name="testlastname",
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
            first_name="test2firstname",
            last_name="test2lastname",
            sex="Male",
            date_of_birth=datetime(1981, 6, 10, tzinfo=timezone.utc),
            email="test2@example.com",
            phone_number=["04467123455"],
            residential_postcodes=["NW1 1WN"],
            flag_unsuitable=False,
            is_principal=True,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

        self.further_duped_sponsor = MvVolunteerFactory(
            first_name="test3firstname",
            last_name="test3lastname",
            is_principal=False,
        )

        self.new_principal_sponsor = MvVolunteerFactory(
            first_name="test2firstname",
            last_name="test2lastname",
            sex="Male",
            date_of_birth=datetime(1981, 6, 10, tzinfo=timezone.utc),
            email="test2@example.com",
            phone_number=["04467123455"],
            residential_postcodes=["NW1 1WN"],
            flag_unsuitable=False,
            is_principal=True,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

        sponsor_duplicate_group = SponsorDuplicateGroupFactory.create(
            principal_record=self.new_principal_sponsor,
            created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        sponsor_duplicate_group.sponsors.set(
            [self.further_duped_sponsor, self.second_sponsor]
        )
        sponsor_duplicate_group.save()

        sponsor_duplicate_group_further = SponsorDuplicateGroupFactory.create(
            principal_record=self.further_duped_sponsor,
            created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        sponsor_duplicate_group_further.sponsors.set(
            [self.first_sponsor, self.second_sponsor]
        )
        sponsor_duplicate_group_further.save()

    def test_admin_user_is_allowed_access(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-actions",
                args=[self.sponsor.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_records_not_from_dedupes_show_no_actions(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-actions",
                args=[self.sponsor.pk],
            )
        )
        self.assertContains(response, "There are no actions available")

    def test_principal_records_created_from_dedupes_show_dupe_record_names(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-actions",
                args=[self.new_principal_sponsor.pk],
            )
        )

        self.assertContains(
            response,
            "Delete this record and restore separate records for",
        )

        self.assertContains(response, "test3firstname test3lastname")

        self.assertContains(response, "test2firstname test2lastname")

        self.assertContains(
            response,
            f'<a href="{
                reverse(
                    "deduplication:sponsors:undo-deduplication-records-manual-step",
                    kwargs={
                        "step": "view-duplicate-records",
                        "id": str(self.new_principal_sponsor.id),
                    },
                )
            }"',
        )

    def test_records_part_of_further_dedupes_cannot_be_undone(self):
        self.second_new_principal_sponsor = MvVolunteerFactory(
            first_name="test2firstname",
            last_name="test3lastname",
            sex="Female",
            date_of_birth=datetime(1997, 11, 11, tzinfo=timezone.utc),
            age=26,
            email="tes4t@example.com",
            phone_number=["01111160698"],
            residential_postcodes=["OX1 1OX"],
            flag_unsuitable=False,
            is_principal=True,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

        self.new_principal_sponsor.is_principal = False
        self.new_principal_sponsor.save()

        self.another_sponsor = MvVolunteerFactory(
            first_name="test3firstname",
            last_name="test3lastname",
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

        further_sponsor_duplicate_group = SponsorDuplicateGroupFactory.create(
            principal_record=self.second_new_principal_sponsor,
            created_at=datetime(2027, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        further_sponsor_duplicate_group.sponsors.set(
            [self.new_principal_sponsor, self.another_sponsor]
        )
        further_sponsor_duplicate_group.save()

        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-actions",
                args=[self.new_principal_sponsor.pk],
            )
        )

        self.assertContains(
            response,
            "This deduplication cannot yet be undone due to a "
            "further deduplication. To restore this record, "
            "first undo the deduplication from the",
        )

        self.assertContains(response, "test2firstname test3lastname")


class GuestsActionsBlockedByMultiLaAccommodationRequestTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()

        self.first_sponsor = MvVolunteerFactory(is_principal=True)
        self.second_sponsor = MvVolunteerFactory(is_principal=True)

        self.ar = MvAccommodationRequestFactory(
            ltla_name=["Barking and Dagenham"],
        )
        self.principal_sponsor = MvVolunteerFactory(
            is_principal=True,
        )
        self.ar.primary_sponsor = self.principal_sponsor
        self.ar.save()

        self.dup_group = SponsorDuplicateGroupFactory.create(
            principal_record=self.principal_sponsor,
        )
        self.dup_group.sponsors.set([self.first_sponsor, self.second_sponsor])
        self.dup_group.save()

    def _get_actions_response(self):
        user = get_admin_user()
        self.client.force_login(user)
        return self.client.get(
            reverse("sponsors:detail-actions", args=[self.principal_sponsor.pk])
        )

    def _unmerge_url(self):
        return reverse(
            "deduplication:sponsors:undo-deduplication-records-manual-step",
            kwargs={
                "step": "view-duplicate-records",
                "id": str(self.principal_sponsor.id),
            },
        )

    def test_principal_records_with_single_la_ar_show_undo_action(
        self,
    ):
        response = self._get_actions_response()

        self.assertContains(response, f'<a href="{self._unmerge_url()}"')

    def test_principal_records_with_multi_la_ar_do_not_show_undo_action(
        self,
    ):
        self.ar.ltla_name = ["Barking and Dagenham", "Camden"]
        self.ar.save()

        response = self._get_actions_response()

        self.assertNotContains(response, f'<a href="{self._unmerge_url()}"')
        self.assertContains(
            response,
            "This sponsor is linked to multiple local authorities (LAs) so "
            "deduplication cannot be undone.",
        )
