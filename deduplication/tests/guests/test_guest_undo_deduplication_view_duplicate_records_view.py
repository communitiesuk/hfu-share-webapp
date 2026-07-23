import http.client
from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.tests.factories import (
    GuestDuplicateGroupFactory,
)
from deduplication.views import UndoDeduplicationRecordsStep
from ontology.models import ReassignmentRequest
from ontology.tests.factories import (
    MvPersonFactory,
    ReassignmentRequestFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)
from webapp.mixins import SummaryListTestCaseMixin


class UndoDeduplicationGuestViewDeduplicatedRecordsViewTestCase(
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
        self.new_principal_ltla_guest = MvPersonFactory(
            pk="person-2",
            first_name="LTLA",
            last_name="Last",
            is_principal=True,
        )
        self.new_principal_da_guest = MvPersonFactory(
            pk="person-3",
            first_name="DA",
            last_name="Last",
            is_principal=True,
        )

        for new_principal_guest in [
            self.new_principal_guest,
            self.new_principal_ltla_guest,
            self.new_principal_da_guest,
        ]:
            guest_duplicate_group = GuestDuplicateGroupFactory.create(
                principal_record=new_principal_guest,
                created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
            )
            guest_duplicate_group.guests.set([self.first_guest, self.second_guest])
            guest_duplicate_group.save()

    def test_admin_user_is_allowed_access(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                    "id": self.new_principal_guest.pk,
                },
            )
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_not_allowed_access(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                    "id": self.new_principal_ltla_guest.pk,
                },
            )
        )
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_da_user_is_not_allowed_access(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                    "id": self.new_principal_da_guest.pk,
                },
            )
        )
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_ukvi_user_is_not_allowed_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                    "id": self.new_principal_guest.pk,
                },
            )
        )
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_ops_user_is_not_allowed_access(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                    "id": self.new_principal_guest.pk,
                },
            )
        )
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_service_support_user_is_not_allowed_access(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                    "id": self.new_principal_guest.pk,
                },
            )
        )
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_view_duplicate_guest_and_host_records_displays_correct_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                    "id": self.new_principal_guest.pk,
                },
            )
        )

        self.assertContains(response, "View duplicate guest records")

        self.assertContains(
            response,
            "Records deduplicated to create new principal guest record for "
            f"{self.new_principal_guest.get_full_name()}",
        )

        self.assertContains(
            response,
            '<div class="govuk-hint govuk-!-font-size-16 govuk-!-margin-top-1 '
            'govuk-!-margin-bottom-0">Duplicate</div>',
            count=2,
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
            '<button class="govuk-button"type="submit">Undo deduplication</button>',
            html=True,
        )

        self.assertRegex(
            response.content.decode(),
            r'<a class="govuk-link govuk-link--no-visited-state" '
            r'href="/guests/\d+/actions\?reset=true">'
            r"Cancel</a>",
        )


class UndoDeduplicationGuestWizardBlockedByReassignmentTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()

        self.first_guest = MvPersonFactory(is_principal=True)
        self.second_guest = MvPersonFactory(is_principal=True)
        self.principal_guest = MvPersonFactory(is_principal=True)

        self.dup_group = GuestDuplicateGroupFactory.create(
            principal_record=self.principal_guest,
            created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        self.dup_group.guests.set([self.first_guest, self.second_guest])
        self.dup_group.save()

        rr = ReassignmentRequestFactory(
            outcome=ReassignmentRequest.Outcome.ACCEPTED,
            responded_at=datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc),
        )
        rr.guests.set([self.principal_guest])

    def test_view_duplicate_guest_records_returns_404_when_undo_blocked_by_reassignment(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:guests:undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                    "id": self.principal_guest.pk,
                },
            )
        )

        self.assertEqual(response.status_code, 404)
