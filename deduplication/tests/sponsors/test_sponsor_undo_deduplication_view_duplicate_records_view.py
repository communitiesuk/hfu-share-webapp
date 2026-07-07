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


class UndoDeduplicationSponsorViewDeduplicatedRecordsViewTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()

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
        sponsor_duplicate_group.sponsors.set([self.first_sponsor, self.second_sponsor])
        sponsor_duplicate_group.save()

    def test_view_duplicate_sponsor_and_host_records_displays_correct_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:sponsors:undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                    "id": self.new_principal_sponsor.pk,
                },
            )
        )

        self.assertContains(response, "View duplicate sponsor and host records")

        self.assertContains(
            response,
            "Records deduplicated to create new principal sponsor and host record for "
            f"{self.new_principal_sponsor.first_name} "
            f"{self.new_principal_sponsor.last_name}",
        )

        self.assertContains(
            response,
            self.first_sponsor.first_name + " " + self.first_sponsor.last_name,
        )
        self.assertContains(response, self.first_sponsor.sex)
        self.assertContains(response, "11 Nov 1999")
        self.assertContains(response, self.first_sponsor.email)
        self.assertContains(response, self.first_sponsor.phone_number[0])

        self.assertContains(
            response,
            self.second_sponsor.first_name + " " + self.second_sponsor.last_name,
        )
        self.assertContains(response, self.second_sponsor.sex)
        self.assertContains(response, "10 Jun 1981")
        self.assertContains(response, self.second_sponsor.email)
        self.assertContains(response, self.second_sponsor.phone_number[0])

        self.assertContains(
            response,
            '<button class="govuk-button"type="submit">Undo deduplication</button>',
            html=True,
        )

        self.assertRegex(
            response.content.decode(),
            r'<a class="govuk-link" href="/sponsors/\d+/actions\?reset=true">'
            r"Cancel</a>",
        )
