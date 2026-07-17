from datetime import date
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone
from freezegun import freeze_time

from deduplication.tests.factories import GuestDuplicateGroupFactory
from ontology.models import (
    CheckType,
    DevCheckV2,
    MvAccommodationRequest,
    MvInteraction,
    MvPerson,
)
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import get_admin_user


class GuestDuplicateGroupUndoDeduplicationTestCase(TestCase):
    def test_should_set_is_principal_true_to_all_undo_deduplicated_guests(self):
        self.guest_one = MvPersonFactory(is_principal=True)
        self.guest_two = MvPersonFactory(is_principal=True)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.duplicate_group.undo_deduplication(user=get_admin_user())

        self.guest_one.refresh_from_db()
        self.guest_two.refresh_from_db()

        self.assertTrue(self.guest_one.is_principal, True)
        self.assertTrue(self.guest_two.is_principal, True)

    def test_should_link_constituents_back_to_ar(self):
        guest_one = MvPersonFactory(is_principal=True, id="person-1")
        guest_two = MvPersonFactory(is_principal=True, id="person-2")

        accommodation_request = MvAccommodationRequestFactory(
            person_id=[guest_one.pk, guest_two.pk]
        )
        accommodation_request.save()
        guest_one.accommodation_request = accommodation_request
        guest_two.accommodation_request = accommodation_request
        guest_one.save()
        guest_two.save()

        duplicate_group = GuestDuplicateGroupFactory()

        duplicate_group.guests.add(guest_one)
        duplicate_group.guests.add(guest_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        duplicate_group.refresh_from_db()
        self.assertEqual(
            duplicate_group.principal_record.accommodation_request,
            accommodation_request,
        )

        accommodation_request.refresh_from_db()
        self.assertEqual(
            accommodation_request.person_id, [duplicate_group.principal_record.pk]
        )

        principal_pk = duplicate_group.principal_record.pk

        duplicate_group.undo_deduplication(user=get_admin_user())

        accommodation_request.refresh_from_db()

        self.assertNotIn(principal_pk, accommodation_request.person_id)
        self.assertIn(guest_one.pk, accommodation_request.person_id)
        self.assertIn(guest_two.pk, accommodation_request.person_id)

    def test_should_link_constituents_back_to_ars_when_original_ars_differed(self):
        guest_one = MvPersonFactory(is_principal=True, id="person-1")
        guest_two = MvPersonFactory(is_principal=True, id="person-2")

        accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[guest_one.pk]
        )
        accommodation_request_one.save()
        guest_one.accommodation_request = accommodation_request_one
        guest_one.save()

        accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[guest_two.pk]
        )
        accommodation_request_two.save()
        guest_two.accommodation_request = accommodation_request_two
        guest_two.save()

        duplicate_group = GuestDuplicateGroupFactory()

        duplicate_group.guests.add(guest_one)
        duplicate_group.guests.add(guest_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={
                "first_name": "bob",
                "accommodation_request": accommodation_request_two,
            },
            user=get_admin_user(),
        )

        duplicate_group.refresh_from_db()
        self.assertEqual(
            duplicate_group.principal_record.accommodation_request,
            accommodation_request_two,
        )

        accommodation_request_two.refresh_from_db()
        self.assertEqual(
            accommodation_request_two.person_id, [duplicate_group.principal_record.pk]
        )

        accommodation_request_one.refresh_from_db()
        self.assertEqual(accommodation_request_one.person_id, [])

        duplicate_group.undo_deduplication(user=get_admin_user())

        accommodation_request_one.refresh_from_db()
        accommodation_request_two.refresh_from_db()

        self.assertEqual(guest_one.accommodation_request, accommodation_request_one)
        self.assertEqual(accommodation_request_one.person_id, [guest_one.pk])

        self.assertEqual(guest_two.accommodation_request, accommodation_request_two)
        self.assertEqual(accommodation_request_two.person_id, [guest_two.pk])

    @freeze_time("2026-02-25 12:00:00")
    def test_should_set_principal_record_to_archived(self):
        self.guest_one = MvPersonFactory(is_principal=True)
        self.guest_two = MvPersonFactory(is_principal=True)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.principal_record = MvPerson.objects.filter(
            pk=self.duplicate_group.principal_record.id
        ).first()

        self.duplicate_group.undo_deduplication(user=get_admin_user())

        self.principal_record.refresh_from_db()
        self.duplicate_group.refresh_from_db()

        self.assertFalse(self.principal_record.is_principal)
        self.assertTrue(self.principal_record.is_archived)
        self.assertEqual(self.principal_record.archived_at, timezone.now())
        self.assertEqual(self.duplicate_group.archived_at, timezone.now())
        self.assertTrue(self.duplicate_group.is_archived)
        self.assertIsNotNone(self.duplicate_group.principal_record)

    def test_undeduplication_restores_title_and_count_on_same_ar(self):
        guest_one = MvPersonFactory(
            first_name="test",
            last_name="one",
            is_principal=True,
            date_of_birth=date(1970, 1, 1),
        )
        guest_two = MvPersonFactory(
            first_name="test",
            last_name="two",
            is_principal=True,
            date_of_birth=date(1980, 1, 1),
        )
        guest_three = MvPersonFactory(
            first_name="test",
            last_name="three",
            is_principal=True,
            date_of_birth=date(1990, 1, 1),
        )

        accommodation_request = MvAccommodationRequestFactory(
            person_id=[guest_one.pk, guest_two.pk, guest_three.pk], number_of_people=3
        )
        accommodation_request.update_primary_contact(guest_one)
        accommodation_request.save()

        for g in [guest_one, guest_two, guest_three]:
            g.accommodation_request = accommodation_request
            g.save()

        self.assertEqual(accommodation_request.title, "test one and 2 others")

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two)

        duplicate_group.deduplicate({"first_name": "bob"}, get_admin_user())

        accommodation_request.refresh_from_db()
        self.assertEqual(accommodation_request.title, "bob and 1 other")

        duplicate_group.undo_deduplication(get_admin_user())

        accommodation_request.refresh_from_db()

        self.assertEqual(accommodation_request.number_of_people, 3)
        self.assertEqual(accommodation_request.title, "test one and 2 others")
        self.assertIn(str(guest_one.pk), accommodation_request.person_id)
        self.assertIn(str(guest_two.pk), accommodation_request.person_id)

    def test_undeduplication_restores_empty_ar_to_original_state(self):
        guest_one = MvPersonFactory(
            first_name="test",
            last_name="one",
            is_principal=True,
        )
        accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[guest_one.pk], number_of_people=1
        )
        accommodation_request_one.update_primary_contact(guest_one)
        accommodation_request_one.save()
        guest_one.accommodation_request = accommodation_request_one
        guest_one.save()

        self.assertEqual(accommodation_request_one.title, "test one")

        guest_two = MvPersonFactory(
            first_name="test",
            last_name="two",
            is_principal=True,
        )
        accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[guest_two.pk], number_of_people=1
        )
        accommodation_request_two.update_primary_contact(guest_two)
        accommodation_request_two.save()
        guest_two.accommodation_request = accommodation_request_two
        guest_two.save()

        self.assertEqual(accommodation_request_two.title, "test two")

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two)

        duplicate_group.deduplicate(
            {"accommodation_request": accommodation_request_two}, get_admin_user()
        )

        accommodation_request_one.refresh_from_db()
        self.assertEqual(accommodation_request_one.title, "Empty group")

        duplicate_group.undo_deduplication(get_admin_user())

        accommodation_request_one.refresh_from_db()
        self.assertEqual(accommodation_request_one.number_of_people, 1)
        self.assertEqual(accommodation_request_one.title, "test one")
        self.assertEqual(accommodation_request_one.person_id, [guest_one.pk])

    def test_undeduplication_corrects_primary_contact_fields(self):
        guest_one = MvPersonFactory(
            first_name="Original",
            last_name="Primary",
            is_principal=True,
            date_of_birth=date(1960, 1, 1),
        )
        guest_two = MvPersonFactory(
            first_name="Other",
            last_name="Guest",
            is_principal=True,
            date_of_birth=date(1990, 1, 1),
        )

        ar = MvAccommodationRequestFactory(
            person_id=[guest_one.pk, guest_two.pk], number_of_people=2
        )
        ar.update_primary_contact(guest_one)
        ar.save()

        for g in [guest_one, guest_two]:
            g.accommodation_request = ar
            g.save()

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two)

        duplicate_group.deduplicate(
            {"first_name": "Bob", "last_name": "Deduplicated"}, get_admin_user()
        )

        ar.refresh_from_db()
        self.assertEqual(ar.primary_contact_first_name, "Bob")

        duplicate_group.undo_deduplication(get_admin_user())

        ar.refresh_from_db()
        self.assertEqual(ar.primary_contact_first_name, "Original")
        self.assertEqual(ar.primary_contact_last_name, "Primary")

    def test_all_linked_uans_carried_over_are_put_back_to_original_ar(self):
        guest_one = MvPersonFactory(
            first_name="test",
            last_name="one",
            is_principal=True,
            date_of_birth=date(1970, 1, 1),
            application_number=["123456", "000000", "111111"],
        )
        guest_two = MvPersonFactory(
            first_name="test",
            last_name="two",
            is_principal=True,
            date_of_birth=date(1990, 1, 1),
            application_number=["654321"],
        )

        accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[guest_one.pk],
            unique_application_number=["123456", "000000", "111111"],
        )
        accommodation_request_one.save()
        guest_one.accommodation_request = accommodation_request_one
        guest_one.save()

        accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[guest_two.pk],
            unique_application_number=["654321"],
        )
        accommodation_request_two.save()
        guest_two.accommodation_request = accommodation_request_two
        guest_two.save()

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two)

        duplicate_group.deduplicate(
            {"accommodation_request": accommodation_request_two},
            get_admin_user(),
        )

        accommodation_request_one.refresh_from_db()
        self.assertEqual(
            accommodation_request_one.unique_application_number,
            [],
        )

        accommodation_request_two.refresh_from_db()
        self.assertEqual(
            sorted(accommodation_request_two.unique_application_number),
            sorted(["654321", "123456", "000000", "111111"]),
        )

        duplicate_group.undo_deduplication(get_admin_user())

        accommodation_request_one.refresh_from_db()
        self.assertEqual(
            sorted(["123456", "000000", "111111"]),
            sorted(accommodation_request_one.unique_application_number),
        )

        accommodation_request_two.refresh_from_db()
        self.assertEqual(
            ["654321"],
            accommodation_request_two.unique_application_number,
        )

    def test_all_sponsors_are_put_back_to_original_ar_and_removed_from_selected(self):
        guest_one = MvPersonFactory(
            first_name="test",
            last_name="one",
            is_principal=True,
            date_of_birth=date(1970, 1, 1),
            application_number=["123456", "000000"],
        )
        guest_two = MvPersonFactory(
            first_name="test",
            last_name="two",
            is_principal=True,
            date_of_birth=date(1990, 1, 1),
            application_number=["654321"],
        )

        sponsor_one = MvVolunteerFactory(
            first_name="test",
            last_name="sponsor",
            is_principal=True,
            application_unique_application_number=["123456"],
        )
        sponsor_one.save()
        sponsor_two = MvVolunteerFactory(
            first_name="test",
            last_name="sponsor",
            is_principal=True,
            application_unique_application_number=["000000"],
        )
        sponsor_two.save()
        sponsor_three = MvVolunteerFactory(
            first_name="test",
            last_name="sponsor",
            is_principal=True,
            application_unique_application_number=["654321"],
        )
        sponsor_three.save()

        accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[guest_one.pk],
            unique_application_number=["123456", "000000"],
            sponsor_id=[sponsor_one.pk, sponsor_two.pk],
        )
        accommodation_request_one.save()
        guest_one.accommodation_request = accommodation_request_one
        guest_one.save()

        accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[guest_two.pk],
            unique_application_number=["654321"],
            sponsor_id=[sponsor_three.pk],
        )
        accommodation_request_two.save()
        guest_two.accommodation_request = accommodation_request_two
        guest_two.save()

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two)

        duplicate_group.deduplicate(
            {"accommodation_request": accommodation_request_two},
            get_admin_user(),
        )

        accommodation_request_two.refresh_from_db()
        self.assertEqual(
            sorted(accommodation_request_two.sponsor_id),
            [sponsor_one.pk, sponsor_two.pk, sponsor_three.pk],
        )

        duplicate_group.undo_deduplication(get_admin_user())

        accommodation_request_one.refresh_from_db()
        self.assertEqual(
            sorted(accommodation_request_one.sponsor_id),
            [sponsor_one.pk, sponsor_two.pk],
        )

        accommodation_request_two.refresh_from_db()
        self.assertEqual(
            accommodation_request_two.sponsor_id,
            [sponsor_three.pk],
        )

    def test_original_ar_will_have_existing_data_preserved_when_data_is_put_back(self):
        guest_one = MvPersonFactory(
            first_name="test",
            last_name="one",
            is_principal=True,
            date_of_birth=date(1970, 1, 1),
            application_number=["123456", "000000"],
        )
        guest_two = MvPersonFactory(
            first_name="test",
            last_name="two",
            is_principal=True,
            date_of_birth=date(1990, 1, 1),
            application_number=["654321"],
        )
        guest_three = MvPersonFactory(
            first_name="test",
            last_name="three",
            is_principal=True,
            date_of_birth=date(1990, 1, 1),
            application_number=["444444"],
        )

        sponsor_one = MvVolunteerFactory(
            first_name="test",
            last_name="sponsor",
            is_principal=True,
            application_unique_application_number=["123456"],
        )
        sponsor_one.save()
        sponsor_two = MvVolunteerFactory(
            first_name="test",
            last_name="sponsor",
            is_principal=True,
            application_unique_application_number=["000000"],
        )
        sponsor_two.save()
        sponsor_three = MvVolunteerFactory(
            first_name="test",
            last_name="sponsor",
            is_principal=True,
            application_unique_application_number=["654321"],
        )
        sponsor_three.save()
        sponsor_four = MvVolunteerFactory(
            first_name="test",
            last_name="sponsor",
            is_principal=True,
            application_unique_application_number=["444444"],
        )
        sponsor_four.save()

        accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[guest_one.pk, guest_three.pk],
            unique_application_number=["123456", "000000", "444444"],
            sponsor_id=[sponsor_one.pk, sponsor_two.pk, "4", "6"],
        )
        accommodation_request_one.save()
        guest_one.accommodation_request = accommodation_request_one
        guest_one.save()
        guest_three.accommodation_request = accommodation_request_one
        guest_three.save()

        accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[guest_two.pk],
            unique_application_number=["654321"],
            sponsor_id=[sponsor_three.pk],
        )
        accommodation_request_two.save()
        guest_two.accommodation_request = accommodation_request_two
        guest_two.save()

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two)

        duplicate_group.deduplicate(
            {"accommodation_request": accommodation_request_two},
            get_admin_user(),
        )

        duplicate_group.undo_deduplication(get_admin_user())

        accommodation_request_one.refresh_from_db()
        self.assertEqual(
            sorted(accommodation_request_one.unique_application_number),
            ["000000", "123456", "444444"],
        )
        self.assertEqual(
            sorted(accommodation_request_one.sponsor_id),
            sorted([sponsor_one.pk, sponsor_two.pk, "4", "6"]),
        )

    def test_interaction_created_on_unselected_ar_after_undo_dedupe(self):
        user = get_admin_user()
        guest_one = MvPersonFactory(
            is_principal=True, id="person-1", first_name="Alice", last_name="Smith"
        )
        guest_two = MvPersonFactory(
            is_principal=True, id="person-2", first_name="Trevor", last_name="Williams"
        )

        accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[guest_one.pk]
        )
        accommodation_request_one.save()
        guest_one.accommodation_request = accommodation_request_one
        guest_one.save()

        accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[guest_two.pk]
        )
        accommodation_request_two.save()
        guest_two.accommodation_request = accommodation_request_two
        guest_two.save()

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one)
        duplicate_group.guests.add(guest_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={
                "first_name": "Alice",
                "last_name": "Williams",
                "accommodation_request": accommodation_request_two,
            },
            user=user,
        )

        duplicate_group.undo_deduplication(user=user)

        ar1_interactions = MvInteraction.objects.filter(
            linked_accommodation_request=accommodation_request_one,
            interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATION_UNDONE,
        )
        self.assertEqual(ar1_interactions.count(), 1)

        interaction = ar1_interactions.first()
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.RECORD_DEDUPLICATION_UNDONE,
        )
        self.assertEqual(interaction.title, "Guest restored")
        self.assertEqual(interaction.created_by, user)

        self.assertEqual(
            interaction.interaction_notes,
            "Alice Smith was restored to this accommodation request by undoing "
            "a deduplication.",
        )

        ar2_interactions = MvInteraction.objects.filter(
            linked_accommodation_request=accommodation_request_two,
            interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATION_UNDONE,
        )
        self.assertEqual(ar2_interactions.count(), 1)

        interaction = ar2_interactions.first()
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.RECORD_DEDUPLICATION_UNDONE,
        )
        self.assertEqual(interaction.title, "Guest restored")
        self.assertEqual(interaction.created_by, user)

        self.assertEqual(
            interaction.interaction_notes,
            "Trevor Williams was restored to this accommodation request by undoing "
            "a deduplication.",
        )

    @override_settings(ENHANCED_DEDUPLICATION_LOGGING=True)
    def test_undo_emits_started_and_finished_sentry_logs(self):
        guest_one = MvPersonFactory(is_principal=True)
        guest_two = MvPersonFactory(is_principal=True)
        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one)
        duplicate_group.guests.add(guest_two)
        duplicate_group.save()
        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"},
            user=get_admin_user(),
        )

        with patch("sentry_sdk.logger.info") as info:
            duplicate_group.undo_deduplication(user=get_admin_user())

        messages = [call.args[0] for call in info.call_args_list]
        self.assertIn("GuestDuplicateGroup.undo_deduplication: started", messages)
        self.assertIn("GuestDuplicateGroup.undo_deduplication: finished", messages)

    def test_undo_emits_completed_sentry_metric(self):
        guest_one = MvPersonFactory(is_principal=True)
        guest_two = MvPersonFactory(is_principal=True)
        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one)
        duplicate_group.guests.add(guest_two)
        duplicate_group.save()
        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"},
            user=get_admin_user(),
        )

        with patch("sentry_sdk.metrics.count") as count:
            duplicate_group.undo_deduplication(user=get_admin_user())

        count.assert_called_once_with(
            "undo_deduplication.completed",
            1,
            attributes={"record_type": "guest"},
        )

    def test_undedupe_recalculates_checks_on_linked_ars_no_existing_checks(self):
        guest_one = MvPersonFactory(
            first_name="test",
            last_name="one",
            is_principal=True,
            date_of_birth=date(1960, 1, 1),
        )
        guest_two = MvPersonFactory(
            first_name="test",
            last_name="two",
            is_principal=True,
            date_of_birth=date(1980, 1, 1),
        )

        accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[guest_one.pk],
            number_of_people=1,
        )
        accommodation_request_one.update_primary_contact(guest_one)
        accommodation_request_one.save()
        guest_one.accommodation_request = accommodation_request_one
        guest_one.save()

        accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[guest_two.pk],
            number_of_people=1,
        )
        accommodation_request_two.update_primary_contact(guest_two)
        accommodation_request_two.save()
        guest_two.accommodation_request = accommodation_request_two
        guest_two.save()

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two)
        accommodation_request_one.checks_status = (
            accommodation_request_one.determine_checks_status_from_linked_objects()
        )

        duplicate_group.deduplicate(
            {"accommodation_request": accommodation_request_two},
            get_admin_user(),
        )

        accommodation_request_one.refresh_from_db()

        self.assertEqual(
            accommodation_request_one.checks_status,
            MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY,
        )

        duplicate_group.undo_deduplication(user=get_admin_user())
        accommodation_request_one.refresh_from_db()

        self.assertEqual(
            accommodation_request_one.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

    def test_undedupe_recalculates_checks_on_linked_ars_failed_checks(self):
        guest_one = MvPersonFactory(
            first_name="test",
            last_name="one",
            is_principal=True,
            date_of_birth=date(1970, 1, 1),
            application_number=["123456", "000000"],
        )
        guest_two = MvPersonFactory(
            first_name="test",
            last_name="two",
            is_principal=True,
            date_of_birth=date(1990, 1, 1),
            application_number=["654321"],
        )

        sponsor_one = MvVolunteerFactory(
            first_name="test",
            last_name="sponsor",
            is_principal=True,
            application_unique_application_number=["123456"],
        )
        sponsor_one.save()
        sponsor_two = MvVolunteerFactory(
            first_name="test",
            last_name="sponsor",
            is_principal=True,
            application_unique_application_number=["654321"],
        )
        sponsor_two.save()

        accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[guest_one.pk],
            unique_application_number=["123456", "000000"],
            sponsor_id=[sponsor_one.pk],
        )
        accommodation_request_one.save()
        guest_one.accommodation_request = accommodation_request_one
        guest_one.save()

        accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[guest_two.pk],
            unique_application_number=["654321"],
            sponsor_id=[sponsor_two.pk],
        )
        accommodation_request_two.save()
        guest_two.accommodation_request = accommodation_request_two
        guest_two.save()

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two)

        sponsor_dbs_check_1 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
        )
        sponsor_dbs_check_1.sponsor.set([sponsor_one])

        sponsor_dbs_check_1.check_status = DevCheckV2.CheckStatus.FAILED

        sponsor_dbs_check_1.save()

        sponsor_dbs_check_2 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
        )
        sponsor_dbs_check_2.sponsor.set([sponsor_two])

        sponsor_dbs_check_2.check_status = DevCheckV2.CheckStatus.PASSED

        sponsor_dbs_check_2.save()

        accommodation_request_one.checks_status = (
            accommodation_request_one.determine_checks_status_from_linked_objects()
        )

        self.assertEqual(
            accommodation_request_one.checks_status,
            MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED,
        )

        accommodation_request_two.checks_status = (
            accommodation_request_two.determine_checks_status_from_linked_objects()
        )

        self.assertEqual(
            accommodation_request_two.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED,
        )

        duplicate_group.deduplicate(
            {"accommodation_request": accommodation_request_two},
            get_admin_user(),
        )
        accommodation_request_one.refresh_from_db()
        accommodation_request_two.refresh_from_db()

        self.assertEqual(
            accommodation_request_one.checks_status,
            MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY,
        )

        duplicate_group.undo_deduplication(user=get_admin_user())
        accommodation_request_one.refresh_from_db()

        self.assertEqual(
            accommodation_request_one.checks_status,
            MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED,
        )

        self.assertEqual(
            accommodation_request_two.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED,
        )

    def test_undo_deduplication_reopens_ar_that_was_closed_empty_after_guest_removed(
        self,
    ):
        guest_one = MvPersonFactory(
            first_name="test",
            last_name="one",
            is_principal=True,
            date_of_birth=date(1960, 1, 1),
        )
        guest_two = MvPersonFactory(
            first_name="test",
            last_name="two",
            is_principal=True,
            date_of_birth=date(1980, 1, 1),
        )

        accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[guest_one.pk],
            number_of_people=1,
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED,
        )
        accommodation_request_one.update_primary_contact(guest_one)
        accommodation_request_one.save()
        guest_one.accommodation_request = accommodation_request_one
        guest_one.save()

        accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[guest_two.pk],
            number_of_people=1,
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED,
        )
        accommodation_request_two.update_primary_contact(guest_two)
        accommodation_request_two.save()
        guest_two.accommodation_request = accommodation_request_two
        guest_two.save()

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two)

        duplicate_group.deduplicate(
            {"accommodation_request": accommodation_request_two},
            get_admin_user(),
        )

        accommodation_request_one.refresh_from_db()
        self.assertEqual(
            accommodation_request_one.checks_status,
            MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY,
        )

        duplicate_group.undo_deduplication(user=get_admin_user())

        accommodation_request_one.refresh_from_db()
        self.assertNotEqual(
            accommodation_request_one.checks_status,
            MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY,
        )
