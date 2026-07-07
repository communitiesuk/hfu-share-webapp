import http.client

from django.urls import reverse

from accounts.enums import GroupType
from ontology.models import ReassignmentRequest
from ontology.tests.factories import ReassignmentRequestFactory
from reassignment_requests.tests.base import ReassignmentRequestsBaseTestCase
from user_management.tests.base import (
    UserGroup,
    get_da_user,
    get_la_user,
    get_user_with_groups,
)


class ReassignmentRequestsMadePageViewTestCase(ReassignmentRequestsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("reassignment-requests:made")

    def test_la_user_is_granted_access(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_granted_access(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.client.OK)

    def test_page_content_is_correct(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(self.url)

        # Check for section heading
        self.assertContains(response, "Requests made")

        # Check for table headers
        self.assertContains(response, "Name")
        self.assertContains(response, "Date of request")
        self.assertContains(response, "Moving to")
        self.assertContains(response, "Status")

    def test_empty_tables_show_correct_messages(self):
        not_somerset_user = get_user_with_groups(
            [UserGroup(name="not_ltla_somerset", type=GroupType.LOCAL_AUTHORITY)]
        )

        self.client.force_login(not_somerset_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You have no requests")

    def test_user_can_only_see_requests_they_made(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        # Check that the context contains the three tables
        self.assertIn("table", response.context)
        table = response.context["table"]

        # Check requests table
        requests = list(table.data)
        request_ids = [request.id for request in requests]

        self.assertIn(str(self.pending_request_somerset_source.id), request_ids)
        self.assertIn(
            str(self.pending_request_somerset_source_multiple_guests.id), request_ids
        )
        self.assertIn(
            str(self.pending_request_somerset_source_single_guest.id), request_ids
        )
        self.assertIn(str(self.rejected_request_somerset_source.id), request_ids)
        self.assertIn(str(self.accepted_request_somerset_source.id), request_ids)

    def test_user_cannot_see_other_la_requests_or_if_they_are_destination(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(self.url)

        # Get all data from all tables
        table = response.context["table"]
        all_visible_requests = [item.id for item in table.data]

        # Verify that requests from other LAs are not visible
        self.assertNotIn(str(self.request_other_la.id), all_visible_requests)

        # The request TO Somerset should not be visible in the "made" view
        self.assertNotIn(str(self.request_to_somerset.id), all_visible_requests)


class ReassignmentRequestsReceivedPageViewTestCase(ReassignmentRequestsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("reassignment-requests:received")

    def test_la_user_is_granted_access(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_granted_access(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.client.OK)

    def test_page_content_is_correct(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(self.url)

        # Check for section headings
        self.assertContains(response, "Requests received")

        # Check for table headers
        self.assertContains(response, "Name")
        self.assertContains(response, "Date of request")
        self.assertContains(response, "Moving from")
        self.assertContains(response, "Status")

    def test_empty_tables_show_correct_messages(self):
        not_somerset_user = get_user_with_groups(
            [UserGroup(name="not_ltla_somerset", type=GroupType.LOCAL_AUTHORITY)]
        )

        self.client.force_login(not_somerset_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You have no requests")

    def test_user_can_only_see_requests_they_received(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        # Check that the context contains the three tables
        self.assertIn("table", response.context)
        table = response.context["table"]
        requests = list(table.data)
        request_ids = [request.id for request in requests]

        self.assertIn(str(self.request_to_somerset.id), request_ids)

    def test_user_cannot_see_requests_they_made_or_from_other_las(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(self.url)

        # Get all data from all tables
        table = response.context["table"]
        all_visible_requests = [item.id for item in table.data]

        # Verify that requests FROM Somerset are not visible in the "received" view
        self.assertNotIn(
            str(self.pending_request_somerset_source.id), all_visible_requests
        )
        self.assertNotIn(
            str(self.rejected_request_somerset_source.id), all_visible_requests
        )
        self.assertNotIn(
            str(self.accepted_request_somerset_source.id), all_visible_requests
        )

        # Verify that requests from other LAs are not visible
        self.assertNotIn(str(self.request_other_la.id), all_visible_requests)

        # The request TO Somerset should be visible in the "received" view
        self.assertIn(str(self.request_to_somerset.id), all_visible_requests)

    def test_requests_with_none_value_source_ltla_names_do_not_cause_exceptions(self):
        user = get_la_user()
        self.client.force_login(user)

        self.pending_request_no_source_ltla_name = ReassignmentRequestFactory(
            source_ltla_name=[None],
            source_utla_name=["utla_somerset"],
            destination_ltla_name="ltla_destination",
            destination_utla_name="utla_destination",
            outcome=ReassignmentRequest.Outcome.PENDING,
            reason="Example reason",
        )

        self.client.get(self.url)
