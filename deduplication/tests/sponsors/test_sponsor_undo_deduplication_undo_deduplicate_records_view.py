from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.tests.factories import SponsorDuplicateGroupFactory
from deduplication.views import UndoDeduplicationRecordsStep
from ontology.models import MvVolunteer
from ontology.tests.factories import (
    MvVolunteerFactory,
)
from user_management.tests.base import get_admin_user
from webapp.mixins import SummaryListTestCaseMixin


class UndoDeduplicationSponsorUndoDeduplicatedRecordsViewTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()

        self.first_sponsor = MvVolunteerFactory(
            first_name="test1firstname",
            last_name="test1lastname",
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

        self.sponsor_duplicate_group = SponsorDuplicateGroupFactory.create(
            principal_record=self.new_principal_sponsor,
            created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        self.sponsor_duplicate_group.sponsors.set(
            [self.first_sponsor, self.second_sponsor]
        )
        self.sponsor_duplicate_group.save()

    def test_view_duplicate_sponsor_and_host_records_redirects_to_undo_deduplicate_view(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:sponsors:undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                    "id": self.new_principal_sponsor.pk,
                },
            ),
            {
                "UndoDeduplicationRecordsFormWizard-current_step": (
                    UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                )
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRegex(
            response.url,
            r"/deduplication"
            r"/sponsors/undo-deduplicate-records/\d+/",
        )

    def test_undo_deduplicate_sponsor_and_host_records_displays_correct_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:sponsors:undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                    "id": self.new_principal_sponsor.pk,
                },
            ),
            {
                "UndoDeduplicationRecordsFormWizard-current_step": (
                    UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                )
            },
            follow=True,
        )

        self.assertContains(response, "Undo deduplicate sponsor and host records")

        self.assertContains(
            response,
            "Records deduplicated to create new principal sponsor and host record for "
            f"{self.new_principal_sponsor.full_name}",
        )

        self.assertContains(response, self.first_sponsor.full_name)
        self.assertContains(response, self.first_sponsor.sex)
        self.assertContains(response, "11 Nov 1999")
        self.assertContains(response, self.first_sponsor.email)
        self.assertContains(response, self.first_sponsor.phone_number[0])

        self.assertContains(response, self.second_sponsor.full_name)
        self.assertContains(response, self.second_sponsor.sex)
        self.assertContains(response, "10 Jun 1981")
        self.assertContains(response, self.second_sponsor.email)
        self.assertContains(response, self.second_sponsor.phone_number[0])

        self.assertContains(
            response,
            f"This action will permanently delete the principal record for "
            f"{self.new_principal_sponsor.full_name}. Any changes to the principal "
            f"record for {self.new_principal_sponsor.full_name} will be lost.",
        )

        self.assertContains(
            response,
            f"This record was created on 1 January 2026 at 9:30am by "
            f"deduplicating two separate records. The original records for "
            f"{self.first_sponsor.full_name} and "
            f"{self.new_principal_sponsor.full_name} will be restored.",
        )

        self.assertContains(
            response,
            "Are you sure you want to delete this sponsor and host record and "
            "restore the original records?",
        )

        self.assertContains(
            response,
            '<button class="govuk-button"type="submit">'
            "Yes, undo deduplication"
            "</button>",
            html=True,
        )

        self.assertRegex(
            response.content.decode(),
            r'<a class="govuk-button govuk-button--secondary" '
            r'href="/sponsors/\d+/actions\?reset=true">No, return to the record</a>',
        )
