import http.client
from unittest.mock import MagicMock, patch

from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode

from accommodation_requests.tests.base import AccommodationRequestsBaseTestCase
from accommodation_requests.views import (
    ReassignGuestsFormSteps,
    ReassignGuestsFormWizard,
    RematchGuestsFormSteps,
    RematchGuestsFormWizard,
)
from accounts.tests.base import TestSessionTokenMixin
from ontology.models import CheckType, MvAccommodationRequest, MvInteraction, MvPerson
from ontology.models.DevCheckV2 import DevCheckV2
from ontology.tests.base import LocalAuthorityBaseTestCaseMixin
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvGroupFactory,
    MvPersonFactory,
    MvVolunteerFactory,
)
from ontology.tests.factories import MvAccommodationRequestFactory as AccReqFactory
from user_management.tests.base import (
    get_admin_user,
    get_la_user,
    get_user_with_no_access,
)


class MoveGuestsFormWizardTestCase(
    TestSessionTokenMixin,
    LocalAuthorityBaseTestCaseMixin,
    AccommodationRequestsBaseTestCase,
):
    def test_should_return_404_for_ar_user_has_no_access_to(self):
        no_access_user = get_user_with_no_access()
        self.client.force_login(no_access_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                args=[self.checks_required_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_should_return_409_for_closed_accommodation_requests(self):
        user = get_admin_user()
        self.client.force_login(user)

        for ar in self.closed_acc_reqs:
            response = self.client.get(
                reverse("accommodation-requests:move-guests", args=[ar.id])
            )

            self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_should_return_409_for_accommodation_requests_without_guests(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                args=[self.no_guests_acc_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_returns_409_for_accommodation_requests_with_only_guests_outside_users_la(
        self,
    ):
        # Guest LA is determined via the guest.accommodation_request LTLA and UTLA names
        # Therefore simulating a guest from a different LA by creating a new guest and
        # AR, where the guest is missing the link to the AR but is in the AR.person_id
        guest = MvPersonFactory(id="person-id", first_name="John", last_name="Doe")
        acc_req = AccReqFactory(
            title="One guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one],
            number_of_people=1,
            person_id=[guest.pk],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
        )

        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                args=[acc_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_returns_409_for_accommodation_requests_with_only_non_existent_guests(
        self,
    ):
        # Intentionally not using the MvPersonFactory here so that we don't save to
        # the DB. This is testing a scenario we saw in prod where an AR had
        # a FK to a guest, but no guest with that key could be found in the
        # MvPerson table
        guest = MvPerson(id="1234")
        acc_req = AccReqFactory(
            title="Fake guests acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            person_id=[guest.id],
        )

        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                args=[acc_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_is_staying_in_la_label_is_singular_for_one_guest(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": self.one_guest_acc_req.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(
            response, "Is the guest remaining within your local authority?"
        )

    def test_is_staying_in_la_label_is_plural_for_multiple_guest(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": self.multiple_guests_acc_req.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(
            response, "Are the guests remaining within your local authority?"
        )


class ReassignGuestsFormWizardTestCase(
    TestSessionTokenMixin,
    LocalAuthorityBaseTestCaseMixin,
    AccommodationRequestsBaseTestCase,
):
    def test_should_return_404_for_ar_user_has_no_access_to(self):
        no_access_user = get_user_with_no_access()
        self.client.force_login(no_access_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:reassign-guests",
                args=[self.checks_required_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_should_return_409_for_closed_accommodation_requests(self):
        user = get_admin_user()
        self.client.force_login(user)

        for ar in self.closed_acc_reqs:
            response = self.client.get(
                reverse("accommodation-requests:reassign-guests", args=[ar.id])
            )

            self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_should_return_409_for_accommodation_requests_without_guests(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:reassign-guests",
                args=[self.no_guests_acc_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_returns_409_for_accommodation_requests_with_only_guests_outside_users_la(
        self,
    ):
        # Guest LA is determined via the guest.accommodation_request LTLA and UTLA names
        # Therefore simulating a guest from a different LA by creating a new guest and
        # AR, where the guest is missing the link to the AR but is in the AR.person_id
        guest = MvPersonFactory(id="person-id", first_name="John", last_name="Doe")
        acc_req = AccReqFactory(
            title="One guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one],
            number_of_people=1,
            person_id=[guest.pk],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
        )

        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:reassign-guests",
                args=[acc_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_returns_409_for_accommodation_requests_with_only_non_existent_guests(
        self,
    ):
        # Intentionally not using the MvPersonFactory here so that we don't save to
        # the DB. This is testing a scenario we saw in prod where an AR had
        # a FK to a guest, but no guest with that key could be found in the
        # MvPerson table
        guest = MvPerson(id="1234")
        acc_req = AccReqFactory(
            title="Fake guests acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            person_id=[guest.id],
        )

        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:reassign-guests",
                args=[acc_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_reassignment_guests_step_shows_when_multiple_guests_on_ar(self):
        user = get_admin_user()
        self.client.force_login(user)

        # View first step
        response = self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": self.multiple_guests_acc_req.id,
                },
            )
        )

        self.assertContains(
            response, "Are the guests remaining within your local authority?"
        )

        # Submit the 'staying in LA' step
        response = self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": self.multiple_guests_acc_req.pk,
                },
            ),
            {
                "within_la": "no",
            },
            follow=True,
        )

        self.assertIn("reassign-guests", response.request["PATH_INFO"])
        self.assertContains(response, "Select guests")
        self.assertContains(
            response, "You can only move guests to one local authority at a time."
        )

    def test_reassignment_guests_step_only_shows_guests_within_users_la(self):
        # Guest LA is determined via the guest.accommodation_request LTLA and UTLA names
        # Therefore simulating a guest from a different LA by creating a new guest and
        # AR, where the guest is missing the link to the AR but is in the AR.person_id
        guest_1 = MvPersonFactory(
            id="person-id-1", first_name="Alice", last_name="Smith"
        )
        guest_2 = MvPersonFactory(id="person-id-2", first_name="Bob", last_name="Brown")
        guest_3 = MvPersonFactory(id="person-id-3", first_name="John", last_name="Doe")
        acc_req = AccReqFactory(
            title="One guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one],
            number_of_people=3,
            person_id=[guest_1.pk, guest_2.pk, guest_3.pk],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
        )

        guests_within_la = [guest_1, guest_2]
        guests_outside_la = [guest_3]

        for guest in guests_within_la:
            guest.accommodation_request = acc_req
            guest.save()

        user = get_la_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": acc_req.id,
                },
            ),
            {
                "within_la": "no",
            },
            follow=True,
        )

        self.assertContains(response, "Select guests")
        self.assertContains(
            response, "You can only move guests to one local authority at a time."
        )
        for guest in guests_within_la:
            self.assertContains(response, guest.get_full_name())
        for guest in guests_outside_la:
            self.assertNotContains(response, guest.get_full_name())

    def test_reassignment_guests_step_doesnt_show_when_one_guest_on_ar(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_request = AccReqFactory(
            title="Two guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            number_of_people=1,
            person_id=[self.guest.pk],
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one.pk],
            ltla_name=[self.ltla_name],
            utla_name=[self.utla_name],
        )

        # View first step
        response = self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.id,
                },
            )
        )

        self.assertContains(
            response, "Is the guest remaining within your local authority?"
        )

        # Submit the 'staying in LA' step
        response = self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.pk,
                },
            ),
            {
                "within_la": "no",
            },
            follow=True,
        )

        self.assertIn("reassign-guests", response.request["PATH_INFO"])
        self.assertNotContains(response, "Select guests")
        self.assertNotContains(
            response, "You can only move guests to one local authority at a time."
        )

    def test_reassignment_shows_correct_content_single_guest(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_request = AccReqFactory(
            title="Two guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            number_of_people=1,
            person_id=[self.guest.pk],
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one.pk],
            ltla_name=[self.ltla_name],
            utla_name=[self.utla_name],
        )

        # View first step
        response = self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.id,
                },
            )
        )
        self.assertContains(
            response, "Is the guest remaining within your local authority?"
        )

        # Submit the first step
        response = self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.pk,
                },
            ),
            {
                "within_la": "no",
            },
            follow=True,
        )
        self.assertContains(response, "Select where to move the guest to")

        # Submit "country" step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.COUNTRY,
                },
            ),
            {
                "country-country": "England",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.COUNTRY,
            },
            follow=True,
        )

        self.assertContains(response, "Select local authority")
        self.assertContains(response, self.english_ltla_name)
        self.assertNotContains(response, self.northern_irish_ltla_name)
        self.assertNotContains(response, self.welsh_ltla_name)
        self.assertNotContains(response, self.scottish_ltla_name)

        # Submit "local_authority" step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.LOCAL_AUTHORITY,
                },
            ),
            {
                "local_authority-local_authority": self.english_ltla_name,
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.LOCAL_AUTHORITY,
            },
            follow=True,
        )
        self.assertContains(response, "Reason for moving guest")

        # Submit "reason" step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.REASON,
                },
            ),
            {
                "reason-reason": "This is the reason...",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.REASON,
            },
            follow=True,
        )

        self.assertNotContains(response, "Select local authority")
        self.assertContains(response, "Are you sure you want to move")
        self.assertContains(response, "Yes, send the request")

        # Submit "confirmation" step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.CONFIRMATION,
                },
            ),
            {
                "confirmation-confirm_guests_moved": "on",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.CONFIRMATION,
                "move_guests": "",
            },
            follow=True,
        )

        reassignment_requests = accommodation_request.reassignment_requests.all()
        # Check that the reassignment request was created
        self.assertTrue(len(reassignment_requests) == 1)

        # Check that the reassignment request has the correct guests
        guest_ids = [guest.pk for guest in reassignment_requests[0].guests.all()]
        self.assertTrue(guest_ids == [self.guest.pk])

        self.assertContains(
            response,
            f"You sent a request to move {self.guest.get_full_name()} "
            f"to {self.english_ltla_name}",
        )

    def test_reassignment_journey_partial(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_request = AccReqFactory(
            title="Two guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            number_of_people=2,
            person_id=[self.guest.pk, self.guest_2.pk],
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one.pk],
            ltla_name=[self.ltla_name],
            utla_name=[self.utla_name],
        )

        # View first step
        response = self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.id,
                },
            )
        )
        self.assertContains(
            response, "Are the guests remaining within your local authority?"
        )

        # Submit the first step
        response = self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.pk,
                },
            ),
            {
                "within_la": "no",
            },
            follow=True,
        )

        self.assertContains(response, "Select guests")
        # Submit the 'guests' step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.GUESTS,
                },
            ),
            {
                "guests-guests": [self.guest.pk],
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.GUESTS,
            },
            follow=True,
        )

        self.assertContains(response, "Select where to move the guests to")

        # Submit "country" step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.COUNTRY,
                },
            ),
            {
                "country-country": "England",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.COUNTRY,
            },
            follow=True,
        )

        self.assertContains(response, "Select local authority")
        self.assertContains(response, self.english_ltla_name)
        self.assertNotContains(response, self.northern_irish_ltla_name)
        self.assertNotContains(response, self.welsh_ltla_name)
        self.assertNotContains(response, self.scottish_ltla_name)

        # Submit "local_authority" step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.LOCAL_AUTHORITY,
                },
            ),
            {
                "local_authority-local_authority": self.english_ltla_name,
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.LOCAL_AUTHORITY,
            },
            follow=True,
        )
        self.assertContains(response, "Reason for moving guest")

        # Submit "reason" step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.REASON,
                },
            ),
            {
                "reason-reason": "This is the reason...",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.REASON,
            },
            follow=True,
        )

        self.assertNotContains(response, "Select local authority")
        self.assertContains(response, "Are you sure you want to move")
        self.assertContains(response, "Yes, send the request")

        # Submit "confirmation" step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.CONFIRMATION,
                },
            ),
            {
                "confirmation-confirm_guests_moved": "on",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.CONFIRMATION,
                "move_guests": "",
            },
            follow=True,
        )

        reassignment_requests = accommodation_request.reassignment_requests.all()
        # Check that the reassignment request was created
        self.assertTrue(len(reassignment_requests) == 1)

        # Check that the reassignment request has the correct guests
        guest_ids = [guest.pk for guest in reassignment_requests[0].guests.all()]
        self.assertTrue(guest_ids == [self.guest.pk])

        self.assertContains(
            response,
            f"You sent a request to move {self.guest.get_full_name()} "
            f"to {self.english_ltla_name}",
        )

        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=accommodation_request
        ).first()

        self.assertIsNotNone(interaction)

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.REASSIGNMENT_REQUEST_CREATED,
        )

    def test_reassignment_journey(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_request = AccReqFactory(
            title="Two guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            number_of_people=2,
            person_id=[self.guest.pk, self.guest_2.pk],
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one.pk],
            ltla_name=[self.ltla_name],
            utla_name=[self.utla_name],
        )

        # View first step
        response = self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.id,
                },
            )
        )
        self.assertContains(
            response, "Are the guests remaining within your local authority?"
        )

        # Submit the first step
        response = self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.pk,
                },
            ),
            {
                "within_la": "no",
            },
            follow=True,
        )
        self.assertContains(response, "Select guests")

        # Submit the 'guests' step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.GUESTS,
                },
            ),
            {
                "guests-guests": [self.guest.pk, self.guest_2.pk],
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.GUESTS,
            },
            follow=True,
        )

        self.assertContains(response, "Select where to move the guests to")

        # Submit "country" step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.COUNTRY,
                },
            ),
            {
                "country-country": "Wales",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.COUNTRY,
            },
            follow=True,
        )

        self.assertContains(response, "Select local authority")
        self.assertContains(response, self.welsh_ltla_name)
        self.assertNotContains(response, self.english_ltla_name)
        self.assertNotContains(response, self.northern_irish_ltla_name)
        self.assertNotContains(response, self.scottish_ltla_name)

        # Submit "local_authority" step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.LOCAL_AUTHORITY,
                },
            ),
            {
                "local_authority-local_authority": self.welsh_la.ltla_name,
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.LOCAL_AUTHORITY,
            },
            follow=True,
        )
        self.assertContains(response, "Reason for moving guests")

        # Submit "reason" step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.REASON,
                },
            ),
            {
                "reason-reason": "This is the reason...",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.REASON,
            },
            follow=True,
        )

        self.assertNotContains(response, "Select local authority")
        self.assertContains(response, "Are you sure you want to move")
        self.assertContains(response, "Yes, send the request")

        # Submit "confirmation" step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.CONFIRMATION,
                },
            ),
            {
                "confirmation-confirm_guests_moved": "on",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.CONFIRMATION,
                "move_guests": "",
            },
            follow=True,
        )

        reassignment_requests = accommodation_request.reassignment_requests.all()
        # Check that the reassignment request was created
        self.assertTrue(len(reassignment_requests) == 1)

        # Check that the reassignment request has the correct guests
        guest_ids = set(guest.pk for guest in reassignment_requests[0].guests.all())
        self.assertTrue(guest_ids == {self.guest.pk, self.guest_2.pk})

        self.assertContains(
            response,
            f"You sent a request to move {self.guest.get_full_name()} and "
            f"{self.guest_2.get_full_name()} to {self.welsh_ltla_name}",
        )

        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=accommodation_request
        ).first()

        self.assertIsNotNone(interaction)

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.REASSIGNMENT_REQUEST_CREATED,
        )

    def test_reassignment_journey_with_incorrect_number_of_people(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Accommodation request with incorrect number of people
        accommodation_request = AccReqFactory(
            title="Two guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            number_of_people=1,
            person_id=[self.guest.pk, self.guest_2.pk],
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one.pk],
            ltla_name=[self.ltla_name],
            utla_name=[self.utla_name],
        )

        # View first step
        response = self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.id,
                },
            )
        )
        self.assertContains(
            response, "Are the guests remaining within your local authority?"
        )

        # Submit the first step
        response = self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.pk,
                },
            ),
            {
                "within_la": "no",
            },
            follow=True,
        )

        # Shows the guests step when the number of people is 1
        self.assertContains(response, "Select guests")

    def test_interaction_created_when_reassignment_request_raised(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_request = AccReqFactory(
            title="One guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            number_of_people=1,
            person_id=[self.guest.pk],
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one.pk],
            ltla_name=[self.ltla_name],
            utla_name=[self.utla_name],
        )

        # Submit the first step
        self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.pk,
                },
            ),
            {
                "within_la": "no",
            },
            follow=True,
        )

        # Submit "country" step
        self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.COUNTRY,
                },
            ),
            {
                "country-country": "Wales",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.COUNTRY,
            },
            follow=True,
        )

        # Submit "local_authority" step
        self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.LOCAL_AUTHORITY,
                },
            ),
            {
                "local_authority-local_authority": self.welsh_la.ltla_name,
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.LOCAL_AUTHORITY,
            },
            follow=True,
        )

        # Submit "reason" step
        self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.REASON,
                },
            ),
            {
                "reason-reason": "This is the reason...",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.REASON,
            },
            follow=True,
        )

        # Submit "confirmation" step
        self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.CONFIRMATION,
                },
            ),
            {
                "confirmation-confirm_guests_moved": "on",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.CONFIRMATION,
                "move_guests": "",
            },
            follow=True,
        )

        reassignment_requests = accommodation_request.reassignment_requests.all()
        # Check that the reassignment request was created
        self.assertTrue(len(reassignment_requests) == 1)

        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=accommodation_request
        ).first()

        self.assertIsNotNone(interaction)

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.REASSIGNMENT_REQUEST_CREATED,
        )

        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.REASSIGNMENT_REQUEST_CREATED,
        )
        self.assertEqual(
            interaction.interaction_notes,
            "Reassignment request for [names_list]John Smith[names_list_end] "
            "from test_ltla_name to test_welsh_ltla_name.",
        )
        self.assertEqual(
            interaction.created_by,
            user,
        )

    def test_interaction_created_when_reassignment_request_raised_from_multi_la(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_request = AccReqFactory(
            title="One guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            number_of_people=1,
            person_id=[self.guest.pk],
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one.pk],
            ltla_name=["ltla_somerset", "ltla_manchester"],
            utla_name=["utla_somerset", "utla_manchester"],
        )

        # Submit the first step
        self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.pk,
                },
            ),
            {
                "within_la": "no",
            },
            follow=True,
        )

        # Submit "country" step
        self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.COUNTRY,
                },
            ),
            {
                "country-country": "Wales",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.COUNTRY,
            },
            follow=True,
        )

        # Submit "local_authority" step
        self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.LOCAL_AUTHORITY,
                },
            ),
            {
                "local_authority-local_authority": self.welsh_la.ltla_name,
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.LOCAL_AUTHORITY,
            },
            follow=True,
        )

        # Submit "reason" step
        self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.REASON,
                },
            ),
            {
                "reason-reason": "This is the reason...",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.REASON,
            },
            follow=True,
        )

        # Submit "confirmation" step
        self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.CONFIRMATION,
                },
            ),
            {
                "confirmation-confirm_guests_moved": "on",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.CONFIRMATION,
                "move_guests": "",
            },
            follow=True,
        )

        reassignment_requests = accommodation_request.reassignment_requests.all()
        # Check that the reassignment request was created
        self.assertTrue(len(reassignment_requests) == 1)

        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=accommodation_request
        ).first()

        self.assertIsNotNone(interaction)

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.REASSIGNMENT_REQUEST_CREATED,
        )

        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.REASSIGNMENT_REQUEST_CREATED,
        )
        self.assertEqual(
            interaction.interaction_notes,
            "Reassignment request for [names_list]John Smith[names_list_end] "
            "from ltla_somerset|ltla_manchester to test_welsh_ltla_name.",
        )
        self.assertEqual(
            interaction.created_by,
            user,
        )

    def test_interaction_created_when_reassignment_request_raised_with_multiple_guests(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_request = AccReqFactory(
            title="One guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            number_of_people=2,
            person_id=[self.guest.pk, self.guest_2.pk],
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one.pk],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
        )

        # Submit the first step
        self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.pk,
                },
            ),
            {
                "within_la": "no",
            },
            follow=True,
        )

        # Submit the 'guests' step
        self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.GUESTS,
                },
            ),
            {
                "guests-guests": [self.guest.pk, self.guest_2.pk],
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.GUESTS,
            },
            follow=True,
        )

        # Submit "country" step
        self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.COUNTRY,
                },
            ),
            {
                "country-country": "Wales",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.COUNTRY,
            },
            follow=True,
        )

        # Submit "local_authority" step
        self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.LOCAL_AUTHORITY,
                },
            ),
            {
                "local_authority-local_authority": self.welsh_la.ltla_name,
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.LOCAL_AUTHORITY,
            },
            follow=True,
        )

        # Submit "reason" step
        self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.REASON,
                },
            ),
            {
                "reason-reason": "This is the reason...",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.REASON,
            },
            follow=True,
        )

        # Submit "confirmation" step
        self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.CONFIRMATION,
                },
            ),
            {
                "confirmation-confirm_guests_moved": "on",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.CONFIRMATION,
                "move_guests": "",
            },
            follow=True,
        )

        reassignment_requests = accommodation_request.reassignment_requests.all()
        # Check that the reassignment request was created
        self.assertTrue(len(reassignment_requests) == 1)

        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=accommodation_request
        ).first()

        self.assertIsNotNone(interaction)

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.REASSIGNMENT_REQUEST_CREATED,
        )

        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.REASSIGNMENT_REQUEST_CREATED,
        )
        self.assertEqual(
            interaction.interaction_notes,
            "Reassignment request for "
            "[names_list]Jane Doe and John Smith[names_list_end] "
            "from ltla_somerset to test_welsh_ltla_name.",
        )
        self.assertEqual(
            interaction.created_by,
            user,
        )

    def test_get_form_kwargs_handles_none_cleaned_data_does_not_throw(self):
        user = get_admin_user()
        self.client.force_login(user)

        acc_req = self.multiple_guests_acc_req
        response = self.client.get(
            reverse(
                "accommodation-requests:reassign-guests",
                args=[acc_req.id],
            )
        )

        wizard = ReassignGuestsFormWizard(
            form_list=ReassignGuestsFormWizard.form_list, condition_dict={}
        )
        wizard.request = response.wsgi_request
        wizard.object = acc_req
        wizard.form_list = {
            ReassignGuestsFormSteps.GUESTS: MagicMock(),
            ReassignGuestsFormSteps.CONFIRMATION: MagicMock(),
            ReassignGuestsFormSteps.LOCAL_AUTHORITY: MagicMock(),
        }

        with patch.object(
            ReassignGuestsFormWizard,
            "get_cleaned_data_for_step",
            return_value=None,
        ):
            wizard.get_form_kwargs(RematchGuestsFormSteps.CONFIRMATION)

    def test_reassignment_with_multi_la_wont_duplicate_items_in_source_lists(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_request = AccReqFactory(
            title="Multi la guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            number_of_people=1,
            person_id=[self.guest.pk],
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one.pk],
            ltla_name=["Bromley", "Lewisham"],
            utla_name=["Bromley", "Lewisham"],
        )

        # View first step
        response = self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.id,
                },
            )
        )
        self.assertContains(
            response, "Is the guest remaining within your local authority?"
        )

        # Submit the first step
        response = self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.pk,
                },
            ),
            {
                "within_la": "no",
            },
            follow=True,
        )

        # Submit "country" step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.COUNTRY,
                },
            ),
            {
                "country-country": "England",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.COUNTRY,
            },
            follow=True,
        )

        self.assertContains(response, "Select local authority")

        # Submit "local_authority" step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.LOCAL_AUTHORITY,
                },
            ),
            {
                "local_authority-local_authority": self.english_la.ltla_name,
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.LOCAL_AUTHORITY,
            },
            follow=True,
        )
        self.assertContains(response, "Reason for moving guest")

        # Submit "reason" step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.REASON,
                },
            ),
            {
                "reason-reason": "This is the reason...",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.REASON,
            },
            follow=True,
        )

        self.assertContains(response, "Are you sure you want to move")
        self.assertContains(response, "Yes, send the request")

        # Submit "confirmation" step
        response = self.client.post(
            reverse(
                "accommodation-requests:reassign-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": ReassignGuestsFormSteps.CONFIRMATION,
                },
            ),
            {
                "confirmation-confirm_guests_moved": "on",
                f"reassign_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": ReassignGuestsFormSteps.CONFIRMATION,
                "move_guests": "",
            },
            follow=True,
        )

        self.assertContains(
            response,
            f"You sent a request to move {self.guest.get_full_name()} "
            f"to {self.english_ltla_name}",
        )

        reassignment_requests = accommodation_request.reassignment_requests.all()
        self.assertTrue(len(reassignment_requests) == 1)

        # Retrieve the newly created reassignment request
        new_reassignment_request = reassignment_requests[0]

        # Reassignment request was created - source arrays should not have duplicates
        self.assertEqual(
            set(new_reassignment_request.source_country),
            set(["England"]),
        )
        self.assertEqual(
            set(new_reassignment_request.source_utla_code),
            set(["E09000023", "E09000006"]),
        )


class RematchGuestsFormWizardTestCase(
    TestSessionTokenMixin,
    LocalAuthorityBaseTestCaseMixin,
    AccommodationRequestsBaseTestCase,
):
    def test_should_return_404_for_ar_user_has_no_access_to(self):
        no_access_user = get_user_with_no_access()
        self.client.force_login(no_access_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:rematch-guests",
                args=[self.checks_required_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_should_return_409_for_closed_accommodation_requests(self):
        user = get_admin_user()
        self.client.force_login(user)

        for ar in self.closed_acc_reqs:
            response = self.client.get(
                reverse("accommodation-requests:rematch-guests", args=[ar.id])
            )

            self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_should_return_409_for_accommodation_requests_without_guests(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:rematch-guests",
                args=[self.no_guests_acc_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_returns_409_for_accommodation_requests_with_only_guests_outside_users_la(
        self,
    ):
        # Guest LA is determined via the guest.accommodation_request LTLA and UTLA names
        # Therefore simulating a guest from a different LA by creating a new guest and
        # AR, where the guest is missing the link to the AR but is in the AR.person_id
        guest = MvPersonFactory(id="person-id", first_name="John", last_name="Doe")
        acc_req = AccReqFactory(
            title="One guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one],
            number_of_people=1,
            person_id=[guest.pk],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
        )

        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:rematch-guests",
                args=[acc_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_returns_409_for_accommodation_requests_with_non_existent_guests(
        self,
    ):
        # Intentionally not using the MvPersonFactory here so that we don't save to
        # the DB. This is testing a scenario we saw in prod where an AR had
        # a FK to a guest, but no guest with that key could be found in the
        # MvPerson table
        guest = MvPerson(id="1234")
        acc_req = AccReqFactory(
            title="Fake guests acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            person_id=[guest.id],
        )

        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:rematch-guests",
                args=[acc_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_select_guests_form_step_appears_if_multiple_guests_on_ar(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": self.multiple_guests_acc_req.id,
                },
            ),
            {
                "within_la": "yes",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "Select guests")

    def test_select_guests_form_step_only_shows_guests_within_users_la(self):
        # Guest LA is determined via the guest.accommodation_request LTLA and UTLA names
        # Therefore simulating a guest from a different LA by creating a new guest and
        # AR, where the guest is missing the link to the AR but is in the AR.person_id
        guest_1 = MvPersonFactory(
            id="person-id-1", first_name="Alice", last_name="Smith"
        )
        guest_2 = MvPersonFactory(id="person-id-2", first_name="Bob", last_name="Brown")
        guest_3 = MvPersonFactory(id="person-id-3", first_name="John", last_name="Doe")
        acc_req = AccReqFactory(
            title="One guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one],
            number_of_people=3,
            person_id=[guest_1.pk, guest_2.pk, guest_3.pk],
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
        )

        guests_within_la = [guest_1, guest_2]
        guests_outside_la = [guest_3]

        for guest in guests_within_la:
            guest.accommodation_request = acc_req
            guest.save()

        user = get_la_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": acc_req.id,
                },
            ),
            {
                "within_la": "yes",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "Select guests")
        for guest in guests_within_la:
            self.assertContains(response, guest.get_full_name())
        for guest in guests_outside_la:
            self.assertNotContains(response, guest.get_full_name())

    def test_select_guests_form_step_is_skipped_if_single_guest_on_ar(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": self.one_guest_acc_req.id,
                },
            ),
            {
                "within_la": "yes",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertNotContains(response, "Select guests")
        self.assertContains(response, "Select accommodation")

    def test_select_accommodation_shows_accommodations_regardless_of_availability(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:rematch-guests-step",
                kwargs={
                    "pk": self.one_guest_acc_req.id,
                    "step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,
                },
            )
            # Sort required due to pagination. Test accommodations
            # have been set up to appear first alphabetically if present.
            + "?sort=full_address"
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "Select accommodation")
        for accommodation in self.accommodations_available_for_rematch:
            self.assertContains(response, accommodation.full_address)
        for accommodation in self.accommodations_not_available_for_rematch:
            self.assertContains(response, accommodation.full_address)

    def test_select_accommodation_form_step_shows_only_accommodations_within_same_ltla(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        same_utla_other_ltla_accommodation = MvAccommodationFactory(
            full_address="accommodation, same utla, different ltla",
            is_available_for_rematch=True,
            ltla_name="OTHER LTLA",
            utla_name=self.utla_name,
        )

        other_utla_accommodation = MvAccommodationFactory(
            full_address="accommodation, different ltla, different utla",
            is_available_for_rematch=True,
            ltla_name="OTHER LTLA",
            utla_name="OTHER UTLA",
        )

        missing_ltla_accommodation = MvAccommodationFactory(
            full_address="accommodation, different ltla, different utla",
            is_available_for_rematch=True,
            ltla_name=None,
            utla_name=self.utla_name,
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:rematch-guests-step",
                kwargs={
                    "pk": self.one_guest_acc_req.id,
                    "step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,
                },
            )
        )
        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "Select accommodation")
        for accommodation in self.accommodations_available_for_rematch:
            self.assertContains(response, accommodation.full_address)

        self.assertNotContains(
            response, same_utla_other_ltla_accommodation.full_address
        )
        self.assertNotContains(response, other_utla_accommodation.full_address)
        self.assertNotContains(response, missing_ltla_accommodation.full_address)

    def test_select_accommodation_form_step_shows_filters(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:rematch-guests-step",
                kwargs={
                    "pk": self.one_guest_acc_req.id,
                    "step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,
                },
            )
        )
        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "Select accommodation")
        self.assertContains(response, "Show filters")

    def test_select_accommodation_form_step_search_filter_works(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:rematch-guests-step",
                kwargs={
                    "pk": self.one_guest_acc_req.id,
                    "step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,
                },
            )
            + "?"
            + urlencode({"search": "one"})
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, self.accommodation_one.full_address)
        self.assertNotContains(response, self.accommodation_two.full_address)
        self.assertNotContains(response, self.accomodation_three.full_address)

    def test_select_accommodation_form_step_temp_accom_filter_works(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:rematch-guests-step",
                kwargs={
                    "pk": self.one_guest_acc_req.id,
                    "step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,
                },
            )
            + "?"
            + urlencode({"show_temporary": "Yes", "show_filters_panel": "True"})
            # Sort required due to pagination. Test accommodations
            # have been set up to appear first alphabetically if present.
            + "&sort=full_address"
        )

        self.assertEqual(response.status_code, http.client.OK)
        for accommodation in self.temporary_accommodations_available_for_rematch:
            self.assertContains(response, accommodation.full_address)
        for accommodation in self.sponsor_accommodations_available_for_rematch:
            self.assertNotContains(response, accommodation.full_address)

        self.assertContains(
            response,
            '<span class="govuk-visually-hidden">Remove this filter</span> Yes</a>',
        )

    def test_select_accommodation_form_step_has_select_button(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:rematch-guests-step",
                kwargs={
                    "pk": self.one_guest_acc_req.id,
                    "step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,
                },
            )
            # Sort required due to pagination. Test accommodations
            # have been set up to appear first alphabetically if present.
            + "?sort=full_address"
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, self.accommodation_one.full_address)
        self.assertContains(
            response,
            '<button type="submit" name="submit" class="govuk-link">Select</button>',
        )

    def test_accommodation_request_is_updated_after_confirmation(self):
        user = get_admin_user()
        self.client.force_login(user)

        first_host = MvVolunteerFactory(id="sponsor-123", is_sponsor=True)
        second_host = MvVolunteerFactory(id="sponsor-456", is_sponsor=True)
        self.accommodation_one.volunteer = first_host
        self.accommodation_one.save()
        self.accommodation_two.volunteer = second_host
        self.accommodation_two.save()

        accommodation_request = AccReqFactory(
            title="One guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            number_of_people=1,
            person_id=[self.guest.pk],
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one.pk],
            ltla_name=[self.ltla_name],
            utla_name=[self.utla_name],
        )

        # View first step
        response = self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.id,
                },
            )
        )
        self.assertContains(
            response, "Is the guest remaining within your local authority?"
        )

        # Submit the first step
        response = self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.pk,
                },
            ),
            {
                "within_la": "yes",
            },
            follow=True,
        )
        self.assertContains(response, "Select accommodation")

        # Submit the second step
        response = self.client.post(
            reverse(
                "accommodation-requests:rematch-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,
                },
            ),
            {
                "select_accommodation-accommodation": self.accommodation_two.pk,
                f"rematch_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,
            },
            follow=True,
        )

        self.assertContains(
            response,
            "Are you sure you want to move John Smith to accommodation two, city b?",
        )

        # Submit the final step
        self.client.post(
            reverse(
                "accommodation-requests:rematch-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": RematchGuestsFormSteps.CONFIRMATION,
                },
            ),
            {
                "confirmation-confirm_guests_moved": "on",
                f"rematch_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": RematchGuestsFormSteps.CONFIRMATION,
            },
            follow=True,
        )

        accommodation_request = MvAccommodationRequest.objects.get(
            pk=accommodation_request.pk
        )
        self.assertEqual(
            accommodation_request.primary_accommodation.pk, self.accommodation_two.pk
        )
        self.assertEqual(accommodation_request.title, "Unknown to accommodation ")
        self.assertEqual(
            accommodation_request.accommodation_id, [self.accommodation_two.pk]
        )
        self.assertEqual(accommodation_request.last_modified_by, user.get_full_name())
        self.assertAlmostEqual(
            accommodation_request.last_modified_at.timestamp(),
            timezone.now().timestamp(),
            delta=1,  # 1 s
        )
        self.assertTrue(accommodation_request.edited_in_app)

        self.assertEqual(
            accommodation_request.primary_sponsor.id,
            self.accommodation_two.volunteer.id,
        )
        self.assertEqual(
            accommodation_request.sponsor_id,
            [self.accommodation_two.volunteer.id],
        )

        # Test that MvInteraction is created
        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=accommodation_request,
            interaction_contact=MvInteraction.InteractionContact.REMATCH_RECORDED,
        ).first()

        self.assertIsNotNone(interaction)
        self.assertEqual(interaction.created_by, user)

    def test_select_accommodation_only_shows_accomm_user_has_permission_for(self):
        user = self.ltla_one_a_user
        self.client.force_login(user)

        self.one_guest_acc_req.ltla_name = [self.ltla_one_a_name]
        self.one_guest_acc_req.utla_name = [self.utla_one_name]
        self.one_guest_acc_req.save()

        # Need to make sure that the AR is correctly linked to the guest so that
        # the user has permissions to access the rematch form
        for guest in self.one_guest_acc_req.get_people():
            guest.accommodation_request = self.one_guest_acc_req
            guest.save()

        self.accommodation_one.ltla_name = self.ltla_one_a_name
        self.accommodation_one.utla_name = self.utla_one_name
        self.accommodation_one.save()

        # Other accommodation must still be in same UTLA otherwise it will already be
        # filtered out based on the page filtering
        self.accommodation_two.ltla_name = self.ltla_one_b_name
        self.accommodation_two.utla_name = self.utla_one_name
        self.accommodation_two.save()

        response = self.client.get(
            reverse(
                "accommodation-requests:rematch-guests-step",
                kwargs={
                    "pk": self.one_guest_acc_req.id,
                    "step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,
                },
            )
        )

        self.assertContains(response, self.accommodation_one.full_address)
        self.assertNotContains(response, self.accommodation_two.full_address)

    def test_accommodation_request_is_updated_after_confirmation_partial(self):
        user = get_admin_user()
        self.client.force_login(user)

        first_host = MvVolunteerFactory(id="sponsor-123", is_sponsor=True)
        second_host = MvVolunteerFactory(id="sponsor-456", is_sponsor=True)
        self.accommodation_one.volunteer = first_host
        self.accommodation_one.save()
        self.accommodation_two.volunteer = second_host
        self.accommodation_two.save()
        group = MvGroupFactory(id="group-123")
        self.guest.group = group
        self.guest.save()
        self.guest_2.group = group
        self.guest_2.save()

        accommodation_request = AccReqFactory(
            title="Two guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            number_of_people=2,
            person_id=[self.guest.pk, self.guest_2.pk],
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one.pk],
            ltla_name=[self.ltla_name],
            utla_name=[self.utla_name],
            group=group,
        )

        # View first step
        response = self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.id,
                },
            )
        )
        self.assertContains(
            response, "Are the guests remaining within your local authority?"
        )

        # Submit the 'staying in LA' step
        response = self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.pk,
                },
            ),
            {
                "within_la": "yes",
            },
            follow=True,
        )
        self.assertContains(response, "Select guests")

        # Submit the 'guests' step
        response = self.client.post(
            reverse(
                "accommodation-requests:rematch-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": RematchGuestsFormSteps.GUESTS,
                },
            ),
            {
                "guests-guests": [self.guest_2.pk],
                f"rematch_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": RematchGuestsFormSteps.GUESTS,
            },
            follow=True,
        )
        self.assertContains(response, "Select accommodation")

        # Submit the 'select accommodation' step
        response = self.client.post(
            reverse(
                "accommodation-requests:rematch-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,
                },
            ),
            {
                "select_accommodation-accommodation": self.accommodation_two.pk,
                f"rematch_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,
            },
            follow=True,
        )

        self.assertContains(
            response,
            "Are you sure you want to move Jane Doe to accommodation two, city b?",
        )

        # Submit the 'confirmation' step
        self.client.post(
            reverse(
                "accommodation-requests:rematch-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": RematchGuestsFormSteps.CONFIRMATION,
                },
            ),
            {
                "confirmation-confirm_guests_moved": "on",
                f"rematch_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": RematchGuestsFormSteps.CONFIRMATION,
            },
            follow=True,
        )

        accommodation_request.refresh_from_db()
        self.guest.refresh_from_db()
        self.guest_2.refresh_from_db()

        # Primary address and accommodation_id is unchanged for partial move
        self.assertEqual(
            accommodation_request.primary_accommodation.pk, self.accommodation_one.pk
        )
        self.assertEqual(
            accommodation_request.accommodation_id, [self.accommodation_one.pk]
        )
        self.assertEqual(accommodation_request.title, "John Smith to accommodation ")
        self.assertEqual(1, accommodation_request.number_of_people)
        self.assertTrue(accommodation_request.edited_in_app)
        self.assertEqual(accommodation_request.group.id, group.id)

        # Check new accommodation request for moved guest
        new_accommodation_request = MvAccommodationRequest.objects.filter(
            title="Jane Doe to accommodation ",
        ).first()
        self.assertNotEqual(new_accommodation_request, None)
        self.assertEqual(new_accommodation_request.title, "Jane Doe to accommodation ")
        self.assertEqual(
            new_accommodation_request.primary_accommodation.pk,
            self.accommodation_two.pk,
        )
        self.assertEqual(
            new_accommodation_request.accommodation_id, [self.accommodation_two.pk]
        )
        self.assertEqual(1, new_accommodation_request.number_of_people)
        self.assertTrue(new_accommodation_request.edited_in_app)
        self.assertEqual(new_accommodation_request.group.id, self.guest_2.group.id)

        self.assertEqual(
            new_accommodation_request.primary_sponsor.id,
            self.accommodation_two.volunteer.id,
        )
        self.assertEqual(
            [self.accommodation_two.volunteer.id], new_accommodation_request.sponsor_id
        )

        # Test that MvInteraction is created
        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=new_accommodation_request,
            interaction_contact=MvInteraction.InteractionContact.REMATCH_RECORDED,
        ).first()

        self.assertIsNotNone(interaction)
        self.assertEqual(interaction.created_by, user)

    def test_ar_status_updates_failed_status_to_pass_due_primary_sponsor_update(self):
        user = get_admin_user()
        self.client.force_login(user)

        first_host = MvVolunteerFactory(id="sponsor-123", is_sponsor=True)
        second_host = MvVolunteerFactory(id="sponsor-456", is_sponsor=True)
        group = MvGroupFactory(id="group-123")

        check_dbs_one = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        check_dbs_two = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        check_acc_exists_one = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        check_acc_exists_two = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        check_acc_suits_one = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        check_acc_suits_two = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        check_gusts_arrived = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.GROUP_ARRIVED),
            check_status=DevCheckV2.CheckStatus.PASSED,
        )

        check_dbs_one.sponsor.set([first_host])
        check_dbs_two.sponsor.set([second_host])

        self.accommodation_one.volunteer = first_host
        self.accommodation_one.save()
        self.accomodation_three.volunteer = second_host
        self.accomodation_three.save()

        accommodation_request = AccReqFactory(
            title="One guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            number_of_people=1,
            person_id=[self.guest.pk],
            primary_sponsor=first_host,
            sponsor_id=[first_host.pk],
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one.pk],
            ltla_name=[self.ltla_name],
            utla_name=[self.utla_name],
            group=group,
        )

        check_acc_exists_one.accommodation.set([self.accommodation_one])
        check_acc_exists_two.accommodation.set([self.accomodation_three])
        check_acc_suits_one.accommodation.set([self.accommodation_one])
        check_acc_suits_two.accommodation.set([self.accomodation_three])
        check_acc_suits_one.AR.set([accommodation_request])
        check_acc_suits_two.AR.set([accommodation_request])
        group.checks.set([check_gusts_arrived])

        accommodation_request.checks_status = (
            accommodation_request.determine_checks_status_from_linked_objects()
        )
        accommodation_request.save()

        self.assertEqual(
            accommodation_request.checks_status,
            MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED,
        )

        # View first step
        self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.id,
                },
            )
        )

        # Submit the first step
        self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.pk,
                },
            ),
            {
                "within_la": "yes",
            },
            follow=True,
        )

        # Submit the second step
        self.client.post(
            reverse(
                "accommodation-requests:rematch-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,
                },
            ),
            {
                "select_accommodation-accommodation": self.accomodation_three.pk,
                f"rematch_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,
            },
            follow=True,
        )

        # Submit the final step
        self.client.post(
            reverse(
                "accommodation-requests:rematch-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": RematchGuestsFormSteps.CONFIRMATION,
                },
            ),
            {
                "confirmation-confirm_guests_moved": "on",
                f"rematch_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": RematchGuestsFormSteps.CONFIRMATION,
            },
            follow=True,
        )

        accommodation_request = MvAccommodationRequest.objects.get(
            pk=accommodation_request.pk
        )

        self.assertEqual(accommodation_request.primary_sponsor.pk, second_host.pk)
        self.assertIn(first_host.pk, accommodation_request.sponsor_id)
        self.assertIn(second_host.pk, accommodation_request.sponsor_id)

        self.assertEqual(
            accommodation_request.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED,
        )

    def test_host_is_not_added_as_sponsor_after_confirmation(self):
        user = get_admin_user()
        self.client.force_login(user)

        first_host = MvVolunteerFactory(id="sponsor-123", is_sponsor=False)
        second_host = MvVolunteerFactory(id="sponsor-456", is_sponsor=False)
        self.accommodation_one.volunteer = first_host
        self.accommodation_one.save()
        self.accommodation_two.volunteer = second_host
        self.accommodation_two.save()

        accommodation_request = AccReqFactory(
            title="One guest acc req",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            number_of_people=1,
            person_id=[self.guest.pk],
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one.pk],
            active_host=first_host,
            sponsor_id=[first_host.id],
            ltla_name=[self.ltla_name],
            utla_name=[self.utla_name],
        )

        # View first step
        response = self.client.get(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.id,
                },
            )
        )
        self.assertContains(
            response, "Is the guest remaining within your local authority?"
        )

        # Submit the first step
        response = self.client.post(
            reverse(
                "accommodation-requests:move-guests",
                kwargs={
                    "pk": accommodation_request.pk,
                },
            ),
            {
                "within_la": "yes",
            },
            follow=True,
        )
        self.assertContains(response, "Select accommodation")

        # Submit the second step
        response = self.client.post(
            reverse(
                "accommodation-requests:rematch-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,
                },
            ),
            {
                "select_accommodation-accommodation": self.accommodation_two.pk,
                f"rematch_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": RematchGuestsFormSteps.SELECT_ACCOMMODATION,
            },
            follow=True,
        )

        self.assertContains(
            response,
            "Are you sure you want to move John Smith to accommodation two, city b?",
        )

        # Submit the final step
        self.client.post(
            reverse(
                "accommodation-requests:rematch-guests-step",
                kwargs={
                    "pk": accommodation_request.pk,
                    "step": RematchGuestsFormSteps.CONFIRMATION,
                },
            ),
            {
                "confirmation-confirm_guests_moved": "on",
                f"rematch_guests_form_wizard_{accommodation_request.pk}"
                f"-current_step": RematchGuestsFormSteps.CONFIRMATION,
            },
            follow=True,
        )

        accommodation_request.refresh_from_db()

        # host changed
        self.assertEqual(accommodation_request.active_host.id, "sponsor-456")

        # sponsor stayed the same
        self.assertEqual(accommodation_request.sponsor_id, ["sponsor-123"])

    def test_get_form_kwargs_handles_none_cleaned_data_does_not_throw(self):
        user = get_admin_user()
        self.client.force_login(user)

        acc_req = self.multiple_guests_acc_req
        response = self.client.get(
            reverse(
                "accommodation-requests:rematch-guests",
                args=[acc_req.id],
            )
        )

        wizard = RematchGuestsFormWizard(
            form_list=RematchGuestsFormWizard.form_list, condition_dict={}
        )
        wizard.request = response.wsgi_request
        wizard.object = acc_req
        wizard.form_list = {
            RematchGuestsFormSteps.GUESTS: MagicMock(),
            RematchGuestsFormSteps.CONFIRMATION: MagicMock(),
        }

        with patch.object(
            RematchGuestsFormWizard,
            "get_cleaned_data_for_step",
            return_value=None,
        ):
            wizard.get_form_kwargs(RematchGuestsFormSteps.CONFIRMATION)
