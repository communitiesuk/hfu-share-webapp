from unittest import mock

from django.urls import reverse

from accounts.enums import GroupType
from accounts.tests.factories import GroupInfoFactory
from ontology.models.MvAccommodationRequest import MvAccommodationRequest
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvVolunteerFactory,
)
from reassignment_requests.tests.base import ReassignmentRequestsBaseTestCase
from user_management.tests.base import UserGroup, get_user_with_groups


def _find_log_calls(mock_calls, message):
    return [c for c in mock_calls if c.args[0] == message]


class AcceptReassignmentLoggingTestCase(ReassignmentRequestsBaseTestCase):
    def setUp(self):
        super().setUp()
        GroupInfoFactory(
            ltla_name="ltla_destination",
            utla_name="utla_destination",
            gss_code="E000",
            utla_gss_code="E001",
        )
        self.user = get_user_with_groups(
            [UserGroup(name="ltla_destination", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(self.user)

        acc = MvAccommodationFactory()
        self.ar = MvAccommodationRequestFactory(
            number_of_people=2,
            person_id=[self.guest_a.id, self.guest_b.id],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            accommodation_id=[acc.id],
            primary_accommodation=acc,
            active_host=MvVolunteerFactory(),
        )
        self.request = self.pending_request_somerset_source_multiple_guests
        self.request.accommodation_request = self.ar
        self.request.save()
        self.url = reverse(
            "reassignment-requests:detail-received", kwargs={"pk": self.request.pk}
        )

    @mock.patch("reassignment_requests.views.log_persistence_check")
    @mock.patch("reassignment_requests.views.log_event")
    def test_started_event_is_logged(self, mock_log_event, _mock_log_pc):
        self.client.post(self.url, {"action": "accept", "comments": "ok"}, follow=True)

        calls = _find_log_calls(
            mock_log_event.call_args_list, "accept_reassignment_request: started"
        )
        self.assertEqual(len(calls), 1)
        kwargs = calls[0].kwargs
        self.assertEqual(kwargs["reassignment_request_pk"], str(self.request.pk))
        self.assertEqual(kwargs["ar_pk"], str(self.ar.pk))

    @mock.patch("reassignment_requests.views.log_persistence_check")
    @mock.patch("reassignment_requests.views.log_event")
    def test_ar_updated_persistence_check_is_logged(self, _mock_log_event, mock_log_pc):
        self.client.post(self.url, {"action": "accept", "comments": "ok"}, follow=True)
        self.ar.refresh_from_db()

        calls = _find_log_calls(
            mock_log_pc.call_args_list, "accept_reassignment_request: AR updated"
        )
        self.assertEqual(len(calls), 1)
        changes = calls[0].kwargs["changes"]
        self.assertEqual(changes["ltla_name"], (self.ar.ltla_name, self.ar.ltla_name))
        self.assertEqual(changes["utla_name"], (self.ar.utla_name, self.ar.utla_name))
        self.assertEqual(
            changes["checks_status"], (self.ar.checks_status, self.ar.checks_status)
        )
        self.assertEqual(changes["person_id"], (self.ar.person_id, self.ar.person_id))
        self.assertEqual(changes["edited_in_app"], (True, True))

    @mock.patch("reassignment_requests.views.log_persistence_check")
    @mock.patch("reassignment_requests.views.log_event")
    def test_guest_ar_links_event_is_logged(self, mock_log_event, _mock_log_pc):
        self.client.post(self.url, {"action": "accept", "comments": "ok"}, follow=True)

        calls = _find_log_calls(
            mock_log_event.call_args_list,
            "accept_reassignment_request: guest AR links",
        )
        self.assertEqual(len(calls), 1)
        kwargs = calls[0].kwargs
        self.assertEqual(kwargs["ar_pk"], str(self.ar.pk))
        self.assertCountEqual(
            [link["id"] for link in kwargs["guest_ar_links"]],
            [self.guest_a.pk, self.guest_b.pk],
        )

    @mock.patch("reassignment_requests.views.log_persistence_check")
    @mock.patch("reassignment_requests.views.log_event")
    def test_accommodation_unlinked_persistence_check_is_logged(
        self, _mock_log_event, mock_log_pc
    ):
        self.client.post(self.url, {"action": "accept", "comments": "ok"}, follow=True)
        self.ar.refresh_from_db()

        calls = _find_log_calls(
            mock_log_pc.call_args_list,
            "accept_reassignment_request: accommodation unlinked",
        )
        self.assertEqual(len(calls), 1)
        changes = calls[0].kwargs["changes"]
        self.assertEqual(
            changes["accommodation_id"],
            (self.ar.accommodation_id, self.ar.accommodation_id),
        )
        self.assertEqual(
            changes["primary_accommodation_id"],
            (self.ar.primary_accommodation_id, self.ar.primary_accommodation_id),
        )
        self.assertEqual(changes["postcode"], (self.ar.postcode, self.ar.postcode))
        self.assertEqual(changes["edited_in_app"], (True, True))

    @mock.patch("reassignment_requests.views.log_persistence_check")
    @mock.patch("reassignment_requests.views.log_event")
    def test_host_unlinked_persistence_check_is_logged(
        self, _mock_log_event, mock_log_pc
    ):
        self.client.post(self.url, {"action": "accept", "comments": "ok"}, follow=True)

        calls = _find_log_calls(
            mock_log_pc.call_args_list, "accept_reassignment_request: host unlinked"
        )
        self.assertEqual(len(calls), 1)
        changes = calls[0].kwargs["changes"]
        self.assertEqual(changes["active_host_id"], (None, None))
        self.assertEqual(changes["active_eoi_host_id"], (None, None))
        self.assertEqual(changes["edited_in_app"], (True, True))

    @mock.patch("reassignment_requests.views.log_persistence_check")
    @mock.patch("reassignment_requests.views.log_event")
    def test_interaction_created_event_is_logged(self, mock_log_event, _mock_log_pc):
        self.client.post(self.url, {"action": "accept", "comments": "ok"}, follow=True)

        calls = _find_log_calls(
            mock_log_event.call_args_list,
            "accept_reassignment_request: interaction created",
        )
        self.assertEqual(len(calls), 1)
        kwargs = calls[0].kwargs
        self.assertIsNotNone(kwargs["interaction_pk"])
        self.assertEqual(kwargs["interaction_type"], "Reassignment accepted")

    @mock.patch("reassignment_requests.views.log_persistence_check")
    @mock.patch("reassignment_requests.views.log_event")
    def test_outcome_set_persistence_check_is_logged(
        self, _mock_log_event, mock_log_pc
    ):
        self.client.post(self.url, {"action": "accept", "comments": "ok"}, follow=True)
        self.request.refresh_from_db()

        calls = _find_log_calls(
            mock_log_pc.call_args_list, "accept_reassignment_request: outcome set"
        )
        self.assertEqual(len(calls), 1)
        changes = calls[0].kwargs["changes"]
        self.assertEqual(
            changes["outcome"],
            (self.request.outcome, self.request.outcome),
        )
        self.assertEqual(
            changes["responded_at"],
            (self.request.responded_at, self.request.responded_at),
        )


class AcceptPartialReassignmentLoggingTestCase(ReassignmentRequestsBaseTestCase):
    def setUp(self):
        super().setUp()
        GroupInfoFactory(
            ltla_name="ltla_destination",
            utla_name="utla_destination",
            gss_code="E000",
            utla_gss_code="E001",
        )
        self.user = get_user_with_groups(
            [UserGroup(name="ltla_destination", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(self.user)

        acc = MvAccommodationFactory()
        self.ar = MvAccommodationRequestFactory(
            number_of_people=3,
            person_id=[self.guest_a.id, self.guest_b.id, self.guest_c.id],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            accommodation_id=[acc.id],
            primary_accommodation=acc,
            active_host=MvVolunteerFactory(),
        )
        # RR only covers guest_a and guest_b (partial - guest_c stays)
        self.request = self.pending_request_somerset_source_multiple_guests
        self.request.accommodation_request = self.ar
        self.request.save()
        self.url = reverse(
            "reassignment-requests:detail-received", kwargs={"pk": self.request.pk}
        )

    @mock.patch("reassignment_requests.views.log_persistence_check")
    @mock.patch("reassignment_requests.views.log_event")
    def test_guests_split_event_is_logged(self, mock_log_event, _mock_log_pc):
        self.client.post(self.url, {"action": "accept", "comments": "ok"}, follow=True)
        self.guest_a.refresh_from_db()

        calls = _find_log_calls(
            mock_log_event.call_args_list,
            "accept_reassignment_request: guests split to new AR",
        )
        self.assertEqual(len(calls), 1)
        kwargs = calls[0].kwargs
        self.assertEqual(kwargs["original_ar_pk"], str(self.ar.pk))
        self.assertEqual(
            str(kwargs["new_ar_pk"]), str(self.guest_a.accommodation_request_id)
        )

    @mock.patch("reassignment_requests.views.log_persistence_check")
    @mock.patch("reassignment_requests.views.log_event")
    def test_partial_split_interaction_event_is_logged(
        self, mock_log_event, _mock_log_pc
    ):
        self.client.post(self.url, {"action": "accept", "comments": "ok"}, follow=True)

        calls = _find_log_calls(
            mock_log_event.call_args_list,
            "accept_reassignment_request: partial split interaction created",
        )
        self.assertEqual(len(calls), 1)
        kwargs = calls[0].kwargs
        self.assertEqual(kwargs["original_ar_pk"], str(self.ar.pk))
        self.assertIsNotNone(kwargs["interaction_pk"])
        self.assertEqual(kwargs["interaction_type"], "Reassignment accepted")

    @mock.patch("reassignment_requests.views.log_persistence_check")
    @mock.patch("reassignment_requests.views.log_event")
    def test_original_ar_guests_after_split_is_logged(
        self, _mock_log_event, mock_log_pc
    ):
        self.client.post(self.url, {"action": "accept", "comments": "ok"}, follow=True)
        self.ar.refresh_from_db()

        calls = _find_log_calls(
            mock_log_pc.call_args_list,
            "accept_reassignment_request: original AR guests after split",
        )
        self.assertEqual(len(calls), 1)
        changes = calls[0].kwargs["changes"]
        self.assertEqual(changes["person_id"], (self.ar.person_id, self.ar.person_id))
        self.assertEqual(changes["edited_in_app"], (True, True))

    @mock.patch("reassignment_requests.views.log_persistence_check")
    @mock.patch("reassignment_requests.views.log_event")
    def test_new_ar_guests_after_split_is_logged(self, _mock_log_event, mock_log_pc):
        self.client.post(self.url, {"action": "accept", "comments": "ok"}, follow=True)
        self.guest_a.refresh_from_db()
        new_ar = MvAccommodationRequest.objects.get(
            pk=self.guest_a.accommodation_request_id
        )

        calls = _find_log_calls(
            mock_log_pc.call_args_list,
            "accept_reassignment_request: new AR guests after split",
        )
        self.assertEqual(len(calls), 1)
        changes = calls[0].kwargs["changes"]
        self.assertEqual(changes["person_id"], (new_ar.person_id, new_ar.person_id))
        self.assertEqual(changes["edited_in_app"], (True, True))


class RejectReassignmentLoggingTestCase(ReassignmentRequestsBaseTestCase):
    def setUp(self):
        super().setUp()
        GroupInfoFactory(
            ltla_name="ltla_destination",
            utla_name="utla_destination",
            gss_code="E000",
            utla_gss_code="E001",
        )
        self.user = get_user_with_groups(
            [UserGroup(name="ltla_destination", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(self.user)

        self.ar = MvAccommodationRequestFactory(
            number_of_people=2,
            person_id=[self.guest_a.id, self.guest_b.id],
            ltla_name=["ltla_somerset"],
        )
        self.request = self.pending_request_somerset_source_multiple_guests
        self.request.accommodation_request = self.ar
        self.request.save()
        self.url = reverse(
            "reassignment-requests:detail-received", kwargs={"pk": self.request.pk}
        )

    @mock.patch("reassignment_requests.views.log_persistence_check")
    @mock.patch("reassignment_requests.views.log_event")
    def test_started_event_is_logged(self, mock_log_event, _mock_log_pc):
        self.client.post(self.url, {"action": "reject", "comments": "no"}, follow=True)

        calls = _find_log_calls(
            mock_log_event.call_args_list, "reject_reassignment_request: started"
        )
        self.assertEqual(len(calls), 1)
        kwargs = calls[0].kwargs
        self.assertEqual(kwargs["reassignment_request_pk"], str(self.request.pk))

    @mock.patch("reassignment_requests.views.log_persistence_check")
    @mock.patch("reassignment_requests.views.log_event")
    def test_interaction_created_event_is_logged(self, mock_log_event, _mock_log_pc):
        self.client.post(self.url, {"action": "reject", "comments": "no"}, follow=True)

        calls = _find_log_calls(
            mock_log_event.call_args_list,
            "reject_reassignment_request: interaction created",
        )
        self.assertEqual(len(calls), 1)
        kwargs = calls[0].kwargs
        self.assertIsNotNone(kwargs["interaction_pk"])
        self.assertEqual(kwargs["interaction_type"], "Reassignment rejected")
        self.assertEqual(kwargs["ar_pk"], str(self.ar.pk))

    @mock.patch("reassignment_requests.views.log_persistence_check")
    @mock.patch("reassignment_requests.views.log_event")
    def test_outcome_set_persistence_check_is_logged(
        self, _mock_log_event, mock_log_pc
    ):
        self.client.post(self.url, {"action": "reject", "comments": "no"}, follow=True)
        self.request.refresh_from_db()

        calls = _find_log_calls(
            mock_log_pc.call_args_list, "reject_reassignment_request: outcome set"
        )
        self.assertEqual(len(calls), 1)
        changes = calls[0].kwargs["changes"]
        self.assertEqual(
            changes["outcome"],
            (self.request.outcome, self.request.outcome),
        )
        self.assertEqual(
            changes["responded_at"],
            (self.request.responded_at, self.request.responded_at),
        )


class CancelReassignmentLoggingTestCase(ReassignmentRequestsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(
            get_user_with_groups(
                [UserGroup(name="ltla_somerset", type=GroupType.LOCAL_AUTHORITY)]
            )
        )
        self.ar = MvAccommodationRequestFactory()
        self.request = self.pending_request_somerset_source_single_guest
        self.request.accommodation_request = self.ar
        self.request.save()
        self.url = reverse(
            "reassignment-requests:cancel-made", kwargs={"pk": self.request.pk}
        )

    @mock.patch("reassignment_requests.views.log_persistence_check")
    @mock.patch("reassignment_requests.views.log_event")
    def test_started_event_is_logged(self, mock_log_event, _mock_log_pc):
        self.client.post(self.url, {"confirmation": True}, follow=True)

        calls = _find_log_calls(
            mock_log_event.call_args_list, "cancel_reassignment_request: started"
        )
        self.assertEqual(len(calls), 1)
        kwargs = calls[0].kwargs
        self.assertEqual(kwargs["reassignment_request_pk"], str(self.request.pk))
        self.assertEqual(kwargs["ar_pk"], str(self.ar.pk))

    @mock.patch("reassignment_requests.views.log_persistence_check")
    @mock.patch("reassignment_requests.views.log_event")
    def test_outcome_set_persistence_check_is_logged(
        self, _mock_log_event, mock_log_pc
    ):
        self.client.post(self.url, {"confirmation": True}, follow=True)
        self.request.refresh_from_db()

        calls = _find_log_calls(
            mock_log_pc.call_args_list, "cancel_reassignment_request: outcome set"
        )
        self.assertEqual(len(calls), 1)
        changes = calls[0].kwargs["changes"]
        self.assertEqual(
            changes["outcome"],
            (self.request.outcome, self.request.outcome),
        )
