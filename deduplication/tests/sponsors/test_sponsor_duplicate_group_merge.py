from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils.timezone import now

from deduplication.exceptions import DeduplicationException
from deduplication.tests.factories import SponsorDuplicateGroupFactory
from ontology.models import CheckType, DevCheckV2, MvAccommodationRequest
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import get_admin_user


class SponsorDuplicateGroupDeduplicationTestCase(TestCase):
    def test_should_create_new_principal_record_when_merging(self):
        self.sponsor_one = MvVolunteerFactory(is_principal=True)
        self.sponsor_two = MvVolunteerFactory(is_principal=True)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.sponsor_one.refresh_from_db()
        self.sponsor_two.refresh_from_db()

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.is_principal)
        self.assertEqual(self.duplicate_group.principal_record.first_name, "bob")

        self.assertFalse(self.sponsor_one.is_principal)
        self.assertFalse(self.sponsor_two.is_principal)

    def test_should_disallow_merging_non_principal_records(self):
        self.sponsor_one = MvVolunteerFactory(is_principal=True)
        self.sponsor_two = MvVolunteerFactory(is_principal=False)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        with self.assertRaises(DeduplicationException) as ctx:
            self.duplicate_group.deduplicate(
                principal_record_values={"first_name": "bob"}, user=get_admin_user()
            )

        self.assertEqual(
            str(ctx.exception), "Cannot deduplicate using non principal records"
        )

    def test_should_disallow_merging_fewer_than_two_records(self):
        self.sponsor_one = MvVolunteerFactory(is_principal=True)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
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
        self.sponsor_one = MvVolunteerFactory(is_principal=True)
        self.sponsor_two = MvVolunteerFactory(is_principal=True)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
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

    def test_result_should_have_notional_data_true_if_any_of_constituents_do(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(is_principal=True, notional_data=True)
        self.sponsor_two = MvVolunteerFactory(is_principal=True, notional_data=False)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.notional_data)

    def test_result_should_have_notional_data_false_if_all_constituents_do(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(is_principal=True, notional_data=False)
        self.sponsor_two = MvVolunteerFactory(is_principal=True, notional_data=False)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertFalse(self.duplicate_group.principal_record.notional_data)

    def test_result_should_aggregate_unique_application_numbers_of_constituents(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(
            is_principal=True, application_unique_application_number=["1a"]
        )
        self.sponsor_two = MvVolunteerFactory(
            is_principal=True, application_unique_application_number=["2b"]
        )

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(
                self.duplicate_group.principal_record.application_unique_application_number
            ),
            sorted(["1a", "2b"]),
        )

    def test_result_should_have_adverse_hit_true_if_any_of_constituents_do(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(is_principal=True, adverse_hit=True)
        self.sponsor_two = MvVolunteerFactory(is_principal=True, adverse_hit=False)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.adverse_hit)

    def test_deduplication_result_should_have_adverse_hit_false_if_all_constituents_do(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(is_principal=True, adverse_hit=False)
        self.sponsor_two = MvVolunteerFactory(is_principal=True, adverse_hit=False)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertFalse(self.duplicate_group.principal_record.adverse_hit)

    def test_result_aggregates_sponsorship_certification_numbers_of_constituents(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(
            is_principal=True, sponsorship_certification_number_id=["1a"]
        )
        self.sponsor_two = MvVolunteerFactory(
            is_principal=True, sponsorship_certification_number_id=["2b"]
        )

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
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
        self.sponsor_one = MvVolunteerFactory(is_principal=True, source=["a"])
        self.sponsor_two = MvVolunteerFactory(is_principal=True, source=["b"])

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
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
        self.sponsor_one = MvVolunteerFactory(
            is_principal=True, viewer_group_names=["group_a"]
        )
        self.sponsor_two = MvVolunteerFactory(
            is_principal=True, viewer_group_names=["group_b"]
        )

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
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
        self.sponsor_one = MvVolunteerFactory(is_principal=True, gwf=["gwf-1"])
        self.sponsor_two = MvVolunteerFactory(is_principal=True, gwf=["gwf-2"])

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(self.duplicate_group.principal_record.gwf),
            sorted(["gwf-1", "gwf-2"]),
        )

    def test_deduplication_result_aggregates_response_id_of_constituents(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(is_principal=True, response_id=["1a"])
        self.sponsor_two = MvVolunteerFactory(is_principal=True, response_id=["2b"])

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            sorted(self.duplicate_group.principal_record.response_id),
            sorted(["1a", "2b"]),
        )

    def test_deduplication_result_should_have_the_latest_checks_date_of_constituents(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(
            is_principal=True, requested_checks_latest_date=now() - timedelta(days=1)
        )
        self.sponsor_two = MvVolunteerFactory(
            is_principal=True, requested_checks_latest_date=now() + timedelta(days=1)
        )
        self.sponsor_three = MvVolunteerFactory(
            is_principal=True, requested_checks_latest_date=None
        )

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.sponsors.add(self.sponsor_three)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            self.duplicate_group.principal_record.requested_checks_latest_date,
            self.sponsor_two.requested_checks_latest_date,
        )

    def test_result_should_have_the_latest_checks_date_of_constituents_null_case(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(
            is_principal=True, requested_checks_latest_date=None
        )

        self.sponsor_two = MvVolunteerFactory(
            is_principal=True, requested_checks_latest_date=None
        )

        self.sponsor_three = MvVolunteerFactory(
            is_principal=True, requested_checks_latest_date=None
        )

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.sponsors.add(self.sponsor_three)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertIsNone(
            self.duplicate_group.principal_record.requested_checks_latest_date,
        )

    def test_deduplication_result_should_have_is_eoi_true_if_any_of_constituents_do(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(is_principal=True, is_eoi=True)
        self.sponsor_two = MvVolunteerFactory(is_principal=True, is_eoi=False)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.is_eoi)

    def test_deduplication_result_should_have_is_eoi_false_if_all_constituents_do(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(is_principal=True, is_eoi=False)
        self.sponsor_two = MvVolunteerFactory(is_principal=True, is_eoi=False)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertFalse(self.duplicate_group.principal_record.is_eoi)

    def test_deduplication_result_should_have_is_sponsor_true_if_any_of_constituents_do(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(is_principal=True, is_sponsor=True)
        self.sponsor_two = MvVolunteerFactory(is_principal=True, is_sponsor=False)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertTrue(self.duplicate_group.principal_record.is_sponsor)

    def test_deduplication_result_should_have_is_sponsor_false_if_all_constituents_do(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(is_principal=True, is_sponsor=False)
        self.sponsor_two = MvVolunteerFactory(is_principal=True, is_sponsor=False)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertFalse(self.duplicate_group.principal_record.is_sponsor)

    def test_result_should_have_the_earliest_creation_date_of_constituents(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(
            is_principal=True, created_date=now() - timedelta(days=1)
        )
        self.sponsor_two = MvVolunteerFactory(
            is_principal=True, created_date=now() + timedelta(days=1)
        )
        self.sponsor_three = MvVolunteerFactory(is_principal=True, created_date=None)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.sponsors.add(self.sponsor_three)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            self.duplicate_group.principal_record.created_date,
            self.sponsor_one.created_date,
        )

    def test_deduplication_result_should_have_the_earliest_creation_date_null_case(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(is_principal=True, created_date=None)

        self.sponsor_two = MvVolunteerFactory(is_principal=True, created_date=None)

        self.sponsor_three = MvVolunteerFactory(is_principal=True, created_date=None)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.sponsors.add(self.sponsor_three)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertIsNone(
            self.duplicate_group.principal_record.created_date,
        )

    def test_result_should_have_the_latest_last_updated_date_of_constituents(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(
            is_principal=True, last_updated_date=now() - timedelta(days=1)
        )
        self.sponsor_two = MvVolunteerFactory(
            is_principal=True, last_updated_date=now() + timedelta(days=1)
        )
        self.sponsor_three = MvVolunteerFactory(
            is_principal=True, last_updated_date=None
        )

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.sponsors.add(self.sponsor_three)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertEqual(
            self.duplicate_group.principal_record.last_updated_date,
            self.sponsor_two.last_updated_date,
        )

    def test_deduplication_result_should_have_the_latest_last_updated_date_null_case(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(is_principal=True, last_updated_date=None)

        self.sponsor_two = MvVolunteerFactory(is_principal=True, last_updated_date=None)

        self.sponsor_three = MvVolunteerFactory(
            is_principal=True, last_updated_date=None
        )

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.sponsors.add(self.sponsor_three)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.assertIsNotNone(self.duplicate_group.principal_record)
        self.assertIsNone(
            self.duplicate_group.principal_record.last_updated_date,
        )

    def test_result_should_have_the_age_value_calculated_from_date_of_birth(
        self,
    ):
        self.sponsor_one = MvVolunteerFactory(is_principal=True)
        self.sponsor_two = MvVolunteerFactory(is_principal=True)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        principal_record_values = {
            "date_of_birth": (datetime(2000, 1, 1, tzinfo=timezone.utc).date()),
        }

        self.duplicate_group.deduplicate(
            principal_record_values=principal_record_values, user=get_admin_user()
        )

        def calculate_age(dob: date) -> int:
            today = date.today()
            return (
                today.year
                - dob.year
                - ((today.month, today.day) < (dob.month, dob.day))
            )

        self.assertIsNotNone(self.duplicate_group.principal_record)

        self.assertEqual(
            self.duplicate_group.principal_record.age,
            calculate_age(principal_record_values["date_of_birth"]),
        )

    def test_deduplication_result_is_linked_to_accommodations_of_the_constituents(self):
        self.accommodation_one = MvAccommodationFactory()
        self.sponsor_one = MvVolunteerFactory(is_principal=True)
        self.sponsor_one.accommodations.add(self.accommodation_one)

        self.accommodation_two = MvAccommodationFactory()
        self.accommodation_three = MvAccommodationFactory()
        self.sponsor_two = MvVolunteerFactory(is_principal=True)
        self.sponsor_two.accommodations.add(self.accommodation_two)
        self.sponsor_two.accommodations.add(self.accommodation_three)

        self.duplicate_group = SponsorDuplicateGroupFactory()

        self.duplicate_group.sponsors.add(self.sponsor_one)
        self.duplicate_group.sponsors.add(self.sponsor_two)
        self.duplicate_group.save()

        self.duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        self.accommodation_one.refresh_from_db()
        self.accommodation_two.refresh_from_db()
        self.accommodation_three.refresh_from_db()

        self.assertEqual(
            self.duplicate_group.principal_record.accommodations.count(), 3
        )
        self.assertIn(
            self.accommodation_one,
            self.duplicate_group.principal_record.accommodations.all(),
        )
        self.assertIn(
            self.accommodation_two,
            self.duplicate_group.principal_record.accommodations.all(),
        )
        self.assertIn(
            self.accommodation_three,
            self.duplicate_group.principal_record.accommodations.all(),
        )
        self.assertEqual(
            self.accommodation_one.volunteer, self.duplicate_group.principal_record
        )
        self.assertEqual(
            self.accommodation_two.volunteer, self.duplicate_group.principal_record
        )
        self.assertEqual(
            self.accommodation_three.volunteer, self.duplicate_group.principal_record
        )

    def test_deduplication_result_is_linked_to_ars_of_the_constituents_via_sponsor_id(
        self,
    ):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        accommodation_request_one = MvAccommodationRequestFactory(
            primary_sponsor=sponsor_one,
            sponsor_id=[sponsor_one.pk],
        )

        sponsor_two = MvVolunteerFactory(is_principal=True)
        accommodation_request_two = MvAccommodationRequestFactory(
            primary_sponsor=sponsor_two,
            sponsor_id=[sponsor_two.pk],
        )

        duplicate_group = SponsorDuplicateGroupFactory()

        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        accommodation_request_one.refresh_from_db()
        accommodation_request_two.refresh_from_db()

        self.assertIn(
            duplicate_group.principal_record.pk, accommodation_request_one.sponsor_id
        )
        self.assertIn(
            duplicate_group.principal_record.pk, accommodation_request_two.sponsor_id
        )

    def test_constituents_is_unlinked_from_ars_sponsor_id(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        accommodation_request_one = MvAccommodationRequestFactory(
            primary_sponsor=sponsor_one,
            sponsor_id=[sponsor_one.pk],
        )

        sponsor_two = MvVolunteerFactory(is_principal=True)
        accommodation_request_two = MvAccommodationRequestFactory(
            primary_sponsor=sponsor_two,
            sponsor_id=[sponsor_two.pk],
        )

        duplicate_group = SponsorDuplicateGroupFactory()

        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        accommodation_request_one.refresh_from_db()
        accommodation_request_two.refresh_from_db()

        self.assertNotIn(sponsor_one.pk, accommodation_request_one.sponsor_id)
        self.assertNotIn(sponsor_two.pk, accommodation_request_two.sponsor_id)

    def test_deduplication_result_is_set_as_primary_sponsor_of_relevant_ars(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        accommodation_request_one = MvAccommodationRequestFactory(
            primary_sponsor=sponsor_one,
            sponsor_id=[sponsor_one.pk],
        )

        sponsor_two = MvVolunteerFactory(is_principal=True)
        accommodation_request_two = MvAccommodationRequestFactory(
            primary_sponsor=sponsor_two,
            sponsor_id=[sponsor_two.pk],
        )

        duplicate_group = SponsorDuplicateGroupFactory()

        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        accommodation_request_one.refresh_from_db()
        accommodation_request_two.refresh_from_db()

        self.assertEqual(
            accommodation_request_one.primary_sponsor, duplicate_group.principal_record
        )
        self.assertEqual(
            accommodation_request_two.primary_sponsor, duplicate_group.principal_record
        )

    def test_constituents_are_removed_as_primary_sponsor_from_relevant_ars(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        accommodation_request_one = MvAccommodationRequestFactory(
            primary_sponsor=sponsor_one,
            sponsor_id=[sponsor_one.pk],
        )

        sponsor_two = MvVolunteerFactory(is_principal=True)
        accommodation_request_two = MvAccommodationRequestFactory(
            primary_sponsor=sponsor_two,
            sponsor_id=[sponsor_two.pk],
        )

        duplicate_group = SponsorDuplicateGroupFactory()

        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        accommodation_request_one.refresh_from_db()
        accommodation_request_two.refresh_from_db()

        self.assertNotEqual(accommodation_request_one.primary_sponsor, sponsor_one)
        self.assertNotEqual(accommodation_request_two.primary_sponsor, sponsor_two)

    def test_deduplication_result_is_set_as_active_host_of_relevant_ars(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        accommodation_request_one = MvAccommodationRequestFactory(
            active_host=sponsor_one,
            sponsor_id=[sponsor_one.pk],
        )

        sponsor_two = MvVolunteerFactory(is_principal=True)
        accommodation_request_two = MvAccommodationRequestFactory(
            active_host=sponsor_two,
            sponsor_id=[sponsor_two.pk],
        )

        duplicate_group = SponsorDuplicateGroupFactory()

        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        accommodation_request_one.refresh_from_db()
        accommodation_request_two.refresh_from_db()

        self.assertEqual(
            accommodation_request_one.active_host, duplicate_group.principal_record
        )
        self.assertEqual(
            accommodation_request_two.active_host, duplicate_group.principal_record
        )

    def test_constituents_are_removed_as_active_host_from_relevant_ars(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        accommodation_request_one = MvAccommodationRequestFactory(
            active_host=sponsor_one,
            sponsor_id=[sponsor_one.pk],
        )

        sponsor_two = MvVolunteerFactory(is_principal=True)
        accommodation_request_two = MvAccommodationRequestFactory(
            active_host=sponsor_two,
            sponsor_id=[sponsor_two.pk],
        )

        duplicate_group = SponsorDuplicateGroupFactory()

        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        accommodation_request_one.refresh_from_db()
        accommodation_request_two.refresh_from_db()

        self.assertNotEqual(accommodation_request_one.active_host, sponsor_one)
        self.assertNotEqual(accommodation_request_two.active_host, sponsor_two)

    def test_dev_checks_from_constituents_are_linked_to_new_principal_sponsor(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        sponsor_one_safeguarding_check = DevCheckV2Factory(
            active=True,
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        sponsor_one_safeguarding_check.sponsor.set([sponsor_one])

        sponsor_two = MvVolunteerFactory(is_principal=True)
        sponsor_two_safeguarding_check = DevCheckV2Factory(
            active=True,
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        sponsor_two_safeguarding_check.sponsor.set([sponsor_two])

        duplicate_group = SponsorDuplicateGroupFactory()

        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        sponsor_one_safeguarding_check.refresh_from_db()
        sponsor_two_safeguarding_check.refresh_from_db()

        self.assertIn(
            duplicate_group.principal_record,
            sponsor_one_safeguarding_check.sponsor.all(),
        )
        self.assertIn(
            duplicate_group.principal_record,
            sponsor_two_safeguarding_check.sponsor.all(),
        )

    def test_dev_checks_from_constituents_remain_linked_to_constituents(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        sponsor_one_safeguarding_check = DevCheckV2Factory(
            active=True,
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        sponsor_one_safeguarding_check.sponsor.set([sponsor_one])

        sponsor_two = MvVolunteerFactory(is_principal=True)
        sponsor_two_safeguarding_check = DevCheckV2Factory(
            active=True,
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        sponsor_two_safeguarding_check.sponsor.set([sponsor_two])

        duplicate_group = SponsorDuplicateGroupFactory()

        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"}, user=get_admin_user()
        )

        sponsor_one_safeguarding_check.refresh_from_db()
        sponsor_two_safeguarding_check.refresh_from_db()

        self.assertIn(
            sponsor_one,
            sponsor_one_safeguarding_check.sponsor.all(),
        )
        self.assertIn(
            sponsor_two,
            sponsor_two_safeguarding_check.sponsor.all(),
        )

    def test_dedupe_with_null_sponsor_id_does_not_crash_and_links_principal(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        sponsor_two = MvVolunteerFactory(is_principal=True)
        ar = MvAccommodationRequestFactory(
            primary_sponsor=sponsor_one,
            sponsor_id=None,
        )

        duplicate_group = SponsorDuplicateGroupFactory()
        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"},
            user=get_admin_user(),
        )

        ar.refresh_from_db()
        self.assertIn(duplicate_group.principal_record.pk, ar.sponsor_id or [])
        self.assertEqual(ar.primary_sponsor, duplicate_group.principal_record)

    def test_dedupe_does_not_duplicate_principal_in_shared_ar_sponsor_id(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        sponsor_two = MvVolunteerFactory(is_principal=True)
        ar = MvAccommodationRequestFactory(
            sponsor_id=[sponsor_one.pk, sponsor_two.pk],
        )

        duplicate_group = SponsorDuplicateGroupFactory()
        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"},
            user=get_admin_user(),
        )

        ar.refresh_from_db()
        principal_pk = duplicate_group.principal_record.pk
        self.assertEqual(ar.sponsor_id.count(principal_pk), 1)
        self.assertNotIn(sponsor_one.pk, ar.sponsor_id)
        self.assertNotIn(sponsor_two.pk, ar.sponsor_id)

    @override_settings(ENHANCED_DEDUPLICATION_LOGGING=True)
    def test_dedupe_emits_started_and_finished_sentry_logs(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        sponsor_two = MvVolunteerFactory(is_principal=True)
        duplicate_group = SponsorDuplicateGroupFactory()
        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        with patch("sentry_sdk.logger.info") as info:
            duplicate_group.deduplicate(
                principal_record_values={"first_name": "bob"},
                user=get_admin_user(),
            )

        messages = [call.args[0] for call in info.call_args_list]
        self.assertIn("SponsorDuplicateGroup.deduplicate: started", messages)
        self.assertIn("SponsorDuplicateGroup.deduplicate: finished", messages)

    def test_dedupe_emits_completed_sentry_metric(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        sponsor_two = MvVolunteerFactory(is_principal=True)
        duplicate_group = SponsorDuplicateGroupFactory()
        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        with patch("sentry_sdk.metrics.count") as count:
            duplicate_group.deduplicate(
                principal_record_values={"first_name": "bob"},
                user=get_admin_user(),
            )

        count.assert_called_once_with(
            "deduplicate.completed",
            1,
            attributes={"record_type": "sponsor"},
        )

    def test_dedupe_emits_failed_sentry_metric_when_raising(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        sponsor_two = MvVolunteerFactory(is_principal=False)
        duplicate_group = SponsorDuplicateGroupFactory()
        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        with patch("sentry_sdk.metrics.count") as count:
            with self.assertRaises(DeduplicationException):
                duplicate_group.deduplicate(
                    principal_record_values={"first_name": "bob"},
                    user=get_admin_user(),
                )

        count.assert_called_once_with(
            "deduplicate.failed",
            1,
            attributes={"record_type": "sponsor"},
        )

    def test_dedupe_recalculates_checks_on_linked_ars_failed_checks(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        sponsor_two = MvVolunteerFactory(is_principal=True)
        ar = MvAccommodationRequestFactory(
            sponsor_id=[sponsor_one.pk, sponsor_two.pk],
        )

        duplicate_group = SponsorDuplicateGroupFactory()
        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        sponsor_dbs_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
        )
        sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.FAILED

        sponsor_dbs_check.sponsor.set([sponsor_one])

        sponsor_dbs_check.save()

        ar.checks_status = ar.determine_checks_status_from_linked_objects()

        self.assertEqual(
            ar.checks_status,
            MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED,
        )

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"},
            user=get_admin_user(),
        )

        ar.refresh_from_db()
        self.assertEqual(
            ar.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

    def test_dedupe_recalculates_checks_on_linked_ars_passed_checks(self):
        sponsor_one = MvVolunteerFactory(is_principal=True)
        sponsor_two = MvVolunteerFactory(is_principal=True)
        ar = MvAccommodationRequestFactory(
            sponsor_id=[sponsor_one.pk, sponsor_two.pk],
        )

        duplicate_group = SponsorDuplicateGroupFactory()
        duplicate_group.sponsors.add(sponsor_one)
        duplicate_group.sponsors.add(sponsor_two)
        duplicate_group.save()

        sponsor_dbs_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
        )
        sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED

        sponsor_dbs_check.sponsor.set([sponsor_one])

        sponsor_dbs_check.save()

        ar.checks_status = ar.determine_checks_status_from_linked_objects()

        self.assertEqual(
            ar.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED,
        )

        duplicate_group.deduplicate(
            principal_record_values={"first_name": "bob"},
            user=get_admin_user(),
        )

        ar.refresh_from_db()
        self.assertEqual(
            ar.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )
