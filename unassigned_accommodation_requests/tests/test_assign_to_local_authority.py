from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import MvAccommodationRequest
from ontology.tests.factories import MvAccommodationRequestFactory as AccReqFactory
from unassigned_accommodation_requests.views import AssignToLocalAuthorityFormSteps
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class AssignToLocalAuthorityFormTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.unassigned_ar = AccReqFactory(
            title="Unassigned record",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )
        self.assigned_ar = AccReqFactory(
            title="Assigned record",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            ltla_name=["some_ltla"],
        )

    def get_form(self, accommodation_request=None):
        url = reverse(
            "unassigned-accommodation-requests:assign-to-local-authority",
            args=[(accommodation_request or self.unassigned_ar).id],
        )
        return self.client.get(url, follow=True)

    def post_region(self, region, accommodation_request=None):
        ar = accommodation_request or self.unassigned_ar
        url = reverse(
            "unassigned-accommodation-requests:assign-to-local-authority-step",
            kwargs={
                "pk": ar.id,
                "step": AssignToLocalAuthorityFormSteps.REGION,
            },
        )
        prefix = f"assign_to_local_authority_form_wizard_{ar.pk}"
        return self.client.post(
            url,
            {
                "region-region": region,
                f"{prefix}-current_step": AssignToLocalAuthorityFormSteps.REGION,
            },
            follow=True,
        )

    def test_admin_users_can_access(self):
        self.client.force_login(get_admin_user())

        self.assertEqual(self.get_form().status_code, 200)

    def test_mhclg_users_can_access(self):
        self.client.force_login(get_mhclg_user())

        self.assertEqual(self.get_form().status_code, 200)

    def test_service_support_users_cannot_access(self):
        self.client.force_login(get_service_support_user())

        self.assertEqual(self.get_form().status_code, 404)

    def test_la_users_cannot_access(self):
        self.client.force_login(get_la_user())

        self.assertEqual(self.get_form().status_code, 404)

    def test_da_users_cannot_access(self):
        self.client.force_login(get_da_user())

        self.assertEqual(self.get_form().status_code, 404)

    def test_ukvi_users_cannot_access(self):
        self.client.force_login(get_ukvi_user())

        self.assertEqual(self.get_form().status_code, 404)

    def test_first_step_asks_for_the_region(self):
        self.client.force_login(get_mhclg_user())

        response = self.get_form()

        self.assertContains(response, "Region")
        self.assertContains(
            response, "You will select a local authority at the next step."
        )

    def test_first_step_offers_the_regions_in_the_same_order_as_reassignment(self):
        self.client.force_login(get_mhclg_user())

        regions = self.get_form().context["form"].fields["region"].choices

        self.assertEqual(
            [region for region, _label in regions],
            ["England", "Scotland", "Northern Ireland", "Wales"],
        )

    def test_first_step_shows_the_record_name(self):
        self.client.force_login(get_mhclg_user())

        response = self.get_form()

        self.assertContains(response, "Assign to local authority for")
        self.assertContains(response, "Unassigned record")

    def test_records_already_assigned_to_a_local_authority_cannot_be_assigned(self):
        self.client.force_login(get_mhclg_user())

        self.assertEqual(self.get_form(self.assigned_ar).status_code, 409)

    def test_records_already_assigned_to_a_local_authority_cannot_be_submitted(self):
        self.client.force_login(get_mhclg_user())

        response = self.post_region("England", self.assigned_ar)

        self.assertEqual(response.status_code, 409)

    def test_a_region_must_be_selected(self):
        self.client.force_login(get_mhclg_user())

        self.assertContains(self.post_region(""), "You must select a region.")

    def test_selecting_a_region_leaves_the_form(self):
        self.client.force_login(get_mhclg_user())

        response = self.post_region("England")

        self.assertRedirects(
            response,
            reverse(
                "accommodation-requests:detail-overview",
                args=[self.unassigned_ar.id],
            ),
        )
