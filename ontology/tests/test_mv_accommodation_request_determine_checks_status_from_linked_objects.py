from datetime import datetime, timezone

from django.test import TestCase

from ontology.models import (
    CheckType,
    DevCheckV2,
    MvAccommodation,
    MvAccommodationRequest,
    MvGroup,
    MvVolunteer,
)
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvGroupFactory,
    MvPersonFactory,
    MvVolunteerFactory,
)


class MvAccommodationRequestDetermineChecksStatusFromLinkedObjects(TestCase):
    def setUp(self):
        super().setUp()

        self.person = MvPersonFactory()
        self.group = MvGroupFactory()
        self.sponsor = MvVolunteerFactory()
        self.accommodation = MvAccommodationFactory()
        self.accommodation_request = self.person.accommodation_request
        self.accommodation_request.primary_accommodation = self.accommodation
        self.accommodation_request.group = self.group
        self.accommodation_request.sponsor_id = [self.sponsor.id]
        self.accommodation_request.save()

        self.accommodation_suitable_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            AR=[self.accommodation_request],
        )
        self.accommodation_suitable_check.accommodation.set([self.accommodation])
        self.accommodation_exists_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
        )
        self.accommodation_exists_check.accommodation.set([self.accommodation])
        self.sponsor_dbs_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
        )
        self.sponsor_dbs_check.sponsor.set([self.sponsor])
        self.guest_has_arrived_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.GROUP_ARRIVED),
        )
        self.guest_has_arrived_check.group.set([self.group])

    def test_returns_in_temporary_accommodation_if_any_active_accom_on_ar_is_temporary(
        self,
    ):
        temporary_accommodation = MvAccommodationFactory(
            accommodation_type=MvAccommodation.AccommodationType.TEMPORARY_ACCOMMODATION,
        )

        self.accommodation_request.primary_accommodation_id = temporary_accommodation.id
        self.accommodation_request.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.IN_TEMPORARY_ACCOMMODATION
        )

    def test_returns_some_checks_failed_if_all_checks_recorded_and_failed(self):
        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.FAILED
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.FAILED
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.FAILED
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.FAILED
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED)

    def test_returns_some_checks_failed_if_accom_suitable_check_is_failed(self):
        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.FAILED
        self.accommodation_suitable_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED)

    def test_returns_some_checks_failed_if_accom_exists_check_is_failed(self):
        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.FAILED
        self.accommodation_exists_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED)

    def test_returns_some_checks_failed_if_sponsor_dbs_check_is_failed(self):
        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.FAILED
        self.sponsor_dbs_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED)

    def test_returns_some_checks_failed_if_group_arrived_check_is_failed(self):
        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.FAILED
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED)

    def test_returns_checks_required_if_enhanced_dbs_required_and_no_checks_are_passed(
        self,
    ):
        # Enhanced DBS required because AR contains minors & is UAM
        self.accommodation_request.is_uam = True
        self.accommodation_request.min_age = 12
        self.accommodation_request.save()

        self.accommodation_suitable_check.check_status = (
            DevCheckV2.CheckStatus.IN_PROGRESS
        )
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = (
            DevCheckV2.CheckStatus.IN_PROGRESS
        )
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.sponsor_dbs_check.check_subtype = (
            DevCheckV2.SponsorDBSPassedType.ENHANCED_DBS
        )
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED)

    def test_enhanced_dbs_required_missing_but_other_checks_pass_returns_partially_complete(  # noqa: E501
        self,
    ):
        # Enhanced DBS required because AR contains minors & is UAM
        self.accommodation_request.is_uam = True
        self.accommodation_request.min_age = 12
        self.accommodation_request.save()

        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.check_subtype = DevCheckV2.SponsorDBSPassedType.BASIC_DBS
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )

    def test_enhanced_dbs_required_and_basic_dbs_recorded_pre_may_2023_and_other_checks_pass_returns_checks_complete(  # noqa: E501
        self,
    ):
        # Enhanced DBS required because AR contains minors & is UAM
        self.accommodation_request.is_uam = True
        self.accommodation_request.min_age = 12
        self.accommodation_request.save()

        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.check_subtype = DevCheckV2.SponsorDBSPassedType.BASIC_DBS
        self.sponsor_dbs_check.create_at = datetime(2023, 4, 29, tzinfo=timezone.utc)
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED)

    def test_enhanced_dbs_required_and_recorded_post_april_2023_and_other_checks_pass_returns_checks_complete(  # noqa: E501
        self,
    ):
        # Enhanced DBS required because AR contains minors & is UAM
        self.accommodation_request.is_uam = True
        self.accommodation_request.min_age = 12
        self.accommodation_request.save()

        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.check_subtype = (
            DevCheckV2.SponsorDBSPassedType.ENHANCED_DBS
        )
        self.sponsor_dbs_check.create_at = datetime(2023, 5, 1, tzinfo=timezone.utc)
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED)

    def test_enhanced_dbs_required_and_only_basic_dbs_recorded_post_april_2023_returns_checks_partially_complete(  # noqa: E501
        self,
    ):
        # Enhanced DBS required because AR contains minors & is UAM
        self.accommodation_request.is_uam = True
        self.accommodation_request.min_age = 12
        self.accommodation_request.save()

        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.check_subtype = DevCheckV2.SponsorDBSPassedType.BASIC_DBS
        self.sponsor_dbs_check.create_at = datetime(2023, 5, 1, tzinfo=timezone.utc)
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )

    def test_legacy_formatting_of_enhanced_dbs_check_is_accepted(
        self,
    ):
        # Enhanced DBS required because AR contains minors & is UAM
        self.accommodation_request.is_uam = True
        self.accommodation_request.min_age = 12
        self.accommodation_request.save()

        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.check_subtype = "Enhanced"
        self.sponsor_dbs_check.create_at = datetime(2023, 5, 1, tzinfo=timezone.utc)
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED)

    def test_returns_checks_required_if_ar_missing_active_host_and_no_other_checks_passed(  # noqa: E501
        self,
    ):
        self.accommodation_request.sponsor_id = None
        self.accommodation_request.primary_sponsor_id = None
        self.accommodation_request.save()

        self.accommodation_suitable_check.check_status = (
            DevCheckV2.CheckStatus.IN_PROGRESS
        )
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = (
            DevCheckV2.CheckStatus.IN_PROGRESS
        )
        self.accommodation_exists_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED)

    def test_returns_partially_complete_if_ar_missing_active_host_but_some_other_check_passed(  # noqa: E501
        self,
    ):
        self.accommodation_request.sponsor_id = None
        self.accommodation_request.primary_sponsor_id = None
        self.accommodation_request.save()

        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_exists_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )

    def test_returns_checks_required_if_ar_missing_an_active_accommodation_no_other_checks_passed(  # noqa: E501
        self,
    ):
        self.accommodation_request.primary_accommodation = None
        self.accommodation_request.accommodation_id = None
        self.accommodation_request.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED)

    def test_returns_partially_complete_if_ar_missing_an_active_accommodation_but_some_other_check_passed(  # noqa: E501
        self,
    ):
        self.accommodation_request.primary_accommodation = None
        self.accommodation_request.accommodation_id = None
        self.accommodation_request.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )

    def test_returns_all_checks_complete_if_no_checks_are_missing_and_all_recorded_are_passed(  # noqa: E501
        self,
    ):
        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED)

    def test_returns_pre_arrival_complete_if_pre_arrival_checks_complete_and_no_other_checks_complete(  # noqa: E501
        self,
    ):
        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.check_subtype = (
            DevCheckV2.SponsorDBSPassedType.ENHANCED_DBS
        )
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.PRE_ARRIVAL_CHECKS_COMPLETE
        )

    def test_returns_checks_required_if_ar_is_uam_and_uam_pre_arrival_checks_incomplete_and_no_other_checks_complete(  # noqa: E501
        self,
    ):
        self.accommodation_request.is_uam = True
        self.accommodation_request.save()

        self.accommodation_suitable_check.check_status = (
            DevCheckV2.CheckStatus.IN_PROGRESS
        )
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = (
            DevCheckV2.CheckStatus.IN_PROGRESS
        )
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.sponsor_dbs_check.pre_arrival = True
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED)

    def test_returns_partially_complete_if_ar_is_uam_and_uam_pre_arrival_checks_incomplete_but_some_other_check_passed(  # noqa: E501
        self,
    ):
        self.accommodation_request.is_uam = True
        self.accommodation_request.save()

        self.accommodation_suitable_check.check_status = (
            DevCheckV2.CheckStatus.IN_PROGRESS
        )
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.sponsor_dbs_check.pre_arrival = True
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )

    def test_returns_checks_required_if_all_checks_recorded_and_in_progress(self):
        self.accommodation_suitable_check.check_status = (
            DevCheckV2.CheckStatus.IN_PROGRESS
        )
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = (
            DevCheckV2.CheckStatus.IN_PROGRESS
        )
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.sponsor_dbs_check.check_subtype = (
            DevCheckV2.SponsorDBSPassedType.ENHANCED_DBS
        )
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED)

    def test_returns_partially_complete_if_required_accom_suitable_check_incomplete(
        self,
    ):
        self.accommodation_suitable_check.check_status = (
            DevCheckV2.CheckStatus.IN_PROGRESS
        )
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )

    def test_for_multiple_accom_ar_returns_partially_complete_if_single_accom_suitable_check_incomplete(  # noqa: E501
        self,
    ):
        accom2 = MvAccommodationFactory()
        # Setting primary_accommodation to None to simulate multiple accommodations
        self.accommodation_request.primary_accommodation = None
        self.accommodation_request.accommodation_id = [self.accommodation.id, accom2.id]
        self.accommodation_request.save()

        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_suitable_check.accommodation.set(
            [self.accommodation, accom2]
        )
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )

    def test_returns_partially_complete_if_required_accom_exists_check_incomplete(
        self,
    ):
        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = (
            DevCheckV2.CheckStatus.IN_PROGRESS
        )
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )

    def test_for_multiple_accom_ar_returns_partially_complete_if_single_accom_exists_check_incomplete(  # noqa: E501
        self,
    ):
        accom2 = MvAccommodationFactory()
        # Setting primary_accommodation to None to simulate multiple accommodations
        self.accommodation_request.primary_accommodation = None
        self.accommodation_request.accommodation_id = [self.accommodation.id, accom2.id]
        self.accommodation_request.save()

        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_exists_check.accommodation.set([self.accommodation, accom2])
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )

    def test_returns_partially_complete_if_required_sponosr_dbs_check_incomplete(
        self,
    ):
        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )

    def test_for_multiple_sponsor_ar_returns_partially_complete_if_single_sponsor_dbs_check_incomplete(  # noqa: E501
        self,
    ):
        sponsor2 = MvVolunteerFactory()
        self.accommodation_request.sponsor_id.append(sponsor2.id)
        self.accommodation_request.save()

        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )

    def test_single_sponsor_appearing_multiple_times_on_ar(
        self,
    ):
        self.accommodation_request.active_host = self.sponsor
        self.accommodation_request.save()

        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_exists_check.check_subtype = (
            DevCheckV2.SponsorDBSPassedType.ENHANCED_DBS
        )
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED)

    def test_returns_pre_arrival_checks_complete_if_required_guests_arrived_check_incomplete(  # noqa: E501
        self,
    ):
        self.accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = DevCheckV2.CheckStatus.IN_PROGRESS
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.PRE_ARRIVAL_CHECKS_COMPLETE
        )

    def test_handles_legacy_formatting_of_checks_statuses(
        self,
    ):
        self.accommodation_suitable_check.check_status = "Passed"
        self.accommodation_suitable_check.save()

        self.accommodation_exists_check.check_status = "Passed"
        self.accommodation_exists_check.save()

        self.sponsor_dbs_check.check_status = "Passed"
        self.sponsor_dbs_check.save()

        self.guest_has_arrived_check.check_status = "Passed"
        self.guest_has_arrived_check.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED)

    def test_handles_nonexistent_linked_accommodation(self):
        # Intentionally not using the Accommodation factory here so that we can be
        # sure that the accommodation does not exist in the database
        accommodation = MvAccommodation(id=1234)
        self.accommodation_request.primary_accommodation = accommodation
        self.accommodation_request.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED)

    def test_handles_nonexistent_linked_group(self):
        # Intentionally not using the Group factory here so that we can be
        # sure that the group does not exist in the database
        group = MvGroup(id=1234)
        self.accommodation_request.group = group
        self.accommodation_request.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED)

    def test_handles_nonexistent_linked_sponsor(self):
        # Intentionally not using the Volunteer factory here so that we can be
        # sure that the sponsor does not exist in the database
        sponsor = MvVolunteer(id=1234)
        self.accommodation_request.sponsor_id = [sponsor.id]
        self.accommodation_request.save()

        status = (
            self.accommodation_request.determine_checks_status_from_linked_objects()
        )
        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED)

    def test_closed_left_programme_status_stays_unchanged(self):
        accommodation_request = MvAccommodationRequest(
            checks_status=MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME
        )

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME
        )

    def test_closed_duplicate_status_stays_unchanged(self):
        accommodation_request = MvAccommodationRequest(
            checks_status=MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE
        )

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE)

    def test_cancelled_status_stays_unchanged(self):
        accommodation_request = MvAccommodationRequest(
            checks_status=MvAccommodationRequest.ChecksStatus.CANCELLED
        )

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CANCELLED)

    def test_closed_empty_status_stays_unchanged(self):
        accommodation_request = MvAccommodationRequest(
            checks_status=MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY
        )

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY)

    def test_cancelled_status_recalculated_if_no_excluded_statuses(self):
        accommodation_request = MvAccommodationRequest(
            checks_status=MvAccommodationRequest.ChecksStatus.CANCELLED
        )

        status = accommodation_request.determine_checks_status_from_linked_objects(
            excluded_statuses=[]
        )

        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED)

    def test_closed_empty_status_is_updated_if_ar_is_empty_group(self):
        accommodation_request = MvAccommodationRequest(
            title="Empty group Example Title",
            number_of_people=0,
            checks_status=MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED,
        )

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY)

    def test_closed_empty_status_is_updated_if_ar_has_empty_person_id(self):
        accommodation_request = MvAccommodationRequest(
            person_id=[],
            checks_status=MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED,
        )

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY)

    def test_ar_without_closed_empty_in_the_title_updates_check_status_correctly(self):
        accommodation_request = MvAccommodationRequest(
            title="Example Title",
            checks_status=MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED,
        )

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED)


class DetermineChecksStatusFromCurrentSponsorLinkedObjects(TestCase):
    def setUp(self):
        super().setUp()

        self.passed_sponsor = MvVolunteerFactory()
        self.failed_sponsor = MvVolunteerFactory()

        self.passed_sponsor_dbs_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        self.passed_sponsor_dbs_check.sponsor.set([self.passed_sponsor])

        self.failed_sponsor_dbs_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        self.failed_sponsor_dbs_check.sponsor.set([self.failed_sponsor])

    def test_it_takes_active_host_over_primary_sponsor(self):
        accommodation_request = MvAccommodationRequestFactory(
            active_host=self.passed_sponsor,
            primary_sponsor=self.failed_sponsor,
        )

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )

    def test_it_takes_active_host_over_sponsor_id(self):
        accommodation_request = MvAccommodationRequestFactory(
            active_host=self.passed_sponsor,
            sponsor_id=[self.failed_sponsor.id],
        )

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )

    def test_it_takes_primary_sponsor_over_sponsor_id(self):
        accommodation_request = MvAccommodationRequestFactory(
            primary_sponsor=self.failed_sponsor,
            sponsor_id=[self.passed_sponsor.id],
        )

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED)

    def test_it_falls_back_on_sponsor_id(self):
        accommodation_request = MvAccommodationRequestFactory(
            sponsor_id=[self.failed_sponsor.id, self.passed_sponsor.id],
        )

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED)

    def test_it_falls_back_on_sponsor_id_ignoring_withdrwan_sponsor(self):
        accommodation_request = MvAccommodationRequestFactory(
            sponsor_id=[self.failed_sponsor.id, self.passed_sponsor.id],
            sponsor_withdrawn=[self.failed_sponsor.id],
        )

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )


class DetermineChecksStatusFromCurrentAccommodationLinkedObjects(TestCase):
    def setUp(self):
        super().setUp()

        self.passed_accommodation = MvAccommodationFactory()
        self.failed_accommodation = MvAccommodationFactory()

        self.passed_accommodation_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        self.passed_accommodation_check.accommodation.set([self.passed_accommodation])

        self.failed_accommodation_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        self.failed_accommodation_check.accommodation.set([self.failed_accommodation])

    def test_it_takes_primary_accommodation_over_accommodation_id(self):
        accommodation_request = MvAccommodationRequestFactory(
            primary_accommodation=self.passed_accommodation,
            accommodation_id=[self.failed_accommodation.id],
        )

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )

    def test_it_falls_back_on_accommodation_id(self):
        accommodation_request = MvAccommodationRequestFactory(
            accommodation_id=[self.passed_accommodation.id],
        )

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )

    def test_it_falls_back_on_multi_accommodation_id(self):
        accommodation_request = MvAccommodationRequestFactory(
            accommodation_id=[
                self.failed_accommodation.id,
                self.passed_accommodation.id,
            ],
        )

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED)


class DetermineChecksStatusWithLegacyCheckTypesObjects(TestCase):
    def test_it_ignores_all_checks_complete_check_type(self):
        group = MvGroupFactory()
        accommodation_request = MvAccommodationRequestFactory(group=group)
        check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SG_CHECKS_COMPLETE),
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        check.AR.set([accommodation_request.id])
        check.group.set([group.id])

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(status, MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED)

    def test_it_ignores_legacy_sponsor_check_types(self):
        sponsor = MvVolunteerFactory()
        accommodation_request = MvAccommodationRequestFactory(primary_sponsor=sponsor)
        check_that_matters = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        check_that_matters.sponsor.set([sponsor.id])

        check_to_ignore = DevCheckV2Factory(
            check_type=CheckType.objects.get(
                id=CheckType.Id.SPONSOR_ARRANGEMENTS_SUITABLE
            ),
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        check_to_ignore.sponsor.set([sponsor.id])

        check_to_ignore_2 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_ACCEPTS_ROLE),
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        check_to_ignore_2.sponsor.set([sponsor.id])

        status = accommodation_request.determine_checks_status_from_linked_objects()

        self.assertEqual(
            status, MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED
        )
