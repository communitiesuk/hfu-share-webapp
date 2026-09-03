import http.client
from unittest.mock import call, patch

from django.db import DatabaseError
from django.urls import reverse

from accommodation_requests.views import (
    SelectPrimaryAccommodationAndHostSteps,
)
from accounts.tests.base import TestSessionTokenMixin
from ontology.models import MvAccommodationRequest, MvInteraction
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvUkPostcodeFactory,
    MvVolunteerFactory,
)
from test_utils.base import BaseTestCase
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class SelectPrimaryAccommodationAndHostWizardTestCase(
    TestSessionTokenMixin, BaseTestCase
):
    def setUp(self):
        super().setUp()

        self.host_1 = MvVolunteerFactory(first_name="Host", last_name="1")
        self.host_2 = MvVolunteerFactory(first_name="Host", last_name="2")
        self.host_3 = MvVolunteerFactory(first_name="Host", last_name="3")

        self.accommodation_1 = MvAccommodationFactory(
            full_address="Accommodation 1",
        )
        self.accommodation_2 = MvAccommodationFactory(
            full_address="Accommodation 2",
        )
        self.accommodation_2.hosts.set(
            [
                self.host_1,
                self.host_2,
                self.host_3,
            ]
        )
        self.accommodation_2.save()
        self.accommodation_3 = MvAccommodationFactory(
            full_address="Accommodation 3",
        )

        self.ltla_accommodation = MvAccommodationFactory(
            full_address="Somerset LTLA Address",
            ltla_name="ltla_somerset",
        )
        self.da_accommodation = MvAccommodationFactory(
            full_address="Scotland DA address",
            ltla_name="Aberdeenshire",
            utla_name="Aberdeenshire",
        )

        self.accommodation_request = MvAccommodationRequestFactory(
            title="Test Accommodation Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[
                self.accommodation_1.id,
                self.accommodation_2.id,
                self.accommodation_3.id,
            ],
        )
        self.la_accommodation_request = MvAccommodationRequestFactory(
            title="Test Accommodation Request LA",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.ltla_accommodation.id],
            ltla_name=["ltla_somerset"],
        )
        self.da_accommodation_request = MvAccommodationRequestFactory(
            title="Test Accommodation Request DA",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.da_accommodation.id],
            ltla_name=["Aberdeenshire"],
            utla_name=["Aberdeenshire"],
        )

    def test_admin_user_is_allowed_access(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:select-primary",
                args=[self.accommodation_request.pk],
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_allowed_access(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:select-primary",
                args=[self.la_accommodation_request.pk],
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_not_allowed_access_outside_their_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:select-primary",
                args=[self.accommodation_request.pk],
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_da_user_is_allowed_access(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:select-primary",
                args=[self.da_accommodation_request.pk],
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_not_allowed_access_outside_their_da(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:select-primary",
                args=[self.accommodation_request.pk],
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_ukvi_user_is_not_allowed_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:select-primary",
                args=[self.accommodation_request.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_mhclg__user_is_not_allowed_access(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:select-primary",
                args=[self.accommodation_request.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_service_support_user_is_not_allowed_access(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:select-primary",
                args=[self.accommodation_request.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_multi_la_ar_get_returns_409(self):
        user = get_admin_user()
        self.client.force_login(user)

        multi_la_accommodation_request = MvAccommodationRequestFactory(
            title="Multi LA Accommodation Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            ltla_name=["ltla_somerset", "ltla_bristol"],
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:select-primary",
                args=[multi_la_accommodation_request.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_multi_la_ar_post_returns_409(self):
        user = get_admin_user()
        self.client.force_login(user)

        multi_la_accommodation_request = MvAccommodationRequestFactory(
            title="Multi LA Accommodation Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_1.id],
            ltla_name=["ltla_somerset", "ltla_bristol"],
        )

        response = self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": multi_la_accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION,
                },
            ),
            {
                "accommodation-accommodation": self.accommodation_1.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{multi_la_accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION.value
                ),
            },
        )
        self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_confirm_primary_accomodation_page(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION,
                },
            )
        )

        self.assertContains(response, "Confirm current accommodation and host for")
        self.assertContains(response, "Test Accommodation Request")
        self.assertContains(
            response,
            "This is where guests are staying, or will be staying.",
        )
        self.assertContains(response, "Select current accommodation")
        self.assertContains(response, "Accommodation 1")
        self.assertContains(response, "Accommodation 2")
        self.assertContains(response, "Accommodation 3")
        self.assertContains(response, "Confirm and continue")
        self.assertContains(response, "Cancel")

    def test_confirm_primary_accomodation_page_errors(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION,
                },
            ),
            {
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION.value
                ),
            },
            follow=True,
        )

        self.assertContains(response, "There is a problem")
        self.assertContains(response, "Select the current accommodation.")
        self.assertContains(response, "Confirm current accommodation and host for")
        self.assertContains(response, "Test Accommodation Request")
        self.assertContains(response, "Confirm and continue")
        self.assertContains(response, "Cancel")

    def test_confirm_primary_host_page(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION,
                },
            ),
            {
                "accommodation-accommodation": self.accommodation_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION.value
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Confirm current accommodation and host for")
        self.assertContains(response, "Test Accommodation Request")
        self.assertContains(
            response,
            "This is who guests are staying with, or will be staying with.",
        )
        self.assertContains(response, "Select current host")
        self.assertContains(response, "Host 1")
        self.assertContains(response, "Host 2")
        self.assertContains(response, "Host 3")
        self.assertContains(response, "Confirm")
        self.assertContains(response, "Cancel")

    def test_confirm_primary_host_page_errors(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION,
                },
            ),
            {
                "accommodation-accommodation": self.accommodation_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION.value
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.HOST,
                },
            ),
            {
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.HOST.value
                ),
            },
            follow=True,
        )

        self.assertContains(response, "There is a problem")
        self.assertContains(response, "Select the current host.")
        self.assertContains(response, "Confirm current accommodation and host for")
        self.assertContains(response, "Test Accommodation Request")
        self.assertContains(response, "Confirm")
        self.assertContains(response, "Cancel")

    def test_select_primary_host_success(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION,
                },
            ),
            {
                "accommodation-accommodation": self.accommodation_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION.value
                ),
            },
            follow=True,
        )

        response = self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.HOST,
                },
            ),
            {
                "host-host": self.host_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.HOST.value
                ),
            },
            follow=True,
        )

        self.accommodation_request.refresh_from_db()

        self.assertContains(response, "Success")
        self.assertContains(
            response,
            "You confirmed the current accommodation and host for "
            f"{self.accommodation_request.title}.",
        )
        self.assertContains(response, "Accommodation request record for")
        self.assertContains(response, self.accommodation_request.title)

        self.assertEqual(
            self.accommodation_request.primary_accommodation_id, self.accommodation_2.id
        )
        self.assertEqual(self.accommodation_request.active_host_id, self.host_2.id)

    def test_select_primary_host_success_updates_last_modified_fields(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.assertIsNone(self.accommodation_request.last_modified_at)

        self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION,
                },
            ),
            {
                "accommodation-accommodation": self.accommodation_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION.value
                ),
            },
            follow=True,
        )

        self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.HOST,
                },
            ),
            {
                "host-host": self.host_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.HOST.value
                ),
            },
            follow=True,
        )

        self.accommodation_request.refresh_from_db()

        self.assertEqual(
            self.accommodation_request.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )
        self.assertIsNotNone(self.accommodation_request.last_modified_at)
        self.assertEqual(
            self.accommodation_request.last_modified_by, user.get_full_name()
        )
        self.assertEqual(
            self.accommodation_request.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

    def test_select_primary_host_success_updates_postcode_and_title(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.accommodation_2.postcode = MvUkPostcodeFactory(
            postcode="AB1 2CD", postcode_formatted="AB1 2CD"
        )
        self.accommodation_2.save()

        self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION,
                },
            ),
            {
                "accommodation-accommodation": self.accommodation_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION.value
                ),
            },
            follow=True,
        )

        self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.HOST,
                },
            ),
            {
                "host-host": self.host_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.HOST.value
                ),
            },
            follow=True,
        )

        self.accommodation_request.refresh_from_db()

        self.assertEqual(self.accommodation_request.postcode, ["AB1 2CD"])
        self.assertIn("AB1 2CD", self.accommodation_request.title)

    def test_select_primary_host_success_logs_interaction_when_none_previously_set(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION,
                },
            ),
            {
                "accommodation-accommodation": self.accommodation_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION.value
                ),
            },
            follow=True,
        )

        self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.HOST,
                },
            ),
            {
                "host-host": self.host_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.HOST.value
                ),
            },
            follow=True,
        )

        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=self.accommodation_request
        ).first()

        self.assertIsNotNone(interaction)
        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.CURRENT_ACCOMMODATION_AND_HOST_CONFIRMED,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.CURRENT_ACCOMMODATION_AND_HOST_CONFIRMED,
        )
        self.assertEqual(
            interaction.title,
            MvInteraction.InteractionContact.CURRENT_ACCOMMODATION_AND_HOST_CONFIRMED,
        )
        self.assertEqual(
            interaction.interaction_notes,
            "Current accommodation confirmed as Accommodation 2.\n"
            "Current host confirmed as Host 2.",
        )
        self.assertEqual(interaction.created_by, user)

    def test_select_primary_host_success_logs_interaction_when_value_changes(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.accommodation_request.primary_accommodation = self.accommodation_1
        self.accommodation_request.active_host = self.host_1
        self.accommodation_request.save()

        self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION,
                },
            ),
            {
                "accommodation-accommodation": self.accommodation_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION.value
                ),
            },
            follow=True,
        )

        self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.HOST,
                },
            ),
            {
                "host-host": self.host_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.HOST.value
                ),
            },
            follow=True,
        )

        interaction = MvInteraction.objects.filter(
            linked_accommodation_request=self.accommodation_request
        ).first()

        self.assertIsNotNone(interaction)
        self.assertEqual(
            interaction.interaction_notes,
            "Current accommodation confirmed: was Accommodation 1 now "
            "Accommodation 2.\n"
            "Current host confirmed: was Host 1 now Host 2.",
        )

    @patch("sentry_sdk.metrics.count")
    def test_select_primary_host_success_sends_sentry_metric(self, sentry_metrics):
        user = get_admin_user()
        self.client.force_login(user)

        self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION,
                },
            ),
            {
                "accommodation-accommodation": self.accommodation_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION.value
                ),
            },
            follow=True,
        )

        self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.HOST,
                },
            ),
            {
                "host-host": self.host_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.HOST.value
                ),
            },
            follow=True,
        )

        self.assertEqual(sentry_metrics.call_count, 1)
        self.assertEqual(
            sentry_metrics.call_args_list,
            [
                call(
                    "confirm_current_accommodation_and_host.completed",
                    1,
                    attributes={"record_type": "accommodation_request"},
                )
            ],
        )

    def test_select_primary_host_db_error(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION,
                },
            ),
            {
                "accommodation-accommodation": self.accommodation_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION.value
                ),
            },
            follow=True,
        )

        with patch(
            "ontology.models.MvAccommodationRequest.MvAccommodationRequest.save",
            side_effect=DatabaseError,
        ):
            response = self.client.post(
                reverse(
                    "accommodation-requests:select-primary-step",
                    kwargs={
                        "pk": self.accommodation_request.pk,
                        "step": SelectPrimaryAccommodationAndHostSteps.HOST,
                    },
                ),
                {
                    "host-host": self.host_2.id,
                    f"select_primary_accommodation_and_host_wizard_"
                    f"{self.accommodation_request.pk}-current_step": (
                        SelectPrimaryAccommodationAndHostSteps.HOST.value
                    ),
                },
                follow=True,
            )

        self.assertContains(
            response,
            "The current accommodation and host were not confirmed. "
            "If the problem continues raise a support ticket.",
        )

        self.accommodation_request.refresh_from_db()

        self.assertIsNone(self.accommodation_request.primary_accommodation_id)
        self.assertIsNone(self.accommodation_request.active_host_id)
        self.assertEqual(
            self.accommodation_request.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

    @patch("sentry_sdk.metrics.count")
    def test_select_primary_host_db_error_sends_failed_sentry_metric(
        self, sentry_metrics
    ):
        user = get_admin_user()
        self.client.force_login(user)

        self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION,
                },
            ),
            {
                "accommodation-accommodation": self.accommodation_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION.value
                ),
            },
            follow=True,
        )

        with patch(
            "ontology.models.MvAccommodationRequest.MvAccommodationRequest.save",
            side_effect=DatabaseError,
        ):
            self.client.post(
                reverse(
                    "accommodation-requests:select-primary-step",
                    kwargs={
                        "pk": self.accommodation_request.pk,
                        "step": SelectPrimaryAccommodationAndHostSteps.HOST,
                    },
                ),
                {
                    "host-host": self.host_2.id,
                    f"select_primary_accommodation_and_host_wizard_"
                    f"{self.accommodation_request.pk}-current_step": (
                        SelectPrimaryAccommodationAndHostSteps.HOST.value
                    ),
                },
                follow=True,
            )

        sentry_metrics.assert_called_once_with(
            "confirm_current_accommodation_and_host.failed",
            1,
            attributes={"record_type": "accommodation_request"},
        )

    def test_going_to_host_step_too_early_redirects_to_accommodation_step(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.HOST,
                },
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION,
                },
            ),
        )

    def test_re_entering_the_wizard_with_reset_starts_from_the_accommodation_step(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        self.client.post(
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION,
                },
            ),
            {
                "accommodation-accommodation": self.accommodation_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION.value
                ),
            },
            follow=True,
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:select-primary",
                args=[self.accommodation_request.pk],
            )
            + "?reset=true",
        )

        self.assertRedirects(
            response,
            reverse(
                "accommodation-requests:select-primary-step",
                kwargs={
                    "pk": self.accommodation_request.pk,
                    "step": SelectPrimaryAccommodationAndHostSteps.ACCOMMODATION,
                },
            )
            + "?reset=true",
        )

        final_response = self.client.get(response.url)
        self.assertContains(final_response, "Select current accommodation")
