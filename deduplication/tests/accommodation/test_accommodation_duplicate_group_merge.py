from datetime import timedelta
from unittest.mock import patch

from django.db import connection
from django.test import TestCase, override_settings
from django.utils.timezone import now

from deduplication.exceptions import DeduplicationException
from deduplication.tests.factories import AccommodationDuplicateGroupFactory
from ontology.models import CheckType, DevCheckV2, MvAccommodationRequest
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvUkPostcodeFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import get_admin_user, get_la_user


class AccommodationDuplicateGroupDeduplicationTestCase(TestCase):
    def test_should_create_new_principal_record_when_merging(self):
        self.record_one = MvAccommodationFactory(is_principal=True)
        self.record_two = MvAccommodationFactory(is_principal=True)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.record_one.refresh_from_db()
        self.record_two.refresh_from_db()

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.is_principal)
        self.assertTrue(self.duplicate_group.principal_record.is_editable)
        self.assertTrue(self.duplicate_group.principal_record.edited_in_app)
        self.assertEqual(
            self.duplicate_group.principal_record.full_address, "123 Street"
        )

        self.assertFalse(self.record_one.is_principal)
        self.assertFalse(self.record_two.is_principal)

    def test_should_disallow_merging_non_principal_records(self):
        self.record_one = MvAccommodationFactory(is_principal=True)
        self.record_two = MvAccommodationFactory(is_principal=False)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        with self.assertRaises(DeduplicationException) as ctx:
            self.duplicate_group.deduplicate(
                principal_record_values={"full_address": "123 Street"},
                user=get_admin_user(),
            )

        self.assertEqual(
            str(ctx.exception), "Cannot deduplicate using non principal records"
        )

    def test_should_disallow_merging_fewer_than_two_records(self):
        self.record_one = MvAccommodationFactory(is_principal=True)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.save()

        with self.assertRaises(DeduplicationException) as ctx:
            self.duplicate_group.deduplicate(
                principal_record_values={"full_address": "123 Street"},
                user=get_admin_user(),
            )

        self.assertEqual(
            str(ctx.exception),
            "Require at least two constituents to perform deduplication",
        )

    def test_should_disallow_merging_already_deduplicated_duplication_groups(self):
        self.record_one = MvAccommodationFactory(is_principal=True)
        self.record_two = MvAccommodationFactory(is_principal=True)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        with self.assertRaises(DeduplicationException) as ctx:
            self.duplicate_group.deduplicate(
                principal_record_values={"full_address": "123 Street"},
                user=get_admin_user(),
            )

        self.assertEqual(
            str(ctx.exception),
            "Cannot perform deduplication on an already deduplicated group",
        )

    def test_deduplication_result_should_have_allow_pet_true_if_any_of_constituents_do(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, allow_pet=True)
        self.record_two = MvAccommodationFactory(is_principal=True, allow_pet=False)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.allow_pet)

    def test_deduplication_result_should_have_allow_pet_false_if_all_constituents_do(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, allow_pet=False)
        self.record_two = MvAccommodationFactory(is_principal=True, allow_pet=False)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertFalse(self.duplicate_group.principal_record.allow_pet)

    def test_result_should_aggregate_unique_application_numbers_of_constituents(
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, application_unique_application_number=["1a"]
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, application_unique_application_number=["2b"]
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(
                self.duplicate_group.principal_record.application_unique_application_number
            ),
            sorted(["1a", "2b"]),
        )

    def test_deduplication_result_should_aggregate_same_countries_of_constituents(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, country="England")
        self.record_two = MvAccommodationFactory(is_principal=True, country="England")

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(self.duplicate_group.principal_record.country, "England")

    def test_deduplication_result_should_aggregate_different_countries_of_constituents(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, country="England")
        self.record_two = MvAccommodationFactory(is_principal=True, country="Wales")

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(self.duplicate_group.principal_record.country),
            sorted(["England", "Wales"]),
        )

    def test_deduplication_result_should_have_the_created_at_of_constituents(self):
        self.record_one = MvAccommodationFactory(
            is_principal=True, created_at=now() - timedelta(days=1)
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, created_at=now() + timedelta(days=1)
        )
        self.record_three = MvAccommodationFactory(is_principal=True, created_at=None)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.accommodations.add(self.record_three)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            self.duplicate_group.principal_record.created_at,
            self.record_one.created_at,
        )

    def test_deduplication_result_should_have_the_created_at_constituents_null_case(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, created_at=None)

        self.record_two = MvAccommodationFactory(is_principal=True, created_at=None)

        self.record_three = MvAccommodationFactory(is_principal=True, created_at=None)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.accommodations.add(self.record_three)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertIsNone(
            self.duplicate_group.principal_record.created_at,
        )

    def test_deduplication_result_should_have_the_created_date_of_constituents(self):
        self.record_one = MvAccommodationFactory(
            is_principal=True, created_date=now() - timedelta(days=1)
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, created_date=now() + timedelta(days=1)
        )
        self.record_three = MvAccommodationFactory(is_principal=True, created_date=None)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.accommodations.add(self.record_three)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            self.duplicate_group.principal_record.created_date,
            self.record_one.created_date,
        )

    def test_deduplication_result_should_have_the_created_date_constituents_null_case(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, created_date=None)

        self.record_two = MvAccommodationFactory(is_principal=True, created_date=None)

        self.record_three = MvAccommodationFactory(is_principal=True, created_date=None)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.accommodations.add(self.record_three)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertIsNone(
            self.duplicate_group.principal_record.created_date,
        )

    def test_deduplication_result_aggregates_gwf_of_constituents(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, gwf=["gwf-1"])
        self.record_two = MvAccommodationFactory(is_principal=True, gwf=["gwf-2"])

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(self.duplicate_group.principal_record.gwf),
            sorted(["gwf-1", "gwf-2"]),
        )

    def test_result_should_have_is_accommodation_true_if_any_of_constituents_do(
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, is_accommodation=True
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, is_accommodation=False
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.is_accommodation)

    def test_deduplication_should_have_is_accommodation_false_if_all_constituents_do(
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, is_accommodation=False
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, is_accommodation=False
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertFalse(self.duplicate_group.principal_record.is_accommodation)

    def test_deduplication_result_should_have_is_eoi_true_if_any_of_constituents_do(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, is_eoi=True)
        self.record_two = MvAccommodationFactory(is_principal=True, is_eoi=False)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.is_eoi)

    def test_deduplication_result_should_have_is_eoi_false_if_all_constituents_do(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, is_eoi=False)
        self.record_two = MvAccommodationFactory(is_principal=True, is_eoi=False)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertFalse(self.duplicate_group.principal_record.is_eoi)

    def test_result_should_have_is_residential_true_if_any_of_constituents_do(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, is_residential=True)
        self.record_two = MvAccommodationFactory(
            is_principal=True, is_residential=False
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.is_residential)

    def test_result_should_have_is_residential_false_if_all_constituents_do(
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, is_residential=False
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, is_residential=False
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertFalse(self.duplicate_group.principal_record.is_residential)

    def test_result_should_have_the_latest_last_modified_date_of_constituents(
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, last_modified_date=now() - timedelta(days=1)
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, last_modified_date=now() + timedelta(days=1)
        )
        self.record_three = MvAccommodationFactory(
            is_principal=True, last_modified_date=None
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.accommodations.add(self.record_three)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            self.duplicate_group.principal_record.last_modified_date,
            self.record_two.last_modified_date,
        )

    def test_deduplication_result_should_have_the_latest_last_modified_date_null_case(
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, last_modified_date=None
        )

        self.record_two = MvAccommodationFactory(
            is_principal=True, last_modified_date=None
        )

        self.record_three = MvAccommodationFactory(
            is_principal=True, last_modified_date=None
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.accommodations.add(self.record_three)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertIsNone(
            self.duplicate_group.principal_record.last_modified_date,
        )

    def test_deduplication_result_should_have_local_authority_populated_by_ltla_name(
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, local_authority="Westminster", ltla_name="Westminster"
        )

        self.record_two = MvAccommodationFactory(
            is_principal=True, local_authority="Camden", ltla_name="Camden"
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)

        self.duplicate_group.deduplicate(
            principal_record_values={
                "full_address": "123 Street",
                "ltla_name": "Westminster",
            },
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            self.duplicate_group.principal_record.local_authority, "Westminster"
        )

    def test_result_should_have_notional_data_true_if_any_of_constituents_do(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, notional_data=True)
        self.record_two = MvAccommodationFactory(is_principal=True, notional_data=False)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.notional_data)

    def test_result_should_have_notional_data_false_if_all_constituents_do(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, notional_data=False)
        self.record_two = MvAccommodationFactory(is_principal=True, notional_data=False)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertFalse(self.duplicate_group.principal_record.notional_data)

    def test_deduplication_result_should_have_number_adults_set_when_they_are_same(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, number_adults=2)
        self.record_two = MvAccommodationFactory(is_principal=True, number_adults=2)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertEqual(self.duplicate_group.principal_record.number_adults, 2)

    def test_result_should_not_have_number_adults_set_when_they_are_different(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, number_adults=2)
        self.record_two = MvAccommodationFactory(is_principal=True, number_adults=3)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertIsNone(self.duplicate_group.principal_record.number_adults)

    def test_deduplication_result_should_have_number_children_set_when_they_are_same(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, number_children=2)
        self.record_two = MvAccommodationFactory(is_principal=True, number_children=2)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertEqual(self.duplicate_group.principal_record.number_children, 2)

    def test_result_should_not_have_number_children_set_when_they_are_different(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, number_children=2)
        self.record_two = MvAccommodationFactory(is_principal=True, number_children=3)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertIsNone(self.duplicate_group.principal_record.number_children)

    def test_deduplication_result_should_have_number_of_double_rooms_available_set_when_they_are_same(  # noqa: E501
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, number_of_double_rooms_available=2
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, number_of_double_rooms_available=2
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertEqual(
            self.duplicate_group.principal_record.number_of_double_rooms_available, 2
        )

    def test_deduplication_result_should_not_have_number_of_double_rooms_available_set_when_they_are_different(  # noqa: E501
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, number_of_double_rooms_available=2
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, number_of_double_rooms_available=3
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertIsNone(
            self.duplicate_group.principal_record.number_of_double_rooms_available
        )

    def test_result_should_have_number_of_single_rooms_set_when_they_are_same(
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, number_of_single_rooms=2
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, number_of_single_rooms=2
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertEqual(
            self.duplicate_group.principal_record.number_of_single_rooms, 2
        )

    def test_deduplication_result_should_not_have_number_of_single_rooms_set_when_they_are_different(  # noqa: E501
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, number_of_single_rooms=2
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, number_of_single_rooms=3
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertIsNone(self.duplicate_group.principal_record.number_of_single_rooms)

    def test_deduplication_result_aggregates_response_id_of_constituents(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, response_id=["1a"])
        self.record_two = MvAccommodationFactory(is_principal=True, response_id=["2b"])

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(self.duplicate_group.principal_record.response_id),
            sorted(["1a", "2b"]),
        )

    def test_deduplication_result_should_have_the_latest_checks_date_of_constituents(
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, requested_checks_latest_date=now() - timedelta(days=1)
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, requested_checks_latest_date=now() + timedelta(days=1)
        )
        self.record_three = MvAccommodationFactory(
            is_principal=True, requested_checks_latest_date=None
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.accommodations.add(self.record_three)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            self.duplicate_group.principal_record.requested_checks_latest_date,
            self.record_two.requested_checks_latest_date,
        )

    def test_result_should_have_the_latest_checks_date_of_constituents_null_case(  # noqa: E501
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, requested_checks_latest_date=None
        )

        self.record_two = MvAccommodationFactory(
            is_principal=True, requested_checks_latest_date=None
        )

        self.record_three = MvAccommodationFactory(
            is_principal=True, requested_checks_latest_date=None
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.accommodations.add(self.record_three)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertIsNone(
            self.duplicate_group.principal_record.requested_checks_latest_date,
        )

    def test_deduplication_result_aggregates_source_of_constituents(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True, source=["a"])
        self.record_two = MvAccommodationFactory(is_principal=True, source=["b"])

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(self.duplicate_group.principal_record.source),
            sorted(["a", "b"]),
        )

    def test_deduplication_result_aggregates_sponsorship_certification_numbers(
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, sponsorship_certification_number_id=["1a"]
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, sponsorship_certification_number_id=["2b"]
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={
                "full_address": "123 Street",
                "postcode": self.record_one.postcode,
                "ltla_name": self.record_one.ltla_name,
                "utla_name": self.record_one.utla_name,
            },
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(
                self.duplicate_group.principal_record.sponsorship_certification_number_id
            ),
            sorted(["1a", "2b"]),
        )

    def test_deduplication_result_aggregates_submission_guids_from_two_guid_fields_of_constituents(  # noqa: E501
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, submission_guid="123"
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, submission_guids=["345", "567"]
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={
                "full_address": "123 Street",
            },
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(self.duplicate_group.principal_record.submission_guids),
            sorted(["123", "345", "567"]),
        )

    def test_deduplication_result_aggregates_viewer_group_names_of_constituents(
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, viewer_group_names=["group_a"]
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, viewer_group_names=["group_b"]
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(self.duplicate_group.principal_record.viewer_group_names),
            sorted(["group_a", "group_b"]),
        )

    def test_deduplication_result_should_pick_a_non_none_volunteer_from_constituents(
        self,
    ):
        self.volunteer_one = MvVolunteerFactory()
        self.volunteer_two = MvVolunteerFactory()
        self.record_one = MvAccommodationFactory(
            is_principal=True, volunteer=self.volunteer_one
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, volunteer=self.volunteer_two
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertIn(
            self.duplicate_group.principal_record.volunteer,
            [self.volunteer_one, self.volunteer_two],
        )

    def test_deduplication_result_should_set_volunteer_to_none_if_no_volunteers(self):
        self.record_one = MvAccommodationFactory(is_principal=True, volunteer=None)
        self.record_two = MvAccommodationFactory(is_principal=True, volunteer=None)

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertIsNone(self.duplicate_group.principal_record.volunteer)

    def test_deduplication_result_should_set_volunteer_to_only_valid_volunteer(self):
        self.volunteer_one = MvVolunteerFactory()
        self.record_one = MvAccommodationFactory(
            is_principal=True, volunteer=self.volunteer_one
        )
        self.record_two = MvAccommodationFactory(is_principal=True)

        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE ontology_mvaccommodation SET volunteer_id = %s WHERE id = %s",
                ["12344", self.record_two.id],
            )

        self.record_two.refresh_from_db()
        self.assertEqual(self.record_two.volunteer_id, "12344")

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            self.duplicate_group.principal_record.volunteer, self.volunteer_one
        )

    def test_deduplication_result_should_aggregate_what_type_of_living_space_can_you_offer_of_constituents(  # noqa: E501
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, what_type_of_living_space_can_you_offer=["A", "B"]
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, what_type_of_living_space_can_you_offer=["A", "C"]
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(
                self.duplicate_group.principal_record.what_type_of_living_space_can_you_offer
            ),
            sorted(["A", "B", "C"]),
        )

    def test_deduplication_result_should_have_wheelchair_accessible_true_if_any_of_constituents_do(  # noqa: E501
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, wheelchair_accessible=True
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, wheelchair_accessible=False
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.wheelchair_accessible)

    def test_deduplication_result_should_have_wheelchair_accessible_false_if_all_constituents_do(  # noqa: E501
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, is_accommodation=False
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, is_accommodation=False
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertFalse(self.duplicate_group.principal_record.wheelchair_accessible)

    def test_deduplication_result_should_aggregate_same_who_can_you_accommodate_of_constituents(  # noqa: E501
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, who_can_you_accommodate="X"
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, who_can_you_accommodate="X"
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            self.duplicate_group.principal_record.who_can_you_accommodate, "X"
        )

    def test_deduplication_result_should_aggregate_different_who_can_you_accommodate_of_constituents(  # noqa: E501
        self,
    ):
        self.record_one = MvAccommodationFactory(
            is_principal=True, who_can_you_accommodate="X"
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, who_can_you_accommodate="Y"
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(self.duplicate_group.principal_record.who_can_you_accommodate),
            sorted(["X", "Y"]),
        )

    def test_deduplication_result_should_set_postcode_user_selected_answer(self):
        self.postcode_one = MvUkPostcodeFactory()
        self.postcode_two = MvUkPostcodeFactory()
        self.record_one = MvAccommodationFactory(
            is_principal=True, postcode=self.postcode_one
        )
        self.record_two = MvAccommodationFactory(
            is_principal=True, postcode=self.postcode_two
        )

        self.duplicate_group = AccommodationDuplicateGroupFactory()

        self.duplicate_group.accommodations.add(self.record_one)
        self.duplicate_group.accommodations.add(self.record_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={
                "full_address": "123 Street",
                "postcode": self.postcode_one,
            },
            user=get_admin_user(),
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            self.duplicate_group.principal_record.postcode, self.postcode_one
        )

    def test_result_is_linked_to_ars_of_the_constituents_via_accommodation_id(
        self,
    ):
        self.record_one = MvAccommodationFactory(is_principal=True)
        accommodation_request_one = MvAccommodationRequestFactory(
            primary_accommodation=self.record_one,
            accommodation_id=[self.record_one.pk],
        )

        self.record_two = MvAccommodationFactory(is_principal=True)
        accommodation_request_two = MvAccommodationRequestFactory(
            primary_accommodation=self.record_two,
            accommodation_id=[self.record_two.pk],
        )

        duplicate_group = AccommodationDuplicateGroupFactory()

        duplicate_group.accommodations.add(self.record_one)
        duplicate_group.accommodations.add(self.record_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        accommodation_request_one.refresh_from_db()
        accommodation_request_two.refresh_from_db()

        self.assertIn(
            duplicate_group.principal_record.pk,
            accommodation_request_one.accommodation_id,
        )
        self.assertIn(
            duplicate_group.principal_record.pk,
            accommodation_request_two.accommodation_id,
        )

    def test_deduplication_result_is_set_as_primary_accommodation_of_relevant_ars(self):
        self.record_one = MvAccommodationFactory(is_principal=True)
        accommodation_request_one = MvAccommodationRequestFactory(
            primary_accommodation=self.record_one,
            accommodation_id=[self.record_one.pk],
        )

        self.record_two = MvAccommodationFactory(is_principal=True)
        accommodation_request_two = MvAccommodationRequestFactory(
            primary_accommodation=self.record_two,
            accommodation_id=[self.record_two.pk],
        )

        duplicate_group = AccommodationDuplicateGroupFactory()

        duplicate_group.accommodations.add(self.record_one)
        duplicate_group.accommodations.add(self.record_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        accommodation_request_one.refresh_from_db()
        accommodation_request_two.refresh_from_db()

        self.assertEqual(
            accommodation_request_one.primary_accommodation,
            duplicate_group.principal_record,
        )
        self.assertEqual(
            accommodation_request_two.primary_accommodation,
            duplicate_group.principal_record,
        )

    @override_settings(ENHANCED_DEDUPLICATION_LOGGING=True)
    def test_dedupe_emits_started_and_finished_sentry_logs(self):
        accommodation_one = MvAccommodationFactory(is_principal=True)
        accommodation_two = MvAccommodationFactory(is_principal=True)
        duplicate_group = AccommodationDuplicateGroupFactory()
        duplicate_group.accommodations.add(accommodation_one)
        duplicate_group.accommodations.add(accommodation_two)
        duplicate_group.save()

        with patch("sentry_sdk.logger.info") as info:
            duplicate_group.deduplicate(
                principal_record_values={},
                user=get_admin_user(),
            )

        messages = [call.args[0] for call in info.call_args_list]
        self.assertIn("AccommodationDuplicateGroup.deduplicate: started", messages)
        self.assertIn("AccommodationDuplicateGroup.deduplicate: finished", messages)

    @override_settings(ENHANCED_DEDUPLICATION_LOGGING=True)
    def test_undo_emits_started_and_finished_sentry_logs(self):
        accommodation_one = MvAccommodationFactory(is_principal=True)
        accommodation_two = MvAccommodationFactory(is_principal=True)
        duplicate_group = AccommodationDuplicateGroupFactory()
        duplicate_group.accommodations.add(accommodation_one)
        duplicate_group.accommodations.add(accommodation_two)
        duplicate_group.save()
        duplicate_group.deduplicate(
            principal_record_values={},
            user=get_admin_user(),
        )

        with patch("sentry_sdk.logger.info") as info:
            duplicate_group.undo_deduplication(user=get_admin_user())

        messages = [call.args[0] for call in info.call_args_list]
        self.assertIn(
            "AccommodationDuplicateGroup.undo_deduplication: started", messages
        )
        self.assertIn(
            "AccommodationDuplicateGroup.undo_deduplication: finished", messages
        )

    def test_dedupe_emits_completed_sentry_metric(self):
        accommodation_one = MvAccommodationFactory(is_principal=True)
        accommodation_two = MvAccommodationFactory(is_principal=True)
        duplicate_group = AccommodationDuplicateGroupFactory()
        duplicate_group.accommodations.add(accommodation_one)
        duplicate_group.accommodations.add(accommodation_two)
        duplicate_group.save()

        with patch("sentry_sdk.metrics.count") as count:
            duplicate_group.deduplicate(
                principal_record_values={},
                user=get_admin_user(),
            )

        count.assert_called_once_with(
            "deduplicate.completed",
            1,
            attributes={"record_type": "accommodation"},
        )

    def test_undo_emits_completed_sentry_metric(self):
        accommodation_one = MvAccommodationFactory(is_principal=True)
        accommodation_two = MvAccommodationFactory(is_principal=True)
        duplicate_group = AccommodationDuplicateGroupFactory()
        duplicate_group.accommodations.add(accommodation_one)
        duplicate_group.accommodations.add(accommodation_two)
        duplicate_group.save()
        duplicate_group.deduplicate(
            principal_record_values={},
            user=get_admin_user(),
        )

        with patch("sentry_sdk.metrics.count") as count:
            duplicate_group.undo_deduplication(user=get_admin_user())

        count.assert_called_once_with(
            "undo_deduplication.completed",
            1,
            attributes={"record_type": "accommodation"},
        )

    def test_undedupe_recalculates_checks_on_linked_ars_no_existing_checks(self):
        accommodation_one = MvAccommodationFactory(is_principal=True)
        accommodation_two = MvAccommodationFactory(is_principal=True)

        accommodation_request_one = MvAccommodationRequestFactory(
            primary_accommodation=accommodation_one,
            accommodation_id=[accommodation_one.pk],
        )

        accommodation_request_one.save()

        accommodation_request_two = MvAccommodationRequestFactory(
            primary_accommodation=accommodation_two,
            accommodation_id=[accommodation_two.pk],
        )

        accommodation_request_two.save()

        duplicate_group = AccommodationDuplicateGroupFactory()
        duplicate_group.accommodations.add(accommodation_one)
        duplicate_group.accommodations.add(accommodation_two)
        duplicate_group.save()
        duplicate_group.deduplicate(
            principal_record_values={},
            user=get_admin_user(),
        )

        accommodation_request_one.checks_status = (
            accommodation_request_one.determine_checks_status_from_linked_objects()
        )

        accommodation_request_one.refresh_from_db()

        self.assertEqual(
            accommodation_request_one.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

        duplicate_group.undo_deduplication(user=get_admin_user())
        accommodation_request_one.refresh_from_db()

        self.assertEqual(
            accommodation_request_one.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

    def test_undedupe_recalculates_checks_on_linked_ars_failed_checks(self):
        accommodation_one = MvAccommodationFactory(is_principal=True)
        accommodation_two = MvAccommodationFactory(is_principal=True)

        accommodation_request_one = MvAccommodationRequestFactory(
            primary_accommodation=accommodation_one,
            accommodation_id=[accommodation_one.pk],
        )

        accommodation_request_one.save()

        accommodation_request_two = MvAccommodationRequestFactory(
            primary_accommodation=accommodation_two,
            accommodation_id=[accommodation_two.pk],
        )

        accommodation_request_two.save()

        accom_suitable_check_1 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
        )
        accom_suitable_check_1.accommodation.set([accommodation_one])

        accom_suitable_check_1.check_status = DevCheckV2.CheckStatus.FAILED

        accom_suitable_check_1.AR.set([accommodation_request_one])

        accom_suitable_check_1.save()

        accom_suitable_check_2 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
        )
        accom_suitable_check_2.accommodation.set([accommodation_two])

        accom_suitable_check_2.check_status = DevCheckV2.CheckStatus.PASSED

        accom_suitable_check_2.AR.set([accommodation_request_two])

        accom_suitable_check_2.save()

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

        duplicate_group = AccommodationDuplicateGroupFactory()
        duplicate_group.accommodations.add(accommodation_one)
        duplicate_group.accommodations.add(accommodation_two)
        duplicate_group.save()
        duplicate_group.deduplicate(
            principal_record_values={},
            user=get_admin_user(),
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

        duplicate_group.undo_deduplication(user=get_admin_user())
        accommodation_request_one.refresh_from_db()

        self.assertEqual(
            accommodation_request_one.checks_status,
            MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED,
        )

        accommodation_request_two.refresh_from_db()

        self.assertEqual(
            accommodation_request_two.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED,
        )

    def _assert_deduplication_does_not_change_ar_checks_status(self, checks_status):
        accommodation_one = MvAccommodationFactory(is_principal=True)
        accommodation_two = MvAccommodationFactory(is_principal=True)
        ar = MvAccommodationRequestFactory(
            primary_accommodation=accommodation_one,
            accommodation_id=[accommodation_one.pk],
            checks_status=checks_status,
        )

        duplicate_group = AccommodationDuplicateGroupFactory()
        duplicate_group.accommodations.add(accommodation_one)
        duplicate_group.accommodations.add(accommodation_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        ar.refresh_from_db()
        self.assertEqual(ar.checks_status, checks_status)

    def test_deduplication_does_not_reopen_closed_left_programme_ar(self):
        self._assert_deduplication_does_not_change_ar_checks_status(
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME
        )

    def test_deduplication_does_not_reopen_closed_duplicate_ar(self):
        self._assert_deduplication_does_not_change_ar_checks_status(
            MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE
        )

    def test_deduplication_does_not_reopen_cancelled_ar(self):
        self._assert_deduplication_does_not_change_ar_checks_status(
            MvAccommodationRequest.ChecksStatus.CANCELLED
        )

    def test_deduplication_does_not_reopen_closed_empty_ar(self):
        self._assert_deduplication_does_not_change_ar_checks_status(
            MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY
        )

    def _assert_undo_deduplication_does_not_change_ar_checks_status(
        self, checks_status
    ):
        accommodation_one = MvAccommodationFactory(is_principal=True)
        accommodation_two = MvAccommodationFactory(is_principal=True)
        ar = MvAccommodationRequestFactory(
            primary_accommodation=accommodation_one,
            accommodation_id=[accommodation_one.pk],
            checks_status=checks_status,
        )

        duplicate_group = AccommodationDuplicateGroupFactory()
        duplicate_group.accommodations.add(accommodation_one)
        duplicate_group.accommodations.add(accommodation_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        duplicate_group.undo_deduplication(user=get_admin_user())

        ar.refresh_from_db()
        self.assertEqual(ar.checks_status, checks_status)

    def test_undo_deduplication_does_not_reopen_closed_left_programme_ar(self):
        self._assert_undo_deduplication_does_not_change_ar_checks_status(
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME
        )

    def test_undo_deduplication_does_not_reopen_closed_duplicate_ar(self):
        self._assert_undo_deduplication_does_not_change_ar_checks_status(
            MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE
        )

    def test_undo_deduplication_does_not_reopen_cancelled_ar(self):
        self._assert_undo_deduplication_does_not_change_ar_checks_status(
            MvAccommodationRequest.ChecksStatus.CANCELLED
        )

    def test_undo_deduplication_does_not_reopen_closed_empty_ar(self):
        self._assert_undo_deduplication_does_not_change_ar_checks_status(
            MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY
        )

    def test_deduplication_sets_last_modified_fields_on_linked_ar(self):
        accommodation_one = MvAccommodationFactory(
            is_principal=True, ltla_name="ltla_somerset"
        )
        accommodation_two = MvAccommodationFactory(
            is_principal=True, ltla_name="ltla_somerset"
        )
        ar = MvAccommodationRequestFactory(
            primary_accommodation=accommodation_one,
            accommodation_id=[accommodation_one.pk],
        )

        duplicate_group = AccommodationDuplicateGroupFactory()
        duplicate_group.accommodations.add(accommodation_one)
        duplicate_group.accommodations.add(accommodation_two)
        duplicate_group.save()

        user = get_la_user()
        before = now()
        duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=user,
        )

        ar.refresh_from_db()
        self.assertEqual(ar.last_modified_by, user.get_full_name())
        self.assertIsNotNone(ar.last_modified_at)
        self.assertGreaterEqual(ar.last_modified_at, before)

    def test_undo_deduplication_sets_last_modified_fields_on_linked_ar(self):
        accommodation_one = MvAccommodationFactory(
            is_principal=True, ltla_name="ltla_somerset"
        )
        accommodation_two = MvAccommodationFactory(
            is_principal=True, ltla_name="ltla_somerset"
        )
        ar = MvAccommodationRequestFactory(
            primary_accommodation=accommodation_one,
            accommodation_id=[accommodation_one.pk],
        )

        duplicate_group = AccommodationDuplicateGroupFactory()
        duplicate_group.accommodations.add(accommodation_one)
        duplicate_group.accommodations.add(accommodation_two)
        duplicate_group.save()

        user = get_la_user()
        duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=user,
        )

        before = now()
        duplicate_group.undo_deduplication(user=user)

        ar.refresh_from_db()
        self.assertEqual(ar.last_modified_by, user.get_full_name())
        self.assertIsNotNone(ar.last_modified_at)
        self.assertGreaterEqual(ar.last_modified_at, before)

    def test_deduplication_result_is_linked_to_hosts_of_the_constituents(self):
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

        duplicate_group.deduplicate(
            principal_record_values={"full_address": "123 Street"},
            user=get_admin_user(),
        )

        principal_hosts = duplicate_group.principal_record.hosts.all()
        self.assertEqual(duplicate_group.principal_record.hosts.count(), 3)
        self.assertIn(sponsor_one, principal_hosts)
        self.assertIn(sponsor_two, principal_hosts)
        self.assertIn(sponsor_three, principal_hosts)
