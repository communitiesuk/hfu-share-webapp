from datetime import datetime, timezone

from ontology.admin_filters import (
    ARsCreatedOrModifiedSinceShareGoLiveFilter,
    ChecksSinceShareGoLiveFilter,
    LtlaNameIsNullArrayFilter,
    UtlaNameIsNullArrayFilter,
)
from ontology.models import CheckType, MvAccommodationRequest
from ontology.models.DevCheckV2 import DevCheckV2
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvVolunteerFactory,
)
from test_utils.base import BaseTestCase


class ChecksSinceShareGoLiveFilterTest(BaseTestCase):
    def setUp(self):
        self.sponsor_1 = MvVolunteerFactory(is_principal=False)
        self.sponsor_2 = MvVolunteerFactory(is_principal=False)
        self.sponsor_3 = MvVolunteerFactory(is_principal=True)
        self.devcheck_1 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            create_at="2025-10-01T12:00:00Z",
        )  # after go live
        self.devcheck_1.sponsor.add(self.sponsor_1)
        self.devcheck_2 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            create_at="2025-08-01T12:00:00Z",
        )  # before go live
        self.devcheck_2.sponsor.add(self.sponsor_2)
        self.devcheck_3 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            create_at="2025-11-01T12:00:00Z",
        )  # after go live
        self.devcheck_3.sponsor.add(self.sponsor_3)

        self.accommodation_1 = MvAccommodationFactory(
            full_address="", is_principal=False
        )
        self.accommodation_2 = MvAccommodationFactory(
            full_address="", is_principal=False
        )
        self.accommodation_3 = MvAccommodationFactory(
            full_address="", is_principal=True
        )

        self.devcheck_4 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            create_at="2025-10-01T12:00:00Z",
        )  # after go live
        self.devcheck_4.accommodation.add(self.accommodation_1)
        self.devcheck_5 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            create_at="2025-08-01T12:00:00Z",
        )  # before go live
        self.devcheck_5.accommodation.add(self.accommodation_2)
        self.devcheck_6 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            create_at="2025-11-01T12:00:00Z",
        )  # after go live
        self.devcheck_6.accommodation.add(self.accommodation_3)

        self.devcheck_7 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            create_at="2025-10-01T12:00:00Z",
        )  # after go live
        self.devcheck_7.accommodation.add(self.accommodation_1)
        self.devcheck_8 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            create_at="2025-08-01T12:00:00Z",
        )  # before go live
        self.devcheck_8.accommodation.add(self.accommodation_2)
        self.devcheck_9 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            create_at="2025-11-01T12:00:00Z",
        )  # after go live
        self.devcheck_9.accommodation.add(self.accommodation_3)

    def test_sponsor_checks_since_share_go_live_filter(self):
        # Create filter instance
        filter_instance = ChecksSinceShareGoLiveFilter(
            request=None,
            params={},
            model=DevCheckV2,
            model_admin=None,
        )

        filter_instance.used_parameters = {"since_share_go_live": "sponsors"}

        # Apply filter
        filtered_queryset = filter_instance.queryset(
            request=None, queryset=DevCheckV2.objects.all()
        )

        # Should return only non-principal sponsor checks after go-live
        self.assertEqual(filtered_queryset.count(), 1)

        ids = [f.id for f in filtered_queryset.all()]
        self.assertIn(str(self.devcheck_1.id), ids)

    def test_accommodation_checks_since_share_go_live_filter(self):
        # Create filter instance
        filter_instance = ChecksSinceShareGoLiveFilter(
            request=None,
            params={},
            model=DevCheckV2,
            model_admin=None,
        )

        filter_instance.used_parameters = {"since_share_go_live": "accommodations"}

        # Apply filter
        filtered_queryset = filter_instance.queryset(
            request=None, queryset=DevCheckV2.objects.all()
        )

        # Should return only non-principal sponsor checks after go-live
        self.assertEqual(filtered_queryset.count(), 2)

        ids = [f.id for f in filtered_queryset.all()]
        self.assertIn(str(self.devcheck_4.id), ids)
        self.assertIn(str(self.devcheck_7.id), ids)


class ARsCreatedOrModifiedSinceShareGoLiveFilterTest(BaseTestCase):
    def setUp(self):
        self.ar_created_before_go_live = MvAccommodationRequestFactory(
            created_at=datetime(2025, 9, 14, 23, 59, 59, tzinfo=timezone.utc)
        )
        self.ar_modified_before_go_live = MvAccommodationRequestFactory(
            last_modified_at=datetime(2025, 9, 12, 23, 59, 59, tzinfo=timezone.utc)
        )
        self.ar_created_after_go_live = MvAccommodationRequestFactory(
            created_at=datetime(2025, 9, 15, 23, 59, 59, tzinfo=timezone.utc)
        )
        self.ar_modified_after_go_live = MvAccommodationRequestFactory(
            last_modified_at=datetime(2025, 9, 23, 23, 59, 59, tzinfo=timezone.utc)
        )
        self.ar_created_before_go_live_modified_after = MvAccommodationRequestFactory(
            created_at=datetime(2025, 9, 14, 23, 59, 59, tzinfo=timezone.utc),
            last_modified_at=datetime(2025, 9, 23, 23, 59, 59, tzinfo=timezone.utc),
        )

    def test_it_filters_out_for_ars_created_or_modified_since_go_live(self):
        filter_instance = ARsCreatedOrModifiedSinceShareGoLiveFilter(
            request=None,
            params={},
            model=MvAccommodationRequest,
            model_admin=None,
        )

        filter_instance.used_parameters = {
            "created_or_modified_ars_since_share_go_live": (
                "created_or_modified_ars_since_share_go_live"
            )
        }

        # Apply filter
        filtered_queryset = filter_instance.queryset(
            request=None, queryset=MvAccommodationRequest.objects.all()
        )

        # Should return only non-principal sponsor checks after go-live
        self.assertEqual(filtered_queryset.count(), 3)

        ids = [f.id for f in filtered_queryset.all()]
        self.assertIn(str(self.ar_created_after_go_live.id), ids)
        self.assertIn(str(self.ar_modified_after_go_live.id), ids)
        self.assertIn(str(self.ar_created_before_go_live_modified_after.id), ids)


class LtlaNameIsNullArrayFilterTest(BaseTestCase):
    def setUp(self):
        self.ar_with_null_ltla = MvAccommodationRequestFactory(ltla_name=[None])
        self.ar_with_empty_ltla = MvAccommodationRequestFactory(ltla_name=[])
        self.ar_with_valid_ltla = MvAccommodationRequestFactory(ltla_name=["Cardiff"])
        self.ar_with_null_ltla_field = MvAccommodationRequestFactory(ltla_name=None)

    def test_it_filters_for_ars_with_null_array_ltla_name(self):
        filter_instance = LtlaNameIsNullArrayFilter(
            request=None,
            params={},
            model=MvAccommodationRequest,
            model_admin=None,
        )

        filter_instance.used_parameters = {"ltla_name_is_null_array": "yes"}

        filtered_queryset = filter_instance.queryset(
            request=None, queryset=MvAccommodationRequest.objects.all()
        )

        self.assertEqual(filtered_queryset.count(), 1)
        ids = [f.id for f in filtered_queryset.all()]
        self.assertIn(str(self.ar_with_null_ltla.id), ids)

    def test_it_does_not_filter_when_no_value_selected(self):
        filter_instance = LtlaNameIsNullArrayFilter(
            request=None,
            params={},
            model=MvAccommodationRequest,
            model_admin=None,
        )

        filter_instance.used_parameters = {}

        filtered_queryset = filter_instance.queryset(
            request=None, queryset=MvAccommodationRequest.objects.all()
        )

        self.assertIsNone(filtered_queryset)


class UtlaNameIsNullArrayFilterTest(BaseTestCase):
    def setUp(self):
        self.ar_with_null_utla = MvAccommodationRequestFactory(utla_name=[None])
        self.ar_with_empty_utla = MvAccommodationRequestFactory(utla_name=[])
        self.ar_with_valid_utla = MvAccommodationRequestFactory(utla_name=["Cardiff"])
        self.ar_with_null_utla_field = MvAccommodationRequestFactory(utla_name=None)

    def test_it_filters_for_ars_with_null_array_utla_name(self):
        filter_instance = UtlaNameIsNullArrayFilter(
            request=None,
            params={},
            model=MvAccommodationRequest,
            model_admin=None,
        )

        filter_instance.used_parameters = {"utla_name_is_null_array": "yes"}

        filtered_queryset = filter_instance.queryset(
            request=None, queryset=MvAccommodationRequest.objects.all()
        )

        self.assertEqual(filtered_queryset.count(), 1)
        ids = [f.id for f in filtered_queryset.all()]
        self.assertIn(str(self.ar_with_null_utla.id), ids)
