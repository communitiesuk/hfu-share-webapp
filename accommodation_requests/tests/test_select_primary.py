import http.client
from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse

from accommodation_requests.views import (
    SelectPrimaryAccommodationAndHostSteps,
)
from accounts.tests.base import TestSessionTokenMixin
from ontology.models import MvAccommodationRequest
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class AccommodationRequestDetailViewsTabsTestCase(TestSessionTokenMixin, TestCase):
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

        self.assertContains(response, "Confirm current accommodation for")
        self.assertContains(response, "Test Accommodation Request")
        self.assertContains(
            response,
            "This is the current address the guest is living in / "
            "going to be living in",
        )
        self.assertContains(
            response,
            "This may not be the same address as the sponsor or "
            "the address provided on the visa",
        )
        self.assertContains(response, "Select current accommodation")
        self.assertContains(response, "Accommodation 1")
        self.assertContains(response, "Accommodation 2")
        self.assertContains(response, "Accommodation 3")
        self.assertContains(response, "Confirm")

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
        self.assertContains(response, "You must select the current accommodation.")
        self.assertContains(response, "Confirm current accommodation for")
        self.assertContains(response, "Test Accommodation Request")
        self.assertContains(response, "Confirm")

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

        self.assertContains(response, "Confirm current host for")
        self.assertContains(response, "Test Accommodation Request")
        self.assertContains(
            response,
            "This is the current host the guest is living with / "
            "going to be living with",
        )
        self.assertContains(
            response,
            "This may not be the same person as the named sponsor",
        )
        self.assertContains(response, "Select current host")
        self.assertContains(response, "Host 1")
        self.assertContains(response, "Host 2")
        self.assertContains(response, "Host 3")
        self.assertContains(response, "Confirm")

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
        self.assertContains(response, "You must select the current host.")
        self.assertContains(response, "Confirm current host for")
        self.assertContains(response, "Test Accommodation Request")
        self.assertContains(response, "Confirm")

    def test_select_primary_host_success(self):
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
                "host-host": self.host_2.id,
                f"select_primary_accommodation_and_host_wizard_"
                f"{self.accommodation_request.pk}-current_step": (
                    SelectPrimaryAccommodationAndHostSteps.HOST.value
                ),
            },
            follow=True,
        )

        self.assertContains(response, "Success")
        self.assertContains(
            response,
            "You confirmed the current accommodation and host for "
            "Test Accommodation Request",
        )
        self.assertContains(response, "Accommodation request record for")
        self.assertContains(response, "Test Accommodation Request")

        self.accommodation_request.refresh_from_db()

        self.assertEqual(
            self.accommodation_request.primary_accommodation_id, self.accommodation_2.id
        )
        self.assertEqual(self.accommodation_request.active_host_id, self.host_2.id)
        self.assertEqual(
            self.accommodation_request.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
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

    # TODO: Add tests for logging
    # TODO: Add test for trying to go to the host page too early
