from datetime import datetime

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import ReassignmentRequest
from ontology.tests.base import LocalAuthorityBaseTestCaseMixin
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvPersonFactory,
    ReassignmentRequestFactory,
)
from test_utils.base import BaseTestCase


class ReassignmentRequestsBaseTestCase(
    TestSessionTokenMixin, LocalAuthorityBaseTestCaseMixin, BaseTestCase
):
    def setUp(self):
        super().setUp()

        # Create reassignment requests with different outcomes for Test LA
        self.pending_request_test_source = ReassignmentRequestFactory(
            source_ltla_name=["ltla_test"],
            source_utla_name=["utla_test"],
            destination_ltla_name="ltla_destination",
            destination_utla_name="utla_destination",
            outcome=ReassignmentRequest.Outcome.PENDING,
        )

        self.rejected_request_test_source = ReassignmentRequestFactory(
            source_ltla_name=["ltla_test"],
            source_utla_name=["utla_test"],
            destination_ltla_name="ltla_destination",
            destination_utla_name="utla_destination",
            outcome=ReassignmentRequest.Outcome.REJECTED,
        )

        self.accepted_request_test_source = ReassignmentRequestFactory(
            source_ltla_name=["ltla_test"],
            source_utla_name=["utla_test"],
            destination_ltla_name="ltla_destination",
            destination_utla_name="utla_destination",
            outcome=ReassignmentRequest.Outcome.ACCEPTED,
        )

        self.needs_ar_request_test_source = ReassignmentRequestFactory(
            source_ltla_name=["ltla_test"],
            source_utla_name=["utla_test"],
            destination_ltla_name="ltla_destination",
            destination_utla_name="utla_destination",
            outcome=ReassignmentRequest.Outcome.NEEDS_ACCOMMODATION_REQUEST,
        )

        # Create requests where Test is the destination (should NOT be visible)
        self.request_to_test = ReassignmentRequestFactory(
            source_ltla_name=["ltla_other"],
            source_utla_name=["utla_other"],
            destination_ltla_name="ltla_test",
            destination_utla_name="utla_test",
            created_at=datetime(2025, 12, 12, 12, 12, 10),
            reason="Example reason",
            outcome=ReassignmentRequest.Outcome.PENDING,
        )

        # Create requests from other LAs (should NOT be visible to Test user)
        self.request_other_la = ReassignmentRequestFactory(
            source_ltla_name=["ltla_other"],
            source_utla_name=["utla_other"],
            destination_ltla_name="ltla_another",
            destination_utla_name="utla_another",
            outcome=ReassignmentRequest.Outcome.PENDING,
        )

        self.da_request = ReassignmentRequestFactory(
            source_ltla_name=["Aberdeenshire"],
            source_utla_name=["Abserdeenshire"],
            destination_ltla_name="ltla_another",
            destination_utla_name="utla_another",
            outcome=ReassignmentRequest.Outcome.PENDING,
        )

        self.pending_request_test_source_single_guest = ReassignmentRequestFactory(
            source_ltla_name=["ltla_test"],
            source_utla_name=["utla_test"],
            destination_ltla_name="ltla_destination",
            destination_utla_name="utla_destination",
            outcome=ReassignmentRequest.Outcome.PENDING,
            reason="Example reason",
        )

        self.pending_request_test_source_multiple_guests = ReassignmentRequestFactory(
            source_ltla_name=["ltla_test"],
            source_utla_name=["utla_test"],
            destination_ltla_name="ltla_destination",
            destination_utla_name="utla_destination",
            outcome=ReassignmentRequest.Outcome.PENDING,
            reason="Example reason",
        )
        self.pending_request_test_source_multiple_guests_ar = (
            MvAccommodationRequestFactory()
        )
        self.pending_request_test_source_multiple_guests.accommodation_request = (
            self.pending_request_test_source_multiple_guests_ar
        )
        self.pending_request_test_source_multiple_guests.save()

        self.guest_a = MvPersonFactory(
            first_name="Guest",
            last_name="A",
        )
        self.guest_b = MvPersonFactory(
            first_name="Guest",
            last_name="B",
        )
        self.guest_c = MvPersonFactory(
            first_name="Guest",
            last_name="C",
        )
        self.pending_request_test_source_single_guest.guests.set([self.guest_a])
        self.pending_request_test_source_multiple_guests.guests.set(
            [self.guest_a, self.guest_b]
        )

        self.pending_request_edinburgh_source = ReassignmentRequestFactory(
            source_ltla_name=["City of Edinburgh"],
            outcome=ReassignmentRequest.Outcome.PENDING,
            reason="Example reason",
        )

        self.pending_request_multi_la_source = ReassignmentRequestFactory(
            source_ltla_name=["Lewisham", "Bromley"],
            source_utla_name=["Lewisham", "Bromley"],
            destination_ltla_name="ltla_destination",
            destination_utla_name="utla_destination",
            outcome=ReassignmentRequest.Outcome.PENDING,
            reason="Example reason",
        )

        self.pending_request_multi_la_source.guests.set([self.guest_a])

        # Requests that should be visible to Test LA
        self.test_requests = [
            self.pending_request_test_source,
            self.pending_request_test_source_single_guest,
            self.pending_request_test_source_multiple_guests,
            self.rejected_request_test_source,
            self.accepted_request_test_source,
            self.needs_ar_request_test_source,
        ]

        # All requests
        self.all_requests = [
            self.pending_request_test_source,
            self.rejected_request_test_source,
            self.accepted_request_test_source,
            self.request_to_test,
            self.request_other_la,
            self.needs_ar_request_test_source,
            self.pending_request_edinburgh_source,
            self.pending_request_multi_la_source,
        ]
