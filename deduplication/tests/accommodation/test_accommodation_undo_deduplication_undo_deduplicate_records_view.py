from datetime import datetime, timezone

from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.tests.factories import (
    AccommodationDuplicateGroupFactory,
)
from deduplication.views import UndoDeduplicationRecordsStep
from ontology.tests.base import MvAccommodationTestCase
from ontology.tests.factories import (
    MvAccommodationFactory,
)
from user_management.tests.base import get_admin_user
from webapp.mixins import SummaryListTestCaseMixin


class UndoDeduplicationSponsorUndoDeduplicatedRecordsViewTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, MvAccommodationTestCase
):
    def setUp(self):
        super().setUp()

        self.new_principal_accommodation = MvAccommodationFactory(
            full_address="123 Street",
            is_principal=True,
        )

        self.ltla_one_a_accommodation.full_address = "123 Street"
        self.ltla_one_a_accommodation.save()
        self.ltla_one_b_accommodation.full_address = "456 Avenue"
        self.ltla_one_b_accommodation.save()

        accommodation_duplicate_group = AccommodationDuplicateGroupFactory.create(
            principal_record=self.new_principal_accommodation,
            created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        accommodation_duplicate_group.accommodations.set(
            [self.ltla_one_a_accommodation, self.ltla_one_b_accommodation]
        )
        accommodation_duplicate_group.save()

    def test_view_duplicate_accommodation_records_redirects_to_undo_deduplicate_view(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:accommodations:undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                    "id": self.new_principal_accommodation.pk,
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
            r"/accommodations/undo-deduplication/undo-deduplicate-records/\d+/",
        )

    def test_undo_deduplicate_accommodation_records_displays_correct_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "deduplication:accommodations:undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                    "id": self.new_principal_accommodation.pk,
                },
            ),
            {
                "UndoDeduplicationRecordsFormWizard-current_step": (
                    UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                )
            },
            follow=True,
        )

        self.assertContains(response, "Undo deduplicate accommodation records")

        self.assertContains(
            response,
            "Records deduplicated to create new principal accommodation record for "
            f"{self.new_principal_accommodation.full_address}",
        )

        self.assertContains(response, self.ltla_one_a_accommodation.full_address)
        self.assertContains(response, self.ltla_one_b_accommodation.full_address)

        self.assertContains(
            response,
            f"This action will permanently delete the principal record for "
            f"{self.new_principal_accommodation.full_address}. "
            f"Any changes to the principal "
            f"record for {self.new_principal_accommodation.full_address} will be lost.",
        )

        self.assertContains(
            response,
            f"This record was created on 1 January 2026 at 9:30am by "
            f"deduplicating two separate records. The original records for "
            f"{self.ltla_one_a_accommodation.full_address} and "
            f"{self.ltla_one_b_accommodation.full_address} will be restored.",
        )

        self.assertContains(
            response,
            "Are you sure you want to delete this accommodation record and "
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
            r'href="/accommodations/\d+/actions\?reset=true">'
            r"No, return to the record</a>",
        )
