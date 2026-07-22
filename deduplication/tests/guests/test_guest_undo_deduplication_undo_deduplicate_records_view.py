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


class UndoDeduplicationGuestUndoDeduplicatedRecordsViewTestCase(
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

    def test_view_duplicate_guest_and_host_records_redirects_to_undo_deduplicate_view(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:guests:undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                    "id": self.new_principal_guest.pk,
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
            r"/guests/undo-deduplication/undo-deduplicate-records/\d+/",
        )

    def test_undo_deduplicate_guest_and_host_records_displays_correct_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:guests:undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                    "id": self.new_principal_guest.pk,
                },
            ),
            {
                "UndoDeduplicationRecordsFormWizard-current_step": (
                    UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                )
            },
            follow=True,
        )

        self.assertContains(response, "Undo deduplicate guest records")

        self.assertContains(
            response,
            "Records deduplicated to create new principal guest record for "
            f"{self.new_principal_guest.get_full_name()}",
        )

        self.assertContains(response, self.first_guest.get_full_name())
        self.assertContains(response, self.first_guest.gender)
        self.assertContains(
            response, self.first_guest.date_of_birth.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.first_guest.passport_id[0])
        self.assertContains(response, self.first_guest.visa_status)
        self.assertContains(
            response, self.first_guest.arrival_date.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.first_guest.visa_status)
        self.assertContains(
            response,
            self.first_guest.visa_application_date_maximum.strftime("%-d %b %Y"),
        )
        self.assertContains(response, self.first_guest.application_number[0])

        self.assertContains(response, self.second_guest.get_full_name())
        self.assertContains(response, self.second_guest.gender)
        self.assertContains(
            response, self.second_guest.date_of_birth.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.second_guest.passport_id[0])
        self.assertContains(response, self.second_guest.visa_status)
        self.assertContains(
            response, self.second_guest.arrival_date.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.second_guest.visa_status)
        self.assertContains(
            response,
            self.second_guest.visa_application_date_maximum.strftime("%-d %b %Y"),
        )
        self.assertContains(response, self.second_guest.application_number[0])

        self.assertContains(
            response,
            f"This action will permanently delete the principal record for "
            f"{self.new_principal_guest.get_full_name()}. Any changes to the principal "
            f"record for {self.new_principal_guest.get_full_name()} will be lost.",
        )

        self.assertContains(
            response,
            f"This record was created on 1 January 2026 at 9:30am by "
            f"deduplicating two separate records. The original records for "
            f"{self.first_guest.get_full_name()} and "
            f"{self.second_guest.get_full_name()} will be restored.",
        )

        self.assertContains(
            response,
            "Are you sure you want to delete this guest record and "
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
            r'href="/guests/\d+/actions\?reset=true">'
            r"No, return to the record</a>",
        )
