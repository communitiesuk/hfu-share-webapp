from unittest import mock

from django.urls import reverse

from accommodation_requests.tests.base import AccommodationRequestsBaseTestCase
from accommodation_requests.views import RematchGuestsFormSteps
from accounts.tests.base import TestSessionTokenMixin
from ontology.models.MvAccommodationRequest import MvAccommodationRequest
from ontology.tests.base import LocalAuthorityBaseTestCaseMixin
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import get_admin_user


def _find_log_calls(mock_calls, message):
    return [c for c in mock_calls if c.args[0] == message]


def _post_rematch_single_guest(client, ar, accommodation):
    client.post(
        reverse("accommodation-requests:move-guests", kwargs={"pk": ar.pk}),
        {"within_la": "yes"},
        follow=True,
    )
    client.post(
        reverse(
            "accommodation-requests:rematch-guests-step",
            kwargs={"pk": ar.pk, "step": RematchGuestsFormSteps.SELECT_ACCOMMODATION},
        ),
        {
            "select_accommodation-accommodation": accommodation.pk,
            f"rematch_guests_form_wizard_{ar.pk}-current_step": (
                RematchGuestsFormSteps.SELECT_ACCOMMODATION
            ),
        },
        follow=True,
    )
    client.post(
        reverse(
            "accommodation-requests:rematch-guests-step",
            kwargs={"pk": ar.pk, "step": RematchGuestsFormSteps.CONFIRMATION},
        ),
        {
            "confirmation-confirm_guests_moved": "on",
            f"rematch_guests_form_wizard_{ar.pk}-current_step": (
                RematchGuestsFormSteps.CONFIRMATION
            ),
        },
        follow=True,
    )


def _post_rematch_partial(client, ar, guest_to_move, accommodation):
    client.post(
        reverse("accommodation-requests:move-guests", kwargs={"pk": ar.pk}),
        {"within_la": "yes"},
        follow=True,
    )
    client.post(
        reverse(
            "accommodation-requests:rematch-guests-step",
            kwargs={"pk": ar.pk, "step": RematchGuestsFormSteps.GUESTS},
        ),
        {
            "guests-guests": [guest_to_move.pk],
            f"rematch_guests_form_wizard_{ar.pk}-current_step": (
                RematchGuestsFormSteps.GUESTS
            ),
        },
        follow=True,
    )
    client.post(
        reverse(
            "accommodation-requests:rematch-guests-step",
            kwargs={"pk": ar.pk, "step": RematchGuestsFormSteps.SELECT_ACCOMMODATION},
        ),
        {
            "select_accommodation-accommodation": accommodation.pk,
            f"rematch_guests_form_wizard_{ar.pk}-current_step": (
                RematchGuestsFormSteps.SELECT_ACCOMMODATION
            ),
        },
        follow=True,
    )
    client.post(
        reverse(
            "accommodation-requests:rematch-guests-step",
            kwargs={"pk": ar.pk, "step": RematchGuestsFormSteps.CONFIRMATION},
        ),
        {
            "confirmation-confirm_guests_moved": "on",
            f"rematch_guests_form_wizard_{ar.pk}-current_step": (
                RematchGuestsFormSteps.CONFIRMATION
            ),
        },
        follow=True,
    )


class RematchLoggingTestCase(
    TestSessionTokenMixin,
    LocalAuthorityBaseTestCaseMixin,
    AccommodationRequestsBaseTestCase,
):
    def setUp(self):
        super().setUp()
        self.client.force_login(get_admin_user())

        self.host = MvVolunteerFactory(is_principal=True)
        self.rematch_guest = MvPersonFactory()
        self.new_accommodation = MvAccommodationFactory(
            ltla_name=self.ltla_name,
            utla_name=self.utla_name,
        )
        self.ar = MvAccommodationRequestFactory(
            number_of_people=1,
            person_id=[self.rematch_guest.pk],
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one.pk],
            active_host=self.host,
            ltla_name=[self.ltla_name],
            utla_name=[self.utla_name],
        )
        self.rematch_guest.accommodation_request = self.ar
        self.rematch_guest.save()

    @mock.patch("accommodation_requests.views.log_persistence_check")
    @mock.patch("accommodation_requests.views.log_event")
    def test_started_event_is_logged(self, mock_log_event, _mock_log_pc):
        _post_rematch_single_guest(self.client, self.ar, self.new_accommodation)

        calls = _find_log_calls(
            mock_log_event.call_args_list, "rematch_guests: started"
        )
        self.assertEqual(len(calls), 1)
        kwargs = calls[0].kwargs
        self.assertEqual(kwargs["ar_pk"], self.ar.pk)
        self.assertEqual(kwargs["accommodation_pk"], self.new_accommodation.pk)

    @mock.patch("accommodation_requests.views.log_persistence_check")
    @mock.patch("accommodation_requests.views.log_event")
    def test_accommodation_updated_persistence_check_is_logged(
        self, _mock_log_event, mock_log_pc
    ):
        _post_rematch_single_guest(self.client, self.ar, self.new_accommodation)

        self.ar.refresh_from_db()

        calls = _find_log_calls(
            mock_log_pc.call_args_list, "rematch_guests: accommodation updated"
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

    @mock.patch("accommodation_requests.views.log_persistence_check")
    @mock.patch("accommodation_requests.views.log_event")
    def test_guest_ar_links_event_is_logged(self, mock_log_event, _mock_log_pc):
        _post_rematch_single_guest(self.client, self.ar, self.new_accommodation)

        calls = _find_log_calls(
            mock_log_event.call_args_list, "rematch_guests: guest AR links"
        )
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            calls[0].kwargs["guest_ar_links"],
            [{"id": self.rematch_guest.pk, "accommodation_request_id": self.ar.pk}],
        )

    @mock.patch("accommodation_requests.views.log_persistence_check")
    @mock.patch("accommodation_requests.views.log_event")
    def test_host_unlinked_persistence_check_is_logged(
        self, _mock_log_event, mock_log_pc
    ):
        _post_rematch_single_guest(self.client, self.ar, self.new_accommodation)

        calls = _find_log_calls(
            mock_log_pc.call_args_list, "rematch_guests: host unlinked"
        )
        self.assertEqual(len(calls), 1)
        changes = calls[0].kwargs["changes"]
        self.assertEqual(changes["active_host_id"], (None, None))
        self.assertEqual(changes["edited_in_app"], (True, True))

    @mock.patch("accommodation_requests.views.log_persistence_check")
    @mock.patch("accommodation_requests.views.log_event")
    def test_host_updated_persistence_check_is_logged(
        self, _mock_log_event, mock_log_pc
    ):
        _post_rematch_single_guest(self.client, self.ar, self.new_accommodation)

        self.ar.refresh_from_db()

        calls = _find_log_calls(
            mock_log_pc.call_args_list, "rematch_guests: host updated"
        )
        self.assertEqual(len(calls), 1)
        changes = calls[0].kwargs["changes"]
        self.assertEqual(
            changes["active_host_id"],
            (self.ar.active_host_id, self.ar.active_host_id),
        )
        self.assertEqual(changes["edited_in_app"], (True, True))

    @mock.patch("accommodation_requests.views.log_persistence_check")
    @mock.patch("accommodation_requests.views.log_event")
    def test_interaction_created_event_is_logged(self, mock_log_event, _mock_log_pc):
        _post_rematch_single_guest(self.client, self.ar, self.new_accommodation)

        calls = _find_log_calls(
            mock_log_event.call_args_list, "rematch_guests: interaction created"
        )
        self.assertEqual(len(calls), 1)
        kwargs = calls[0].kwargs
        self.assertIsNotNone(kwargs["interaction_pk"])
        self.assertEqual(kwargs["interaction_type"], "Rematch Recorded")

    @mock.patch("accommodation_requests.views.log_persistence_check")
    @mock.patch("accommodation_requests.views.log_event")
    def test_checks_status_updated_persistence_check_is_logged(
        self, _mock_log_event, mock_log_pc
    ):
        _post_rematch_single_guest(self.client, self.ar, self.new_accommodation)

        self.ar.refresh_from_db()

        calls = _find_log_calls(
            mock_log_pc.call_args_list, "rematch_guests: checks status updated"
        )
        self.assertEqual(len(calls), 1)
        changes = calls[0].kwargs["changes"]
        self.assertEqual(
            changes["checks_status"], (self.ar.checks_status, self.ar.checks_status)
        )
        self.assertEqual(changes["edited_in_app"], (True, True))


class RematchPartialLoggingTestCase(
    TestSessionTokenMixin,
    LocalAuthorityBaseTestCaseMixin,
    AccommodationRequestsBaseTestCase,
):
    def setUp(self):
        super().setUp()
        self.client.force_login(get_admin_user())

        self.guest_a = MvPersonFactory()
        self.guest_b = MvPersonFactory()
        self.new_accommodation = MvAccommodationFactory(
            ltla_name=self.ltla_name,
            utla_name=self.utla_name,
        )
        self.ar = MvAccommodationRequestFactory(
            number_of_people=2,
            person_id=[self.guest_a.pk, self.guest_b.pk],
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one.pk],
            ltla_name=[self.ltla_name],
            utla_name=[self.utla_name],
        )
        self.guest_a.accommodation_request = self.ar
        self.guest_a.save()
        self.guest_b.accommodation_request = self.ar
        self.guest_b.save()

    @mock.patch("accommodation_requests.views.log_persistence_check")
    @mock.patch("accommodation_requests.views.log_event")
    def test_guests_split_event_is_logged(self, mock_log_event, _mock_log_pc):
        _post_rematch_partial(
            self.client, self.ar, self.guest_b, self.new_accommodation
        )

        calls = _find_log_calls(
            mock_log_event.call_args_list, "rematch_guests: guests split to new AR"
        )
        self.guest_b.refresh_from_db()
        self.assertEqual(len(calls), 1)
        kwargs = calls[0].kwargs
        self.assertEqual(kwargs["original_ar_pk"], self.ar.pk)
        self.assertEqual(
            str(kwargs["new_ar_pk"]), str(self.guest_b.accommodation_request_id)
        )

    @mock.patch("accommodation_requests.views.log_persistence_check")
    @mock.patch("accommodation_requests.views.log_event")
    def test_original_ar_guests_after_split_is_logged(
        self, _mock_log_event, mock_log_pc
    ):
        _post_rematch_partial(
            self.client, self.ar, self.guest_b, self.new_accommodation
        )
        self.ar.refresh_from_db()

        calls = _find_log_calls(
            mock_log_pc.call_args_list,
            "rematch_guests: original AR guests after split",
        )
        self.assertEqual(len(calls), 1)
        changes = calls[0].kwargs["changes"]
        self.assertEqual(changes["person_id"], (self.ar.person_id, self.ar.person_id))
        self.assertEqual(changes["edited_in_app"], (True, True))

    @mock.patch("accommodation_requests.views.log_persistence_check")
    @mock.patch("accommodation_requests.views.log_event")
    def test_new_ar_guests_after_split_is_logged(self, _mock_log_event, mock_log_pc):
        _post_rematch_partial(
            self.client, self.ar, self.guest_b, self.new_accommodation
        )
        self.guest_b.refresh_from_db()
        new_ar = MvAccommodationRequest.objects.get(
            pk=self.guest_b.accommodation_request_id
        )

        calls = _find_log_calls(
            mock_log_pc.call_args_list,
            "rematch_guests: new AR guests after split",
        )
        self.assertEqual(len(calls), 1)
        changes = calls[0].kwargs["changes"]
        self.assertEqual(changes["person_id"], (new_ar.person_id, new_ar.person_id))
        self.assertEqual(changes["edited_in_app"], (True, True))
