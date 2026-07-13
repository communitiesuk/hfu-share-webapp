from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from deduplication.tests.factories import AccommodationDuplicateGroupFactory
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import get_admin_user


class AccommodationDuplicateGroupUndoDeduplicationTestCase(TestCase):
    def test_should_remove_hosts_from_principal_on_undo(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        accommodation_one = MvAccommodationFactory(is_principal=True)
        accommodation_one.hosts.add(sponsor_one)

        sponsor_two = MvVolunteerFactory(is_principal=True)
        sponsor_three = MvVolunteerFactory(is_principal=True)
        accommodation_two = MvAccommodationFactory(is_principal=True)
        accommodation_two.hosts.add(sponsor_two)
        accommodation_two.hosts.add(sponsor_three)

        duplicate_group = AccommodationDuplicateGroupFactory()
        duplicate_group.accommodations.add(accommodation_one)
        duplicate_group.accommodations.add(accommodation_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        principal = duplicate_group.principal_record
        self.assertEqual(principal.hosts.count(), 3)

        duplicate_group.undo_deduplication(user=get_admin_user())

        self.assertEqual(principal.hosts.count(), 0)

    def test_undo_preserves_original_host_links_on_constituent_accommodations(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        accommodation_one = MvAccommodationFactory(is_principal=True)
        accommodation_one.hosts.add(sponsor_one)

        sponsor_two = MvVolunteerFactory(is_principal=True)
        accommodation_two = MvAccommodationFactory(is_principal=True)
        accommodation_two.hosts.add(sponsor_two)

        duplicate_group = AccommodationDuplicateGroupFactory()
        duplicate_group.accommodations.add(accommodation_one)
        duplicate_group.accommodations.add(accommodation_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        duplicate_group.undo_deduplication(user=get_admin_user())

        self.assertEqual(list(accommodation_one.hosts.all()), [sponsor_one])
        self.assertEqual(list(accommodation_two.hosts.all()), [sponsor_two])

    @freeze_time("2026-02-25 12:00:00")
    def test_should_set_principal_record_to_archived(self):
        accommodation_one = MvAccommodationFactory(is_principal=True)

        accommodation_two = MvAccommodationFactory(is_principal=True)

        duplicate_group = AccommodationDuplicateGroupFactory()
        duplicate_group.accommodations.add(accommodation_one)
        duplicate_group.accommodations.add(accommodation_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        duplicate_group.undo_deduplication(user=get_admin_user())

        duplicate_group.principal_record.refresh_from_db()
        duplicate_group.refresh_from_db()

        self.assertFalse(duplicate_group.principal_record.is_principal)
        self.assertTrue(duplicate_group.principal_record.is_archived)
        self.assertEqual(duplicate_group.principal_record.archived_at, timezone.now())
        self.assertEqual(duplicate_group.archived_at, timezone.now())
        self.assertTrue(duplicate_group.is_archived)
        self.assertIsNotNone(self.duplicate_group.principal_record)
