from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.tests.factories import (
    GuestDuplicateGroupFactory,
)
from ontology.tests.factories import MvPersonFactory
from user_management.tests.base import get_admin_user


class GuestDeduplicationHistoryViewTest(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.first_guest = MvPersonFactory(
            first_name="test1firstname",
            last_name="test1lastname",
            gender="Female",
            date_of_birth=datetime(1999, 1, 1, tzinfo=timezone.utc),
            email=["test1@example.com"],
            phone=["07777777777"],
            passport_id=["XX88888"],
            visa_status="Issued",
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
            visa_status="Pending",
            arrival_date=datetime(2035, 9, 19, tzinfo=timezone.utc),
            visa_application_date_maximum=datetime(2032, 3, 3, tzinfo=timezone.utc),
            application_number=["9999-9999-9999-9999"],
            is_principal=True,
        )

        self.new_principal_values = {
            "first_name": self.first_guest.first_name,
            "last_name": self.first_guest.last_name,
        }

        self.duplicate_group = GuestDuplicateGroupFactory()
        self.duplicate_group.guests.add(self.first_guest, self.second_guest)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            self.new_principal_values, user=get_admin_user()
        )

    def test_history_view_shows_deduplication_event_on_first_guest(self):
        self.client.force_login(get_admin_user())

        response = self.client.get(
            reverse(
                "guests:detail-history",
                args=[self.first_guest.pk],
            )
        )
        self.assertContains(response, "Record deduplicated")
        self.assertContains(
            response,
            f"This record, and guest record {self.second_guest.get_full_name()}"
            f" were marked as duplicates. New principal record is"
            f" {self.duplicate_group.principal_record.get_full_name()}.",
        )

    def test_history_view_shows_deduplication_event_on_second_guest(self):
        self.client.force_login(get_admin_user())

        response = self.client.get(
            reverse(
                "guests:detail-history",
                args=[self.second_guest.pk],
            )
        )
        self.assertContains(response, "Record deduplicated")
        self.assertContains(
            response,
            f"This record, and guest record {self.first_guest.get_full_name()}"
            f" were marked as duplicates. "
            f"New principal record is "
            f"{self.duplicate_group.principal_record.get_full_name()}.",
        )

    def test_history_view_shows_deduplication_event_on_principal_guest(self):
        self.client.force_login(get_admin_user())

        response = self.client.get(
            reverse(
                "guests:detail-history",
                args=[self.duplicate_group.principal_record.pk],
            )
        )
        self.assertContains(response, "Record deduplicated")
        self.assertContains(
            response,
            f"This record was created after guest records "
            f"{self.first_guest.get_full_name()} and "
            f"{self.second_guest.get_full_name()} "
            f"were marked as duplicates.",
        )

    def test_history_view_shows_undo_deduplication_event_on_first_guest(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.duplicate_group.undo_deduplication(user=user)

        response = self.client.get(
            reverse("guests:detail-history", kwargs={"pk": self.first_guest.pk})
        )

        self.assertContains(response, "Deduplication undone")
        self.assertContains(
            response,
            f"This record, and guest record {self.second_guest.get_full_name()}"
            f" were restored as separate principal records. A principal record"
            f" combining data from both was deleted.",
        )

    def test_history_view_shows_undo_deduplication_event_on_second_guest(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.duplicate_group.undo_deduplication(user=user)

        response = self.client.get(
            reverse("guests:detail-history", kwargs={"pk": self.second_guest.pk})
        )

        self.assertContains(response, "Deduplication undone")
        self.assertContains(
            response,
            f"This record, and guest record {self.first_guest.get_full_name()}"
            f" were restored as separate principal records. A principal record"
            f" combining data from both was deleted.",
        )
