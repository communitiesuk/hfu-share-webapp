from unittest.mock import patch

from django.db import DatabaseError
from django.urls import reverse

from accommodation_requests.tests.base import AccommodationRequestsBaseTestCase
from accommodation_requests.views import RematchGuestsFormSteps
from accounts.tests.base import TestSessionTokenMixin
from ontology.models import MvAccommodationRequest, MvInteraction
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import get_la_user


class RematchGuestsDBErrorTestCase(
    TestSessionTokenMixin, AccommodationRequestsBaseTestCase
):
    def setUp(self):
        super().setUp()
        self.user = get_la_user()
        self.client.force_login(self.user)
        self.accommodation = MvAccommodationFactory(
            full_address="somerset accommodation",
            is_available_for_rematch=True,
            ltla_name="ltla_somerset",
            utla_name="utla_somerset",
            is_principal=True,
        )
        self.ar = MvAccommodationRequestFactory(
            title="Multiple guests acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[str(self.accommodation.pk)],
            number_of_people=2,
            person_id=[self.guest.pk, self.guest_2.pk],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            active_host=MvVolunteerFactory(),
        )
        self.guest.accommodation_request = self.ar
        self.guest.save()
        self.guest_2.accommodation_request = self.ar
        self.guest_2.save()

    def get_rematch_step_url(self, step):
        return reverse(
            "accommodation-requests:rematch-guests-step",
            kwargs={"pk": self.ar.pk, "step": step},
        )

    def _post_confirmation(self, pk):
        return self.client.post(
            self.get_rematch_step_url(RematchGuestsFormSteps.CONFIRMATION),
            {
                "confirmation-confirm_guests_moved": "on",
                f"rematch_guests_form_wizard_{pk}-current_step": RematchGuestsFormSteps.CONFIRMATION,  # noqa E501
            },
            follow=True,
        )

    def _assert_error_message(self, response):
        self.assertContains(
            response,
            "The guest was not moved. If the problem continues raise a support ticket.",
        )

    def _assert_plural_error_message(self, response):
        self.assertContains(
            response,
            "The guests were not moved. If the "
            "problem continues raise a support ticket.",
        )

    def _assert_rollback(self, ar_count_before, interaction_count_before):
        self.assertEqual(MvAccommodationRequest.objects.count(), ar_count_before)
        self.assertEqual(MvInteraction.objects.count(), interaction_count_before)
        self.ar.refresh_from_db()
        self.assertEqual(
            self.ar.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

    def _run_rematch_wizard_to_confirmation(self):
        pk = self.ar.pk
        guest_id = str(self.guest.pk)
        accommodation_id = str(self.accommodation.pk)

        # Step 1: Select guests
        response = self.client.post(
            self.get_rematch_step_url(RematchGuestsFormSteps.GUESTS),
            {
                "guests-guests": [guest_id],
                f"rematch_guests_form_wizard_{pk}-current_step": RematchGuestsFormSteps.GUESTS,  # noqa E501
            },
            follow=True,
        )
        self.assertContains(response, "Select accommodation")

        # Step 2: Select accommodation
        response = self.client.post(
            self.get_rematch_step_url(RematchGuestsFormSteps.SELECT_ACCOMMODATION),
            {
                "select_accommodation-accommodation": accommodation_id,
                f"rematch_guests_form_wizard_{pk}-current_step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,  # noqa E501
            },
            follow=True,
        )
        self.assertContains(response, "Are you sure you want to move")
        return pk

    def test_db_error_on_ar_save(self):
        pk = self._run_rematch_wizard_to_confirmation()
        ar_count = MvAccommodationRequest.objects.count()
        interaction_count = MvInteraction.objects.count()
        with patch(
            "ontology.models.MvAccommodationRequest.MvAccommodationRequest.save",
            side_effect=DatabaseError,
        ):
            response = self._post_confirmation(pk)
        self._assert_error_message(response)
        self._assert_rollback(ar_count, interaction_count)

    def test_db_error_on_update_accommodation(self):
        pk = self._run_rematch_wizard_to_confirmation()
        ar_count = MvAccommodationRequest.objects.count()
        interaction_count = MvInteraction.objects.count()
        with patch(
            "ontology.models.MvAccommodationRequest.MvAccommodationRequest.update_accommodation",
            side_effect=DatabaseError,
        ):
            response = self._post_confirmation(pk)
        self._assert_error_message(response)
        self._assert_rollback(ar_count, interaction_count)

    def test_db_error_on_unlink_host(self):
        host = MvVolunteerFactory()
        self.ar.active_host = host
        self.ar.save()
        pk = self._run_rematch_wizard_to_confirmation()
        ar_count = MvAccommodationRequest.objects.count()
        interaction_count = MvInteraction.objects.count()
        with patch(
            "ontology.models.MvAccommodationRequest.MvAccommodationRequest.unlink_host",
            side_effect=DatabaseError,
        ):
            response = self._post_confirmation(pk)
        self._assert_error_message(response)
        self._assert_rollback(ar_count, interaction_count)

    def test_db_error_on_split_guests(self):
        pk = self._run_rematch_wizard_to_confirmation()
        ar_count = MvAccommodationRequest.objects.count()
        interaction_count = MvInteraction.objects.count()
        with patch(
            "ontology.models.MvAccommodationRequest.MvAccommodationRequest.split_guests",
            side_effect=DatabaseError,
        ):
            response = self._post_confirmation(pk)
        self._assert_error_message(response)
        self._assert_rollback(ar_count, interaction_count)

    def test_plural_error_message_when_multiple_guests_not_moved(self):
        pk = self.ar.pk
        accommodation_id = str(self.accommodation.pk)

        # Select both guests
        response = self.client.post(
            self.get_rematch_step_url(RematchGuestsFormSteps.GUESTS),
            {
                "guests-guests": [str(self.guest.pk), str(self.guest_2.pk)],
                f"rematch_guests_form_wizard_{pk}-current_step": RematchGuestsFormSteps.GUESTS,  # noqa E501
            },
            follow=True,
        )
        self.assertContains(response, "Select accommodation")

        response = self.client.post(
            self.get_rematch_step_url(RematchGuestsFormSteps.SELECT_ACCOMMODATION),
            {
                "select_accommodation-accommodation": accommodation_id,
                f"rematch_guests_form_wizard_{pk}-current_step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,  # noqa E501
            },
            follow=True,
        )
        self.assertContains(response, "Are you sure you want to move")

        ar_count = MvAccommodationRequest.objects.count()
        interaction_count = MvInteraction.objects.count()
        with patch(
            "ontology.models.MvAccommodationRequest.MvAccommodationRequest.save",
            side_effect=DatabaseError,
        ):
            response = self._post_confirmation(pk)
        self._assert_plural_error_message(response)
        self._assert_rollback(ar_count, interaction_count)
