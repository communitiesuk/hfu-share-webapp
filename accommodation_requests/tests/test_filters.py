from django.test import TestCase

from accommodation_requests.views import AccommodationRequestsFilter
from ontology.models import MvAccommodationRequest as AccReq
from ontology.tests.factories import MvAccommodationRequestFactory as AccReqFactory


class AccommodationRequestFilterTestCase(TestCase):
    def setUp(self):
        self.active_req = AccReqFactory(
            id="accommodation_request-00000",
            title="Active request",
            checks_status=AccReq.ChecksStatus.CHECKS_REQUIRED,
            person_id=["1", "2", "3"],
        )
        self.closed_duplicate = AccReqFactory(
            id="accommodation_request-00001",
            title="Closed duplicate",
            checks_status=AccReq.ChecksStatus.CLOSED_DUPLICATE,
            person_id=["1", "2", "3"],
        )
        self.cancelled = AccReqFactory(
            id="accommodation_request-00002",
            title="Cancelled",
            checks_status=AccReq.ChecksStatus.CANCELLED,
            person_id=["1", "2", "3"],
        )
        self.closed_empty = AccReqFactory(
            id="accommodation_request-00003",
            title="Closed empty",
            checks_status=AccReq.ChecksStatus.CLOSED_EMPTY,
        )
        self.closed_left = AccReqFactory(
            id="accommodation_request-00004",
            title="Closed left",
            checks_status=AccReq.ChecksStatus.CLOSED_LEFT_PROGRAMME,
            person_id=["1", "2", "3"],
        )

    def test_show_inactive_default_shows_all(self):
        filter_set = AccommodationRequestsFilter(
            queryset=AccReq.objects.all(),
            data={},
        )

        results = filter_set.qs
        accomodation_request_ids = results.values_list("id", flat=True)

        self.assertEqual(len(accomodation_request_ids), 4)
        self.assertIn(self.active_req.id, accomodation_request_ids)
        self.assertIn(self.closed_duplicate.id, accomodation_request_ids)
        self.assertIn(self.cancelled.id, accomodation_request_ids)
        self.assertNotIn(self.closed_empty.id, accomodation_request_ids)
        self.assertIn(self.closed_left.id, accomodation_request_ids)

    def test_filter_by_one_checks_status(self):
        filter_set = AccommodationRequestsFilter(
            queryset=AccReq.objects.all(),
            data={"status": [AccReq.ChecksStatus.CLOSED_DUPLICATE]},
        )

        results = filter_set.qs
        accomodation_request_ids = results.values_list("id", flat=True)

        self.assertEqual(len(accomodation_request_ids), 1)
        self.assertNotIn(self.active_req.id, accomodation_request_ids)
        self.assertIn(self.closed_duplicate.id, accomodation_request_ids)
        self.assertNotIn(self.cancelled.id, accomodation_request_ids)
        self.assertNotIn(self.closed_empty.id, accomodation_request_ids)
        self.assertNotIn(self.closed_left.id, accomodation_request_ids)

    def test_filter_by_mulitple_checks_status(self):
        filter_set = AccommodationRequestsFilter(
            queryset=AccReq.objects.all(),
            data={
                "status": [
                    AccReq.ChecksStatus.CLOSED_DUPLICATE,
                    AccReq.ChecksStatus.CLOSED_EMPTY,
                    AccReq.ChecksStatus.CLOSED_LEFT_PROGRAMME,
                ],
            },
        )

        results = filter_set.qs
        accomodation_request_ids = results.values_list("id", flat=True)

        self.assertEqual(len(accomodation_request_ids), 3)
        self.assertNotIn(self.active_req.id, accomodation_request_ids)
        self.assertIn(self.closed_duplicate.id, accomodation_request_ids)
        self.assertNotIn(self.cancelled.id, accomodation_request_ids)
        self.assertIn(self.closed_empty.id, accomodation_request_ids)
        self.assertIn(self.closed_left.id, accomodation_request_ids)

    def test_filter_by_checks_status_closed_empty(self):
        filter_set = AccommodationRequestsFilter(
            queryset=AccReq.objects.all(),
            data={"status": [AccReq.ChecksStatus.CLOSED_EMPTY]},
        )

        results = filter_set.qs
        accomodation_request_ids = results.values_list("id", flat=True)

        self.assertEqual(len(accomodation_request_ids), 1)
        self.assertNotIn(self.active_req.id, accomodation_request_ids)
        self.assertNotIn(self.closed_duplicate.id, accomodation_request_ids)
        self.assertNotIn(self.cancelled.id, accomodation_request_ids)
        self.assertIn(self.closed_empty.id, accomodation_request_ids)
        self.assertNotIn(self.closed_left.id, accomodation_request_ids)
