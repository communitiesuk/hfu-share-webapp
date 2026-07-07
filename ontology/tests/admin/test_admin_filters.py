from datetime import datetime, timezone

from django.test import TestCase

from ontology.admin_filters import (
    ARsCreatedOrModifiedSinceShareGoLiveFilter,
    ChecksSinceShareGoLiveFilter,
)
from ontology.models import CheckType, MvAccommodationRequest
from ontology.models.DevCheckV2 import DevCheckV2
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvVolunteerFactory,
)


class ChecksSinceShareGoLiveFilterTest(TestCase):
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


class ARsCreatedOrModifiedSinceShareGoLiveFilterTest(TestCase):
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
