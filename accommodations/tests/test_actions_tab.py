import http
from datetime import datetime, timezone

from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.tests.factories import (
    AccommodationDuplicateGroupFactory,
)
from ontology.tests.base import MvAccommodationTestCase
from ontology.tests.factories import (
    MvAccommodationFactory,
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


class AccommodationsActionsTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, MvAccommodationTestCase
):
    def setUp(self):
        super().setUp()
        self.accommodation = MvAccommodationFactory(
            full_address="123 Street",
            ltla_name="ltla_somerset",
        )

        self.new_principal_accommodation = MvAccommodationFactory(
            full_address="123 Street",
            is_principal=True,
            ltla_name="ltla_somerset",
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

    def test_admin_user_is_allowed_access(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-actions",
                args=[self.accommodation.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_not_allowed_access(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-actions",
                args=[self.accommodation.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_da_user_is_not_allowed_access(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-actions",
                args=[self.accommodation.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_ukvi_user_is_not_allowed_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-actions",
                args=[self.accommodation.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_ops_user_is_not_allowed_access(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-actions",
                args=[self.accommodation.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_service_support_user_is_not_allowed_access(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-actions",
                args=[self.accommodation.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_records_not_from_dedupes_show_no_actions(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-actions",
                args=[self.accommodation.pk],
            )
        )
        self.assertContains(response, "There are no actions available")

    def test_principal_records_created_from_dedupes_show_dupe_record_names(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-actions",
                args=[self.new_principal_accommodation.pk],
            )
        )

        self.assertContains(
            response,
            "Delete this record and restore separate records for",
        )

        self.assertContains(response, "123 Street")

        self.assertContains(response, "456 Avenue")

        self.assertContains(
            response,
            f'<a href="{
                reverse(
                    "deduplication:accommodations:undo-deduplication-records-manual-step",
                    kwargs={
                        "step": "view-duplicate-records",
                        "id": str(self.new_principal_accommodation.id),
                    },
                )
            }"',
        )

    def test_records_part_of_further_dedupes_cannot_be_undone(self):
        self.second_new_principal_accommodation = MvAccommodationFactory(
            full_address="123 Street",
            is_principal=True,
        )

        self.new_principal_accommodation.is_principal = False
        self.new_principal_accommodation.save()
        self.ltla_two_a_accommodation.full_address = "789 Way"
        self.ltla_two_a_accommodation.save()

        further_accommodation_duplicate_group = (
            AccommodationDuplicateGroupFactory.create(
                principal_record=self.second_new_principal_accommodation,
                created_at=datetime(2027, 1, 1, 9, 30, tzinfo=timezone.utc),
            )
        )
        further_accommodation_duplicate_group.accommodations.set(
            [self.new_principal_accommodation, self.ltla_two_a_accommodation]
        )
        further_accommodation_duplicate_group.save()

        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-actions",
                args=[self.new_principal_accommodation.pk],
            )
        )

        self.assertContains(
            response,
            "This deduplication cannot yet be undone due to a "
            "further deduplication. To restore this record, "
            "first undo the deduplication from the",
        )

        self.assertContains(response, "123 Street")
