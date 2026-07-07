from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.views import UndoDeduplicationRecordsStep
from ontology.models import MvVolunteer
from ontology.tests.factories import (
    MvVolunteerFactory,
)
from user_management.tests.base import get_admin_user
from webapp.mixins import SummaryListTestCaseMixin


class UndoDeduplicationSponsorDeduplicatedRecordsRestoredViewTestCase(
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

    def test_undo_deduplication_sponsor_and_host_records_displays_correct_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        session = self.client.session
        session["wizard_UndoDeduplicationRecordsFormWizard"] = {
            "step": UndoDeduplicationRecordsStep.DEDUPLICATED_RECORDS_RESTORED,
            "step_data": {},
            "step_files": {},
            "extra_data": {
                "deduplication_data": {
                    "principal_name": self.new_principal_sponsor.full_name,
                    "deduplicated_sponsor_data": [
                        {
                            "url": reverse(
                                "sponsors:detail-overview", args=[self.first_sponsor.pk]
                            ),
                            "name": self.first_sponsor.full_name,
                        },
                        {
                            "url": reverse(
                                "sponsors:detail-overview",
                                args=[self.second_sponsor.pk],
                            ),
                            "name": self.second_sponsor.full_name,
                        },
                    ],
                    "formatted_deduplicated_sponsors": (
                        f"{self.first_sponsor.full_name} "
                        f"and "
                        f"{self.second_sponsor.full_name}"
                    ),
                }
            },
        }
        session.save()

        response = self.client.get(
            reverse(
                "deduplication:sponsors:complete-undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.DEDUPLICATED_RECORDS_RESTORED,
                },
            ),
            {
                "UndoDeduplicationRecordsFormWizard-current_step": (
                    UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                )
            },
        )

        self.assertContains(response, "Success")

        self.assertContains(response, "You have restored 2 sponsor and host records")

        self.assertContains(
            response,
            f"{self.first_sponsor.full_name} and {self.second_sponsor.full_name} "
            f"have been restored and the principal record "
            f"{self.new_principal_sponsor.full_name} was deleted.",
        )

        self.assertContains(response, "Deduplicated records restored")

        self.assertContains(response, "Review restored records")

        self.assertContains(
            response,
            "Review the restored sponsor and host records and linked accommodation"
            " requests.",
        )

        self.assertContains(
            response,
            '<a class="govuk-button govuk-button--secondary" '
            'href="/sponsors/">Back to list of sponsors and hosts</a>',
            html=True,
        )
