from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.tests.factories import GuestDuplicateGroupFactory
from deduplication.views import UndoDeduplicationRecordsStep
from ontology.tests.factories import (
    MvPersonFactory,
)
from user_management.tests.base import get_admin_user
from webapp.mixins import SummaryListTestCaseMixin


class UndoDeduplicationGuestDeduplicatedRecordsRestoredViewTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()

        self.first_guest = MvPersonFactory(
            first_name="test1firstname",
            last_name="test1lastname",
            gender="Female",
            date_of_birth=datetime(1999, 11, 11, tzinfo=timezone.utc),
            email=["test1@example.com"],
            phone=["07777777777"],
            passport_id=["XX88888"],
            visa_status="Arrived",
            arrival_date=datetime(2025, 12, 10, tzinfo=timezone.utc),
            visa_application_date_maximum=datetime(2030, 6, 20, tzinfo=timezone.utc),
            application_number=["4242-4242-4242-4242"],
            is_principal=True,
        )

        self.second_guest = MvPersonFactory(
            first_name="test2firstname",
            last_name="test2lastname",
            gender="Male",
            date_of_birth=datetime(1989, 6, 6, tzinfo=timezone.utc),
            email=["test2@example.com"],
            phone=["07888888888"],
            passport_id=["XX99999"],
            visa_status="Issued",
            arrival_date=datetime(2035, 9, 19, tzinfo=timezone.utc),
            visa_application_date_maximum=datetime(2032, 3, 3, tzinfo=timezone.utc),
            application_number=["9999-9999-9999-9999"],
            is_principal=True,
        )

        self.new_principal_guest = MvPersonFactory(
            first_name="test2firstname",
            last_name="test1lastname",
            gender="Male",
            date_of_birth=datetime(1989, 6, 6, tzinfo=timezone.utc),
            email=["test2@example.com"],
            phone=["07888888888"],
            passport_id=["XX99999"],
            visa_status="Issued",
            arrival_date=datetime(2035, 9, 19, tzinfo=timezone.utc),
            visa_application_date_maximum=datetime(2032, 3, 3, tzinfo=timezone.utc),
            application_number=["9999-9999-9999-9999"],
            is_principal=True,
        )

        guest_duplicate_group = GuestDuplicateGroupFactory.create(
            principal_record=self.new_principal_guest,
            created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        guest_duplicate_group.guests.set([self.first_guest, self.second_guest])
        guest_duplicate_group.save()

    def test_undo_deduplication_guest_and_host_records_displays_correct_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        session = self.client.session
        session["wizard_UndoDeduplicationRecordsFormWizard"] = {
            "step": UndoDeduplicationRecordsStep.DEDUPLICATED_RECORDS_RESTORED,
            "step_data": {},
            "step_files": {},
            "extra_data": {
                "deduplication_data": {
                    "principal_name": self.new_principal_guest.get_full_name(),
                    "deduplicated_guest_data": [
                        {
                            "url": reverse(
                                "guests:detail-overview", args=[self.first_guest.pk]
                            ),
                            "name": self.first_guest.get_full_name(),
                        },
                        {
                            "url": reverse(
                                "guests:detail-overview",
                                args=[self.second_guest.pk],
                            ),
                            "name": self.second_guest.get_full_name(),
                        },
                    ],
                    "formatted_deduplicated_guests": (
                        f"{self.first_guest.get_full_name()} "
                        f"and {self.second_guest.get_full_name()}"
                    ),
                }
            },
        }
        session.save()

        response = self.client.get(
            reverse(
                "deduplication:guests:complete-undo-deduplication-records-manual-step",
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

        self.assertContains(response, "You have restored 2 guest records")

        self.assertContains(
            response,
            f"{self.first_guest.get_full_name()} and "
            f"{self.second_guest.get_full_name()} "
            f"have been restored and the principal record "
            f"{self.new_principal_guest.get_full_name()} was deleted.",
        )

        self.assertContains(response, "Deduplicated records restored")

        self.assertContains(response, "Review restored records")

        self.assertContains(
            response,
            "Review the restored guest records and linked accommodation requests.",
        )

        self.assertContains(
            response,
            '<a class="govuk-button govuk-button--secondary" '
            'href="/guests/">Back to list of guests</a>',
            html=True,
        )
