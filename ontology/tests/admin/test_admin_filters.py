from datetime import datetime, timezone
from typing import cast

from django.contrib.admin import ModelAdmin, SimpleListFilter
from django.db import models
from django.test import RequestFactory, TestCase

from ontology.admin_filters import (
    ARsCreatedOrModifiedSinceShareGoLiveFilter,
    ChecksSinceShareGoLiveFilter,
    GuestsWithMismatchedARFilter,
)
from ontology.models import CheckType, MvAccommodationRequest, MvPerson
from ontology.models.DevCheckV2 import DevCheckV2
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
)


class FilterTest(TestCase):
    filter_cls: type[SimpleListFilter]
    filter_param: str
    model: type[models.Model]
    request = RequestFactory().get("/")

    @classmethod
    def get_filtered_queryset(cls, filter_param: str):
        # Create filter instance
        filter_instance = cls.filter_cls(
            request=cls.request,
            params={},
            model=cls.model,
            model_admin=cast(ModelAdmin, None),
        )

        filter_instance.used_parameters = {cls.filter_param: filter_param}

        # Apply filter
        return filter_instance.queryset(
            request=cls.request, queryset=cls.model.objects.all()
        )


class ChecksSinceShareGoLiveFilterTest(FilterTest):
    filter_cls = ChecksSinceShareGoLiveFilter
    filter_param = "since_share_go_live"
    model = DevCheckV2

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
        filtered_queryset = self.get_filtered_queryset("sponsors")

        # Should return only non-principal sponsor checks after go-live
        self.assertEqual(filtered_queryset.count(), 1)

        ids = [f.id for f in filtered_queryset.all()]
        self.assertIn(str(self.devcheck_1.id), ids)

    def test_accommodation_checks_since_share_go_live_filter(self):
        filtered_queryset = self.get_filtered_queryset("accommodations")

        # Should return only non-principal sponsor checks after go-live
        self.assertEqual(filtered_queryset.count(), 2)

        ids = [f.id for f in filtered_queryset.all()]
        self.assertIn(str(self.devcheck_4.id), ids)
        self.assertIn(str(self.devcheck_7.id), ids)


class ARsCreatedOrModifiedSinceShareGoLiveFilterTest(FilterTest):
    filter_cls = ARsCreatedOrModifiedSinceShareGoLiveFilter
    filter_param = "created_or_modified_ars_since_share_go_live"
    model = MvAccommodationRequest

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
        filtered_queryset = self.get_filtered_queryset(
            "created_or_modified_ars_since_share_go_live"
        )

        # Should return only non-principal sponsor checks after go-live
        self.assertEqual(filtered_queryset.count(), 3)

        ids = [f.id for f in filtered_queryset.all()]
        self.assertIn(str(self.ar_created_after_go_live.id), ids)
        self.assertIn(str(self.ar_modified_after_go_live.id), ids)
        self.assertIn(str(self.ar_created_before_go_live_modified_after.id), ids)


class GuestsWithMismatchedARFilterTest(FilterTest):
    filter_cls = GuestsWithMismatchedARFilter
    filter_param = "mismatched_ar"
    model = MvPerson

    def setUp(self):
        self.guest_1 = MvPersonFactory()
        self.guest_2 = MvPersonFactory()
        self.guest_3 = MvPersonFactory()
        self.guest_4 = MvPersonFactory()
        self.guest_5 = MvPersonFactory()
        self.ar_1 = MvAccommodationRequestFactory(person_id=[self.guest_1.id])
        self.ar_2 = MvAccommodationRequestFactory(person_id=[self.guest_2.id])
        self.ar_3 = MvAccommodationRequestFactory(person_id=[self.guest_3.id])
        self.ar_4 = MvAccommodationRequestFactory(person_id=[self.guest_5.id])
        self.ar_5 = MvAccommodationRequestFactory()
        self.guest_1.accommodation_request_id = self.ar_1.id
        self.guest_2.accommodation_request_id = None
        self.guest_3.accommodation_request_id = self.ar_4.id
        self.guest_4.accommodation_request_id = self.ar_5.id
        self.guest_5.accommodation_request_id = self.ar_4.id

        self.guest_1.save()
        self.guest_2.save()
        self.guest_3.save()
        self.guest_4.save()
        self.guest_5.save()

    def test_filter_returns_person_with_incorrect_ar_excluding_nulls(self):
        filtered_queryset = self.get_filtered_queryset("exclude_nulls")

        self.assertEqual(filtered_queryset.count(), 2)

        ids = [f.id for f in filtered_queryset.all()]
        self.assertNotIn(self.guest_1.id, ids)
        self.assertNotIn(self.guest_2.id, ids)
        self.assertIn(self.guest_3.id, ids)
        self.assertIn(self.guest_4.id, ids)
        self.assertNotIn(self.guest_5.id, ids)

    def test_filter_returns_person_with_incorrect_ar_including_nulls(self):
        filtered_queryset = self.get_filtered_queryset("include_nulls")

        self.assertEqual(filtered_queryset.count(), 3)

        ids = [f.id for f in filtered_queryset.all()]
        self.assertNotIn(self.guest_1.id, ids)
        self.assertIn(self.guest_2.id, ids)
        self.assertIn(self.guest_3.id, ids)
        self.assertIn(self.guest_4.id, ids)
        self.assertNotIn(self.guest_5.id, ids)

    def test_filter_returns_none_for_unexpected_filter_param(self):
        filtered_queryset = self.get_filtered_queryset("include_nothing")

        self.assertIsNone(filtered_queryset)
