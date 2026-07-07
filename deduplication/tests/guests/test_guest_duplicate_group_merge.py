from datetime import date, datetime, timezone
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils.formats import date_format

from deduplication.exceptions import DeduplicationException
from deduplication.tests.factories import GuestDuplicateGroupFactory
from ontology.models import MvAccommodationRequest, MvInteraction
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import get_admin_user


class GuestDuplicateGroupDeduplicationTestCase(TestCase):
    def test_should_create_new_principal_record_from_values_when_merging(self):
        self.guest_one = MvPersonFactory(is_principal=True)
        self.guest_two = MvPersonFactory(is_principal=True)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        principal_record_values = {
            "first_name": "bob",
            "last_name": "test",
            "gender": "male",
            "date_of_birth": datetime(2020, 1, 1),
            "email": ["email1", "email2"],
            "phone": ["phone1", "phone2"],
            "passport_id": ["id1", "id2"],
            "application_number": ["123", "456"],
        }

        self.duplicate_group.deduplicate(
            principal_record_values=principal_record_values, user=get_admin_user()
        )

        self.guest_one.refresh_from_db()
        self.guest_two.refresh_from_db()

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.is_principal)
        self.assertEqual(
            self.duplicate_group.principal_record.first_name,
            principal_record_values["first_name"],
        )
        self.assertEqual(
            self.duplicate_group.principal_record.last_name,
            principal_record_values["last_name"],
        )
        self.assertEqual(
            self.duplicate_group.principal_record.gender,
            principal_record_values["gender"],
        )
        self.assertEqual(
            self.duplicate_group.principal_record.date_of_birth,
            principal_record_values["date_of_birth"],
        )
        self.assertEqual(
            self.duplicate_group.principal_record.email,
            principal_record_values["email"],
        )
        self.assertEqual(
            self.duplicate_group.principal_record.phone,
            principal_record_values["phone"],
        )
        self.assertEqual(
            self.duplicate_group.principal_record.passport_id,
            principal_record_values["passport_id"],
        )
        self.assertEqual(
            self.duplicate_group.principal_record.application_number,
            principal_record_values["application_number"],
        )

        self.assertFalse(self.guest_one.is_principal)
        self.assertFalse(self.guest_two.is_principal)

    def test_should_disallow_merging_non_principal_records(self):
        self.guest_one = MvPersonFactory(is_principal=True)
        self.guest_two = MvPersonFactory(is_principal=False)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        with self.assertRaises(DeduplicationException) as ctx:
            self.duplicate_group.deduplicate(
                principal_record_values={"first_name": "bob"}, user=get_admin_user()
            )

        self.assertEqual(
            str(ctx.exception), "Cannot deduplicate using non principal records"
        )

    def test_should_disallow_merging_fewer_than_two_records(self):
        self.guest_one = MvPersonFactory(is_principal=True)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.save()

        with self.assertRaises(DeduplicationException) as ctx:
            self.duplicate_group.deduplicate(
                principal_record_values={"first_name": "bob"}, user=get_admin_user()
            )

        self.assertEqual(
            str(ctx.exception),
            "Require at least two constituents to perform deduplication",
        )

    def test_should_disallow_merging_already_deduplicated_duplication_groups(self):
        self.guest_one = MvPersonFactory(is_principal=True)
        self.guest_two = MvPersonFactory(is_principal=True)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        with self.assertRaises(DeduplicationException) as ctx:
            self.duplicate_group.deduplicate(
                principal_record_values={"first_name": "bob"}, user=get_admin_user()
            )

        self.assertEqual(
            str(ctx.exception),
            "Cannot perform deduplication on an already deduplicated group",
        )

    def test_result_is_linked_to_ar_of_the_constituents_when_ars_are_the_same(
        self,
    ):
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

    def test_deduplication_result_is_linked_to_chosen_ar_when_ars_are_different(self):
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

    def test_constituents_is_unlinked_from_ars_person_id(self):
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

        accommodation_request_one.refresh_from_db()
        accommodation_request_two.refresh_from_db()

        self.assertNotIn(guest_one.pk, accommodation_request_one.person_id)
        self.assertNotIn(guest_two.pk, accommodation_request_two.person_id)

    def test_result_should_have_notional_data_true_if_any_of_constituents_do(
        self,
    ):
        self.guest_one = MvPersonFactory(is_principal=True, notional_data=True)
        self.guest_two = MvPersonFactory(is_principal=True, notional_data=False)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.notional_data)

    def test_result_should_have_notional_data_false_if_all_constituents_do(
        self,
    ):
        self.guest_one = MvPersonFactory(is_principal=True, notional_data=False)
        self.guest_two = MvPersonFactory(is_principal=True, notional_data=False)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertFalse(self.duplicate_group.principal_record.notional_data)

    def test_deduplication_result_should_aggregate_application_numbers_of_constituents(
        self,
    ):
        self.guest_one = MvPersonFactory(is_principal=True, application_number=["1a"])
        self.guest_two = MvPersonFactory(is_principal=True, application_number=["2b"])

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(self.duplicate_group.principal_record.application_number),
            sorted(["1a", "2b"]),
        )

    def test_result_should_have_adverse_rematch_true_if_any_of_constituents_do(
        self,
    ):
        self.guest_one = MvPersonFactory(is_principal=True, adverse_rematch=True)
        self.guest_two = MvPersonFactory(is_principal=True, adverse_rematch=False)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.adverse_rematch)

    def test_result_should_have_adverse_rematch_false_if_all_constituents_do(
        self,
    ):
        self.guest_one = MvPersonFactory(is_principal=True, adverse_rematch=False)
        self.guest_two = MvPersonFactory(is_principal=True, adverse_rematch=False)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertFalse(self.duplicate_group.principal_record.adverse_rematch)

    def test_result_aggregates_sponsorship_certification_numbers_of_constituents(
        self,
    ):
        self.guest_one = MvPersonFactory(
            is_principal=True, sponsorship_certification_number_id=["1a"]
        )
        self.guest_two = MvPersonFactory(
            is_principal=True, sponsorship_certification_number_id=["2b"]
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(
                self.duplicate_group.principal_record.sponsorship_certification_number_id
            ),
            sorted(["1a", "2b"]),
        )

    def test_deduplication_result_aggregates_source_of_constituents(
        self,
    ):
        self.guest_one = MvPersonFactory(is_principal=True, source=["a"])
        self.guest_two = MvPersonFactory(is_principal=True, source=["b"])

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(self.duplicate_group.principal_record.source),
            sorted(["a", "b"]),
        )

    def test_deduplication_result_aggregates_viewer_group_names_of_constituents(
        self,
    ):
        self.guest_one = MvPersonFactory(
            is_principal=True, viewer_group_names=["group_a"]
        )
        self.guest_two = MvPersonFactory(
            is_principal=True, viewer_group_names=["group_b"]
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(self.duplicate_group.principal_record.viewer_group_names),
            sorted(["group_a", "group_b"]),
        )

    def test_deduplication_result_aggregates_gwf_of_constituents(
        self,
    ):
        self.guest_one = MvPersonFactory(is_principal=True, gwf=["gwf-1"])
        self.guest_two = MvPersonFactory(is_principal=True, gwf=["gwf-2"])

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(self.duplicate_group.principal_record.gwf),
            sorted(["gwf-1", "gwf-2"]),
        )

    def test_should_calculate_age_for_principal_from_passed_dob(self):
        self.guest_one = MvPersonFactory(is_principal=True)
        self.guest_two = MvPersonFactory(is_principal=True)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        date_of_birth = datetime.strptime("1990-06-15", "%Y-%m-%d").date()

        self.duplicate_group.deduplicate(
            principal_record_values={"date_of_birth": date_of_birth},
            user=get_admin_user(),
        )

        def calculate_age(dob: date) -> int:
            today = date.today()
            return (
                today.year
                - dob.year
                - ((today.month, today.day) < (dob.month, dob.day))
            )

        self.guest_one.refresh_from_db()
        self.guest_two.refresh_from_db()

        self.assertEqual(
            self.duplicate_group.principal_record.age,
            calculate_age(date_of_birth),
        )

    def test_should_have_can_be_contacted_by_phone_yes_if_any_of_constituents_do(
        self,
    ):
        self.guest_one = MvPersonFactory(
            is_principal=True, can_be_contacted_by_phone="Yes"
        )
        self.guest_two = MvPersonFactory(
            is_principal=True, can_be_contacted_by_phone="No"
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertEqual(
            self.duplicate_group.principal_record.can_be_contacted_by_phone, "Yes"
        )

    def test_should_have_can_be_contacted_by_phone_no_if_all_constituents_do(
        self,
    ):
        self.guest_one = MvPersonFactory(
            is_principal=True, can_be_contacted_by_phone="No"
        )
        self.guest_two = MvPersonFactory(
            is_principal=True, can_be_contacted_by_phone="No"
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )
        self.assertEqual(
            self.duplicate_group.principal_record.can_be_contacted_by_phone, "No"
        )

    def test_should_set_created_at_set_to_earliest_created_at_of_guests(
        self,
    ):
        user = get_admin_user()

        self.guest_one = MvPersonFactory(
            is_principal=True,
            created_at=(datetime(1990, 6, 14, 23, 0, tzinfo=timezone.utc)),
        )
        self.guest_two = MvPersonFactory(
            is_principal=True,
            created_at=datetime(2000, 6, 14, 23, 0, tzinfo=timezone.utc),
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=user
        )
        self.assertEqual(
            self.duplicate_group.principal_record.created_at,
            self.guest_one.created_at,
        )

    def test_should_set_created_by_to_email_of_user(
        self,
    ):
        user = get_admin_user()

        self.guest_one = MvPersonFactory(
            is_principal=True,
        )
        self.guest_two = MvPersonFactory(
            is_principal=True,
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=user
        )
        self.assertEqual(self.duplicate_group.principal_record.created_by, user.email)

    def test_result_should_have_disability_flag_true_if_any_of_constituents_do(
        self,
    ):
        self.guest_one = MvPersonFactory(is_principal=True, disability_flag=True)
        self.guest_two = MvPersonFactory(is_principal=True, disability_flag=False)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.disability_flag)

    def test_result_should_have_disability_flag_false_if_all_constituents_do(
        self,
    ):
        self.guest_one = MvPersonFactory(is_principal=True, disability_flag=False)
        self.guest_two = MvPersonFactory(is_principal=True, disability_flag=False)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertFalse(self.duplicate_group.principal_record.disability_flag)

    def test_deduplication_result_should_have_is_uam_true_if_any_of_constituents_do(
        self,
    ):
        self.guest_one = MvPersonFactory(is_principal=True, is_uam=True)
        self.guest_two = MvPersonFactory(is_principal=True, is_uam=False)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.is_uam)
        self.assertIsNone(self.duplicate_group.principal_record.is_uam_edited_time)

    def test_deduplication_result_should_have_is_uam_false_if_all_constituents_do(
        self,
    ):
        self.guest_one = MvPersonFactory(is_principal=True, is_uam=False)
        self.guest_two = MvPersonFactory(is_principal=True, is_uam=False)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertFalse(self.duplicate_group.principal_record.is_uam)
        self.assertIsNone(self.duplicate_group.principal_record.is_uam_edited_time)

    def test_deduplication_result_aggregates_nationality_of_constituents(
        self,
    ):
        self.guest_one = MvPersonFactory(is_principal=True, nationality=["a"])
        self.guest_two = MvPersonFactory(is_principal=True, nationality=["b", "c"])

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(self.duplicate_group.principal_record.nationality),
            sorted(["a", "b", "c"]),
        )

    def test_result_aggregates_primary_application_numbers_of_constituents(
        self,
    ):
        self.guest_one = MvPersonFactory(
            is_principal=True, primary_application_numbers=["a"]
        )
        self.guest_two = MvPersonFactory(
            is_principal=True, primary_application_numbers=["b", "c"]
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(self.duplicate_group.principal_record.primary_application_numbers),
            sorted(["a", "b", "c"]),
        )

    def test_result_should_have_wheelchair_required_true_if_any_of_constituents_do(
        self,
    ):
        self.guest_one = MvPersonFactory(is_principal=True, wheelchair_required=True)
        self.guest_two = MvPersonFactory(is_principal=True, wheelchair_required=False)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.wheelchair_required)

    def test_result_should_have_wheelchair_required_false_if_all_constituents_do(
        self,
    ):
        self.guest_one = MvPersonFactory(is_principal=True, wheelchair_required=False)
        self.guest_two = MvPersonFactory(is_principal=True, wheelchair_required=False)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertFalse(self.duplicate_group.principal_record.wheelchair_required)

    def test_deduplication_result_should_have_edited_in_app_true(
        self,
    ):
        self.guest_one = MvPersonFactory(is_principal=True)
        self.guest_two = MvPersonFactory(is_principal=True)

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.edited_in_app)

    def test_should_not_set_date_of_first_visa_decision(
        self,
    ):
        user = get_admin_user()

        self.guest_one = MvPersonFactory(
            is_principal=True,
        )
        self.guest_two = MvPersonFactory(
            is_principal=True,
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=user
        )
        self.assertIsNone(
            self.duplicate_group.principal_record.date_of_first_issue_visa_decision
        )

    def test_should_not_set_alternate_email_fields(
        self,
    ):
        user = get_admin_user()

        self.guest_one = MvPersonFactory(
            is_principal=True,
        )
        self.guest_two = MvPersonFactory(
            is_principal=True,
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=user
        )
        self.assertIsNone(self.duplicate_group.principal_record.email_after_decision)
        self.assertIsNone(self.duplicate_group.principal_record.email_for_decision)
        self.assertIsNone(self.duplicate_group.principal_record.email_for_questions)

    def test_should_not_set_arrival_info(
        self,
    ):
        user = get_admin_user()

        self.guest_one = MvPersonFactory(
            is_principal=True,
        )
        self.guest_two = MvPersonFactory(
            is_principal=True,
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=user
        )
        self.assertIsNone(self.duplicate_group.principal_record.arrival_date)
        self.assertIsNone(self.duplicate_group.principal_record.arrival_port_code)
        self.assertIsNone(self.duplicate_group.principal_record.arrival_port_name)

    def test_should_not_set_group(
        self,
    ):
        user = get_admin_user()

        self.guest_one = MvPersonFactory(
            is_principal=True,
        )
        self.guest_two = MvPersonFactory(
            is_principal=True,
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=user
        )
        self.assertIsNone(self.duplicate_group.principal_record.group)

    def test_should_not_set_edited_info(
        self,
    ):
        user = get_admin_user()

        self.guest_one = MvPersonFactory(
            is_principal=True,
        )
        self.guest_two = MvPersonFactory(
            is_principal=True,
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=user
        )
        self.assertIsNone(self.duplicate_group.principal_record.last_edited_at)
        self.assertIsNone(self.duplicate_group.principal_record.last_edited_by)

    def test_should_not_set_visa_application_date_maximum(
        self,
    ):
        user = get_admin_user()

        self.guest_one = MvPersonFactory(
            is_principal=True,
        )
        self.guest_two = MvPersonFactory(
            is_principal=True,
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=user
        )
        self.assertIsNone(
            self.duplicate_group.principal_record.visa_application_date_maximum
        )

    def test_should_not_set_latest_arrival_date(
        self,
    ):
        user = get_admin_user()

        self.guest_one = MvPersonFactory(
            is_principal=True,
        )
        self.guest_two = MvPersonFactory(
            is_principal=True,
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=user
        )
        self.assertIsNone(self.duplicate_group.principal_record.latest_arrival_date)

    def test_should_not_set_old_group_info(
        self,
    ):
        user = get_admin_user()

        self.guest_one = MvPersonFactory(
            is_principal=True,
        )
        self.guest_two = MvPersonFactory(
            is_principal=True,
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=user
        )
        self.assertIsNone(self.duplicate_group.principal_record.old_group)
        self.assertIsNone(self.duplicate_group.principal_record.previous_group_id)
        self.assertIsNone(
            self.duplicate_group.principal_record.previous_group_leaving_times
        )

    def test_should_not_set_title(
        self,
    ):
        user = get_admin_user()

        self.guest_one = MvPersonFactory(
            is_principal=True,
        )
        self.guest_two = MvPersonFactory(
            is_principal=True,
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=user
        )
        self.assertIsNone(self.duplicate_group.principal_record.title)

    def test_should_not_set_travelling_to_uk(
        self,
    ):
        user = get_admin_user()

        self.guest_one = MvPersonFactory(
            is_principal=True,
        )
        self.guest_two = MvPersonFactory(
            is_principal=True,
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=user
        )
        self.assertIsNone(self.duplicate_group.principal_record.travelling_to_uk)

    def test_should_not_set_upe_visa_status(
        self,
    ):
        user = get_admin_user()

        self.guest_one = MvPersonFactory(
            is_principal=True,
        )
        self.guest_two = MvPersonFactory(
            is_principal=True,
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=user
        )
        self.assertIsNone(self.duplicate_group.principal_record.upe_visa_status)

    def test_should_not_set_alternate_visa_application_fields(
        self,
    ):
        user = get_admin_user()

        self.guest_one = MvPersonFactory(
            is_principal=True,
        )
        self.guest_two = MvPersonFactory(
            is_principal=True,
        )

        self.duplicate_group = GuestDuplicateGroupFactory()

        self.duplicate_group.guests.add(self.guest_one)
        self.duplicate_group.guests.add(self.guest_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=user
        )
        self.assertIsNone(self.duplicate_group.principal_record.visa_application_date)
        self.assertIsNone(self.duplicate_group.principal_record.visa_application_dates)
        self.assertIsNone(self.duplicate_group.principal_record.visa_decision_date)

    def test_same_ar_neither_is_primary_no_change_to_ar_primary(self):
        guest_one = MvPersonFactory(
            first_name="test",
            last_name="one",
            is_principal=True,
            date_of_birth=date(1990, 1, 1),
        )
        guest_two = MvPersonFactory(
            first_name="test",
            last_name="two",
            is_principal=True,
            date_of_birth=date(1990, 1, 1),
        )
        guest_three = MvPersonFactory(
            first_name="test",
            last_name="three",
            is_principal=True,
            date_of_birth=date(1970, 1, 1),
        )

        accommodation_request = MvAccommodationRequestFactory(
            person_id=[guest_one.pk, guest_two.pk, guest_three.pk],
            number_of_people=3,
        )
        accommodation_request.update_primary_contact(guest_three)
        accommodation_request.save()

        for g in [guest_one, guest_two, guest_three]:
            g.accommodation_request = accommodation_request
            g.save()

        self.assertEqual("test three and 2 others", accommodation_request.title)

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two)
        duplicate_group.deduplicate({"first_name": "bob"}, get_admin_user())

        accommodation_request.refresh_from_db()
        self.assertEqual("test three and 1 other", accommodation_request.title)

    def test_same_ar_one_is_primary_updates_to_new_principal(self):
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
            date_of_birth=date(1990, 1, 1),
        )

        accommodation_request = MvAccommodationRequestFactory(
            person_id=[guest_one.pk, guest_two.pk],
            number_of_people=2,
        )
        accommodation_request.update_primary_contact(guest_one)
        accommodation_request.save()

        for g in [guest_one, guest_two]:
            g.accommodation_request = accommodation_request
            g.save()

        self.assertEqual("test one and 1 other", accommodation_request.title)

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two)
        duplicate_group.deduplicate({"first_name": "bob"}, get_admin_user())

        accommodation_request.refresh_from_db()
        self.assertEqual("bob", accommodation_request.title)

    def test_diff_ar_neither_is_primary_no_change_to_selected_ar_primary(self):
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
            date_of_birth=date(1990, 1, 1),
        )
        guest_three = MvPersonFactory(
            first_name="test",
            last_name="three",
            is_principal=True,
            date_of_birth=date(1960, 1, 1),
        )

        accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[guest_one.pk],
            number_of_people=1,
        )
        accommodation_request_one.save()
        guest_one.accommodation_request = accommodation_request_one
        guest_one.save()

        accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[guest_two.pk, guest_three.pk],
            number_of_people=2,
        )
        accommodation_request_two.update_primary_contact(guest_three)
        accommodation_request_two.save()
        guest_two.accommodation_request = accommodation_request_two
        guest_three.accommodation_request = accommodation_request_two
        guest_two.save()
        guest_three.save()

        self.assertEqual("test three and 1 other", accommodation_request_two.title)

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two)

        duplicate_group.deduplicate(
            {"first_name": "bob", "accommodation_request": accommodation_request_two},
            get_admin_user(),
        )

        accommodation_request_two.refresh_from_db()
        self.assertEqual("test three and 1 other", accommodation_request_two.title)

    def test_diff_ar_selected_primary_deduped_unselected_not_deduped(self):
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

        accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[guest_one.pk, guest_three.pk],
            number_of_people=2,
        )
        accommodation_request_one.save()
        guest_one.accommodation_request = accommodation_request_one
        guest_one.save()

        accommodation_request_one.refresh_from_db()
        self.assertEqual("test one and 1 other", accommodation_request_one.title)

        accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[guest_two.pk],
            number_of_people=1,
        )
        accommodation_request_two.update_primary_contact(guest_two)
        accommodation_request_two.save()
        guest_two.accommodation_request = accommodation_request_two
        guest_two.save()

        self.assertEqual("test two", accommodation_request_two.title)

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two)

        duplicate_group.deduplicate(
            {"first_name": "bob", "accommodation_request": accommodation_request_two},
            get_admin_user(),
        )

        accommodation_request_one.refresh_from_db()
        self.assertEqual("test three", accommodation_request_one.title)

        accommodation_request_two.refresh_from_db()
        self.assertEqual("bob", accommodation_request_two.title)

    def test_diff_ar_unselected_is_now_empty(self):
        guest_one = MvPersonFactory(
            first_name="test", last_name="one", is_principal=True
        )
        guest_two = MvPersonFactory(
            first_name="test", last_name="two", is_principal=True
        )

        accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[guest_one.pk],
            number_of_people=1,
        )
        accommodation_request_one.update_primary_contact(guest_one)
        accommodation_request_one.save()
        guest_one.accommodation_request = accommodation_request_one
        guest_one.save()

        self.assertEqual("test one", accommodation_request_one.title)

        accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[guest_two.pk],
            number_of_people=1,
        )
        accommodation_request_two.update_primary_contact(guest_two)
        accommodation_request_two.save()
        guest_two.accommodation_request = accommodation_request_two
        guest_two.save()

        self.assertEqual("test two", accommodation_request_two.title)

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two)
        duplicate_group.deduplicate(
            {"accommodation_request": accommodation_request_two}, get_admin_user()
        )

        accommodation_request_one.refresh_from_db()
        self.assertEqual("Empty group", accommodation_request_one.title)
        self.assertTrue(accommodation_request_one.is_empty_group)
        self.assertEqual(0, accommodation_request_one.number_of_people)

    def test_diff_ar_unselected_primary_is_deduped_picks_next_oldest(self):
        guest_one = MvPersonFactory(
            first_name="test",
            last_name="one",
            is_principal=True,
            date_of_birth=date(1960, 1, 1),
        )
        guest_three = MvPersonFactory(
            first_name="test",
            last_name="three",
            is_principal=True,
            date_of_birth=date(1970, 1, 1),
        )
        guest_four = MvPersonFactory(
            first_name="test",
            last_name="four",
            is_principal=True,
            date_of_birth=date(1980, 1, 1),
        )

        accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[guest_one.pk, guest_three.pk, guest_four.pk],
            number_of_people=3,
        )
        accommodation_request_one.update_primary_contact(guest_one)
        accommodation_request_one.save()

        for g in [guest_one, guest_three, guest_four]:
            g.accommodation_request = accommodation_request_one
            g.save()

        self.assertEqual("test one and 2 others", accommodation_request_one.title)

        guest_two = MvPersonFactory(
            first_name="test", last_name="two", is_principal=True
        )
        accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[guest_two.pk],
            number_of_people=1,
        )
        accommodation_request_two.update_primary_contact(guest_two)
        accommodation_request_two.save()

        guest_two.accommodation_request = accommodation_request_two
        guest_two.save()

        self.assertEqual("test two", accommodation_request_two.title)

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two)

        duplicate_group.deduplicate(
            {"accommodation_request": accommodation_request_two}, get_admin_user()
        )

        accommodation_request_one.refresh_from_db()

        self.assertEqual("test three and 1 other", accommodation_request_one.title)

    def test_linked_uan_is_removed_from_unselected_ar_and_added_to_selected_ar(self):
        guest_one = MvPersonFactory(
            first_name="test",
            last_name="one",
            is_principal=True,
            date_of_birth=date(1970, 1, 1),
            application_number=["123456"],
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
            unique_application_number=["123456"],
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
            accommodation_request_two.unique_application_number,
            ["654321", "123456"],
        )

    def test_only_correct_linked_uan_is_removed_from_unselected_ar(self):
        guest_one = MvPersonFactory(
            first_name="test",
            last_name="one",
            is_principal=True,
            date_of_birth=date(1970, 1, 1),
            application_number=["123456"],
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
            unique_application_number=["123456", "000000"],
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
            ["000000"],
        )

    def test_all_linked_uans_are_carried_over_to_selected_ar(self):
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
            accommodation_request_two.unique_application_number,
            ["654321", "123456", "000000", "111111"],
        )

    def test_sponsors_linked_to_uan_move_to_selected_ar(self):
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
            sponsor_id=["01010101"],
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
            accommodation_request_two.sponsor_id,
            ["01010101", sponsor_one.pk, sponsor_two.pk],
        )

    def test_dedup_interaction_created_on_unselected_ar_when_ars_are_different(self):
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

        ar1_interactions = MvInteraction.objects.filter(
            linked_accommodation_request=accommodation_request_one,
            interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
        )
        self.assertEqual(ar1_interactions.count(), 1)
        interaction = ar1_interactions.first()
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
        )
        self.assertEqual(interaction.title, "Record deduplicated")
        self.assertEqual(interaction.created_by, user)

        formatted_date = date_format(duplicate_group.created_at, "j F Y")
        self.assertEqual(
            interaction.interaction_notes,
            f"Alice Smith was moved to another accommodation request as part of a"
            f" deduplication on {formatted_date}.\n\n"
            f"The guest was marked as a duplicate and a new principal guest record"
            f" created for Alice Williams.",
        )

    def test_dedup_interaction_created_on_selected_ar_when_ars_are_different(self):
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

        ar2_interactions = MvInteraction.objects.filter(
            linked_accommodation_request=accommodation_request_two,
            interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
        )
        self.assertEqual(ar2_interactions.count(), 1)
        interaction = ar2_interactions.first()
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
        )
        self.assertEqual(interaction.title, "Record deduplicated")
        self.assertEqual(interaction.created_by, user)

        formatted_date = date_format(duplicate_group.created_at, "j F Y")
        self.assertEqual(
            interaction.interaction_notes,
            f"Trevor Williams was marked as a duplicate on {formatted_date} and"
            f" replaced by a new principal record, Alice Williams.\n\n"
            f"This principal record was created after guest records"
            f" Alice Smith and Trevor Williams were marked as duplicates.",
        )

    def test_dedup_interaction_on_ar_when_both_guests_are_on_same_ar(self):
        user = get_admin_user()
        guest_one = MvPersonFactory(
            is_principal=True,
            id="person-1",
            first_name="Alice",
            last_name="Smith",
            date_of_birth=date(1970, 1, 1),
        )
        guest_two = MvPersonFactory(
            is_principal=True,
            id="person-2",
            first_name="Trevor",
            last_name="Williams",
            date_of_birth=date(1980, 1, 1),
        )

        accommodation_request = MvAccommodationRequestFactory(
            person_id=[guest_one.pk, guest_two.pk]
        )
        accommodation_request.save()
        guest_one.accommodation_request = accommodation_request
        guest_one.save()
        guest_two.accommodation_request = accommodation_request
        guest_two.save()

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one)
        duplicate_group.guests.add(guest_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={
                "first_name": "Alice",
                "last_name": "Williams",
            },
            user=user,
        )

        ar_interactions = MvInteraction.objects.filter(
            linked_accommodation_request=accommodation_request,
            interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
        )
        self.assertEqual(ar_interactions.count(), 1)
        interaction = ar_interactions.first()
        self.assertEqual(interaction.title, "Record deduplicated")
        self.assertEqual(interaction.created_by, user)

        formatted_date = date_format(duplicate_group.created_at, "j F Y")
        self.assertEqual(
            interaction.interaction_notes,
            f"Alice Smith and Trevor Williams were marked as duplicates"
            f" on {formatted_date} and replaced by a new principal record,"
            f" Alice Williams.",
        )

    def test_dedup_interactions_created_for_three_guests_on_different_ars(self):
        user = get_admin_user()
        guest_one = MvPersonFactory(
            is_principal=True,
            id="person-1",
            first_name="Alice",
            last_name="Smith",
            date_of_birth=date(1970, 1, 1),
        )
        guest_two = MvPersonFactory(
            is_principal=True,
            id="person-2",
            first_name="Trevor",
            last_name="Williams",
            date_of_birth=date(1980, 1, 1),
        )
        guest_three = MvPersonFactory(
            is_principal=True,
            id="person-3",
            first_name="Bob",
            last_name="Jones",
            date_of_birth=date(1990, 1, 1),
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

        accommodation_request_three = MvAccommodationRequestFactory(
            person_id=[guest_three.pk]
        )
        accommodation_request_three.save()
        guest_three.accommodation_request = accommodation_request_three
        guest_three.save()

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two, guest_three)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={
                "first_name": "Alice",
                "last_name": "Jones",
                "accommodation_request": accommodation_request_three,
            },
            user=user,
        )

        formatted_date = date_format(duplicate_group.created_at, "j F Y")

        for ar, name in [
            (accommodation_request_one, "Alice Smith"),
            (accommodation_request_two, "Trevor Williams"),
        ]:
            interactions = MvInteraction.objects.filter(
                linked_accommodation_request=ar,
                interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
            )
            self.assertEqual(interactions.count(), 1)
            self.assertEqual(
                interactions.first().interaction_notes,
                f"{name} was moved to another accommodation request as part of a"
                f" deduplication on {formatted_date}.\n\n"
                f"The guest was marked as a duplicate and a new principal guest"
                f" record created for Alice Jones.",
            )

        ar3_interactions = MvInteraction.objects.filter(
            linked_accommodation_request=accommodation_request_three,
            interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
        )
        self.assertEqual(ar3_interactions.count(), 1)
        self.assertEqual(
            ar3_interactions.first().interaction_notes,
            f"Bob Jones was marked as a duplicate on {formatted_date} and replaced"
            f" by a new principal record, Alice Jones.\n\n"
            f"This principal record was created after guest records"
            f" Alice Smith, Bob Jones and Trevor Williams were marked as duplicates.",
        )

    def test_dedup_interaction_on_unselected_ar_when_multiple_guests_moved_from_it(  # noqa: E501
        self,
    ):
        user = get_admin_user()
        guest_one = MvPersonFactory(
            is_principal=True,
            id="person-1",
            first_name="Alice",
            last_name="Smith",
            date_of_birth=date(1970, 1, 1),
        )
        guest_two = MvPersonFactory(
            is_principal=True,
            id="person-2",
            first_name="Trevor",
            last_name="Williams",
            date_of_birth=date(1980, 1, 1),
        )
        guest_three = MvPersonFactory(
            is_principal=True,
            id="person-3",
            first_name="Bob",
            last_name="Jones",
            date_of_birth=date(1990, 1, 1),
        )

        accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[guest_one.pk, guest_two.pk]
        )
        accommodation_request_one.save()
        guest_one.accommodation_request = accommodation_request_one
        guest_one.save()
        guest_two.accommodation_request = accommodation_request_one
        guest_two.save()

        accommodation_request_two = MvAccommodationRequestFactory(
            person_id=[guest_three.pk]
        )
        accommodation_request_two.save()
        guest_three.accommodation_request = accommodation_request_two
        guest_three.save()

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two, guest_three)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={
                "first_name": "Alice",
                "last_name": "Jones",
                "accommodation_request": accommodation_request_two,
            },
            user=user,
        )

        formatted_date = date_format(duplicate_group.created_at, "j F Y")

        ar1_interactions = MvInteraction.objects.filter(
            linked_accommodation_request=accommodation_request_one,
            interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
        )
        self.assertEqual(ar1_interactions.count(), 1)
        self.assertEqual(
            ar1_interactions.first().interaction_notes,
            f"• Alice Smith\n• Trevor Williams\n\n"
            f"were moved to another accommodation request as part of a"
            f" deduplication on {formatted_date}.\n\n"
            f"New principal guest record is Alice Jones.",
        )

    def test_dedupe_persists_person_id_changes_on_affected_ar(self):
        guest_one = MvPersonFactory(is_principal=True)
        guest_two = MvPersonFactory(is_principal=True)
        ar = MvAccommodationRequestFactory(
            person_id=[str(guest_one.pk), str(guest_two.pk)],
        )
        guest_one.accommodation_request = ar
        guest_one.save()
        guest_two.accommodation_request = ar
        guest_two.save()

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one)
        duplicate_group.guests.add(guest_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={
                "first_name": "bob",
                "accommodation_request": ar,
            },
            user=get_admin_user(),
        )

        ar.refresh_from_db()
        self.assertIn(str(duplicate_group.principal_record.pk), ar.person_id or [])
        self.assertNotIn(str(guest_one.pk), ar.person_id or [])
        self.assertNotIn(str(guest_two.pk), ar.person_id or [])

    @override_settings(ENHANCED_DEDUPLICATION_LOGGING=True)
    def test_dedupe_emits_started_and_finished_sentry_logs(self):
        guest_one = MvPersonFactory(is_principal=True)
        guest_two = MvPersonFactory(is_principal=True)
        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one)
        duplicate_group.guests.add(guest_two)
        duplicate_group.save()

        with patch("sentry_sdk.logger.info") as info:
            duplicate_group.deduplicate(
                principal_record_values={"first_name": "bob"},
                user=get_admin_user(),
            )

        messages = [call.args[0] for call in info.call_args_list]
        self.assertIn("GuestDuplicateGroup.deduplicate: started", messages)
        self.assertIn("GuestDuplicateGroup.deduplicate: finished", messages)

    def test_dedupe_emits_completed_sentry_metric(self):
        guest_one = MvPersonFactory(is_principal=True)
        guest_two = MvPersonFactory(is_principal=True)
        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one)
        duplicate_group.guests.add(guest_two)
        duplicate_group.save()

        with patch("sentry_sdk.metrics.count") as count:
            duplicate_group.deduplicate(
                principal_record_values={"first_name": "bob"},
                user=get_admin_user(),
            )

        count.assert_called_once_with(
            "deduplicate.completed",
            1,
            attributes={"record_type": "guest"},
        )

    def test_dedupe_when_ar_left_empty_sets_status_to_closed_empty(self):
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

        self.assertEqual("test one", accommodation_request_one.title)

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

    def test_dedupe_all_involved_ars_checks_status_is_recalculated_after_dedupe(self):
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
        guest_three = MvPersonFactory(
            first_name="test",
            last_name="three",
            is_principal=True,
            date_of_birth=date(1970, 1, 1),
        )

        accommodation_request_one = MvAccommodationRequestFactory(
            person_id=[guest_one.pk, guest_three.pk],
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

        self.assertEqual("test one", accommodation_request_one.title)

        duplicate_group = GuestDuplicateGroupFactory()
        duplicate_group.guests.add(guest_one, guest_two)

        duplicate_group.deduplicate(
            {"accommodation_request": accommodation_request_two},
            get_admin_user(),
        )

        accommodation_request_one.refresh_from_db()

        self.assertEqual(
            accommodation_request_one.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

        accommodation_request_two.refresh_from_db()

        self.assertEqual(
            accommodation_request_two.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )
