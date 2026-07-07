from datetime import datetime, timezone

from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.tests.factories import AccommodationDuplicateGroupFactory
from deduplication.views import UndoDeduplicationRecordsStep
from ontology.tests.base import MvAccommodationTestCase
from ontology.tests.factories import (
    MvAccommodationFactory,
)
from user_management.tests.base import get_admin_user
from webapp.mixins import SummaryListTestCaseMixin


class UndoDeduplicationAccommodationViewDeduplicatedRecordsViewTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, MvAccommodationTestCase
):
    def setUp(self):
        super().setUp()

        self.new_principal_accommodation = MvAccommodationFactory(
            full_address="123 Street",
            is_principal=True,
        )

        accommodation_duplicate_group = AccommodationDuplicateGroupFactory.create(
            principal_record=self.new_principal_accommodation,
            created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        accommodation_duplicate_group.accommodations.set(
            [self.ltla_one_a_accommodation, self.ltla_one_b_accommodation]
        )
        accommodation_duplicate_group.save()

    def test_view_duplicate_accommodation_records_displays_correct_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:accommodations:undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                    "id": self.new_principal_accommodation.pk,
                },
            )
        )

        self.assertContains(response, "View duplicate accommodation records")

        self.assertContains(
            response,
            "Records deduplicated to create new principal accommodation record for "
            f"{self.new_principal_accommodation.full_address}",
        )

        self.assertContains(
            response,
            self.ltla_one_a_accommodation.full_address,
        )

        self.assertContains(
            response,
            self.ltla_one_b_accommodation.full_address,
        )

        self.assertContains(
            response,
            '<button class="govuk-button"type="submit">Undo deduplication</button>',
            html=True,
        )

        self.assertRegex(
            response.content.decode(),
            r'<a class="govuk-link" href="/accommodations/\d+/actions\?reset=true">'
            r"Cancel</a>",
        )
