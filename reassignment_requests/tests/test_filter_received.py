from datetime import datetime, timezone

from django.test import TestCase

from ontology.models import ReassignmentRequest
from ontology.tests.factories import ReassignmentRequestFactory
from reassignment_requests.views import ReassignmentRequestsReceivedFilter


class FilterReassignmentRequestsReceivedTestCase(TestCase):
    def setUp(self):
        self.pending = ReassignmentRequestFactory(
            outcome=ReassignmentRequest.Outcome.PENDING,
            source_ltla_name=["Bristol"],
        )
        self.pending.created_at = datetime(2025, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
        self.pending.save()

        self.rejected = ReassignmentRequestFactory(
            outcome=ReassignmentRequest.Outcome.REJECTED,
            source_ltla_name=["Bristol"],
        )
        self.rejected.created_at = datetime(2025, 7, 1, 10, 0, 0, tzinfo=timezone.utc)
        self.rejected.save()

        self.accepted = ReassignmentRequestFactory(
            outcome=ReassignmentRequest.Outcome.ACCEPTED,
            source_ltla_name=["North Somerset"],
        )
        self.accepted.created_at = datetime(2025, 8, 10, 10, 0, 0, tzinfo=timezone.utc)
        self.accepted.save()

    def _check_object_in_results(self, obj, results):
        return str(obj.pk) in [str(r.pk) for r in results]

    def test_default_shows_all(self):
        filter_set = ReassignmentRequestsReceivedFilter(
            queryset=ReassignmentRequest.objects.all(),
            data={},
        )
        results = filter_set.qs
        self.assertEqual(len(results), 3)
        self.assertTrue(self._check_object_in_results(self.pending, results))
        self.assertTrue(self._check_object_in_results(self.rejected, results))
        self.assertTrue(self._check_object_in_results(self.accepted, results))

    def test_filter_by_outcome(self):
        filter_set = ReassignmentRequestsReceivedFilter(
            queryset=ReassignmentRequest.objects.all(),
            data={"outcome": [ReassignmentRequest.Outcome.ACCEPTED]},
        )
        results = filter_set.qs
        self.assertEqual(len(results), 1)
        self.assertTrue(self._check_object_in_results(self.accepted, results))
        self.assertFalse(self._check_object_in_results(self.pending, results))
        self.assertFalse(self._check_object_in_results(self.rejected, results))

    def test_filter_by_multiple_outcomes(self):
        filter_set = ReassignmentRequestsReceivedFilter(
            queryset=ReassignmentRequest.objects.all(),
            data={
                "outcome": [
                    ReassignmentRequest.Outcome.PENDING,
                    ReassignmentRequest.Outcome.REJECTED,
                ],
            },
        )
        results = filter_set.qs
        self.assertEqual(len(results), 2)
        self.assertTrue(self._check_object_in_results(self.pending, results))
        self.assertTrue(self._check_object_in_results(self.rejected, results))
        self.assertFalse(self._check_object_in_results(self.accepted, results))

    def test_filter_by_source_ltla_name(self):
        filter_set = ReassignmentRequestsReceivedFilter(
            queryset=ReassignmentRequest.objects.all(),
            data={"source_ltla_name": "North Somerset"},
        )
        results = filter_set.qs
        self.assertEqual(len(results), 1)
        self.assertTrue(self._check_object_in_results(self.accepted, results))
        self.assertFalse(self._check_object_in_results(self.pending, results))
        self.assertFalse(self._check_object_in_results(self.rejected, results))

    def test_filter_by_created_at_range(self):
        filter_set = ReassignmentRequestsReceivedFilter(
            queryset=ReassignmentRequest.objects.all(),
            data={
                "created_at_0": "2025-08-01",
                "created_at_1": "2025-08-31",
            },
        )
        results = filter_set.qs
        self.assertEqual(len(results), 1)
        self.assertTrue(self._check_object_in_results(self.accepted, results))
        self.assertFalse(self._check_object_in_results(self.pending, results))
        self.assertFalse(self._check_object_in_results(self.rejected, results))
