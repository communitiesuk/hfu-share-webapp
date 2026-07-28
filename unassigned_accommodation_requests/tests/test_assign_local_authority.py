import base64
import hashlib
import re

from django.test import TestCase
from django.urls import reverse

from accounts.enums import GroupType
from accounts.tests.base import TestSessionTokenMixin
from accounts.tests.factories import GroupInfoFactory
from case_management.settings import CONTENT_SECURITY_POLICY
from ontology.models import MvAccommodationRequest
from ontology.tests.factories import MvAccommodationRequestFactory as AccReqFactory
from unassigned_accommodation_requests.views import AssignLocalAuthorityFormSteps
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class AssignLocalAuthorityFormTestCase(TestSessionTokenMixin, TestCase):
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

        self.english_la = GroupInfoFactory(
            group_type=GroupType.LOCAL_AUTHORITY,
            da_name="England",
            is_utla=False,
            ltla_name="English LTLA",
        )
        self.english_utla = GroupInfoFactory(
            group_type=GroupType.LOCAL_AUTHORITY,
            da_name="England",
            is_utla=True,
            utla_name="English UTLA",
        )
        self.welsh_la = GroupInfoFactory(
            group_type=GroupType.LOCAL_AUTHORITY,
            da_name="Wales",
            is_utla=False,
            ltla_name="Welsh LTLA",
        )

    def get_form(self, accommodation_request, query_string=""):
        url = reverse(
            "unassigned-accommodation-requests:assign-local-authority",
            args=[accommodation_request.id],
        )
        return self.client.get(url + query_string, follow=True)

    def post_step(self, accommodation_request, step, data):
        url = reverse(
            "unassigned-accommodation-requests:assign-local-authority-step",
            kwargs={"pk": accommodation_request.id, "step": step},
        )
        prefix = f"assign_local_authority_form_wizard_{accommodation_request.pk}"
        return self.client.post(
            url,
            {**data, f"{prefix}-current_step": step},
            follow=True,
        )

    def post_region(self, accommodation_request, region):
        return self.post_step(
            accommodation_request,
            AssignLocalAuthorityFormSteps.REGION,
            {"region-region": region},
        )

    def post_local_authority(self, accommodation_request, local_authority):
        return self.post_step(
            accommodation_request,
            AssignLocalAuthorityFormSteps.LOCAL_AUTHORITY,
            {"local-authority-local_authority": local_authority},
        )

    def test_admin_users_can_access(self):
        self.client.force_login(get_admin_user())

        self.assertEqual(self.get_form(self.unassigned_ar).status_code, 200)

    def test_mhclg_users_can_access(self):
        self.client.force_login(get_mhclg_user())

        self.assertEqual(self.get_form(self.unassigned_ar).status_code, 200)

    def test_service_support_users_cannot_access(self):
        self.client.force_login(get_service_support_user())

        self.assertEqual(self.get_form(self.unassigned_ar).status_code, 404)

    def test_la_users_cannot_access(self):
        self.client.force_login(get_la_user())

        self.assertEqual(self.get_form(self.unassigned_ar).status_code, 404)

    def test_da_users_cannot_access(self):
        self.client.force_login(get_da_user())

        self.assertEqual(self.get_form(self.unassigned_ar).status_code, 404)

    def test_ukvi_users_cannot_access(self):
        self.client.force_login(get_ukvi_user())

        self.assertEqual(self.get_form(self.unassigned_ar).status_code, 404)

    def test_first_step_asks_for_the_region(self):
        self.client.force_login(get_mhclg_user())

        response = self.get_form(self.unassigned_ar)

        self.assertContains(response, "Select region")
        self.assertContains(
            response, "You will select a local authority at the next step."
        )

    def test_first_step_offers_the_regions_in_the_same_order_as_reassignment(self):
        self.client.force_login(get_mhclg_user())

        response = self.get_form(self.unassigned_ar)
        regions = response.context["form"].fields["region"].choices

        self.assertEqual(
            [region for region, _label in regions],
            ["England", "Scotland", "Northern Ireland", "Wales"],
        )

    def test_first_step_shows_the_record_name(self):
        self.client.force_login(get_mhclg_user())

        response = self.get_form(self.unassigned_ar)

        self.assertContains(response, "Assign local authority for")
        self.assertContains(response, "Unassigned record")

    def test_records_already_assigned_to_a_local_authority_cannot_be_assigned(self):
        self.client.force_login(get_mhclg_user())

        self.assertEqual(self.get_form(self.assigned_ar).status_code, 409)

    def test_records_already_assigned_to_a_local_authority_cannot_be_submitted(self):
        self.client.force_login(get_mhclg_user())

        response = self.post_region(self.assigned_ar, "England")

        self.assertEqual(response.status_code, 409)

    def test_a_region_must_be_selected(self):
        self.client.force_login(get_mhclg_user())

        response = self.post_region(self.unassigned_ar, "")

        self.assertContains(response, "You must select a region.")

    def test_selecting_a_region_leads_to_the_local_authority_step(self):
        self.client.force_login(get_mhclg_user())

        response = self.post_region(self.unassigned_ar, "England")

        self.assertRedirects(
            response,
            reverse(
                "unassigned-accommodation-requests:assign-local-authority-step",
                kwargs={
                    "pk": self.unassigned_ar.id,
                    "step": AssignLocalAuthorityFormSteps.LOCAL_AUTHORITY,
                },
            ),
        )
        self.assertContains(response, "Select local authority")

    def test_local_authority_step_only_offers_las_in_the_selected_region(self):
        self.client.force_login(get_mhclg_user())

        response = self.post_region(self.unassigned_ar, "England")
        local_authorities = response.context["form"].fields["local_authority"].queryset

        self.assertIn(self.english_la, local_authorities)
        self.assertNotIn(self.welsh_la, local_authorities)
        self.assertNotIn(self.english_utla, local_authorities)

    def test_local_authority_search_script_is_allowed_by_the_content_security_policy(
        self,
    ):
        self.client.force_login(get_mhclg_user())

        html = self.post_region(self.unassigned_ar, "England").content.decode()
        scripts = [
            script
            for script in re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
            if "accessibleAutocomplete" in script
        ]

        self.assertEqual(len(scripts), 1)
        digest = base64.b64encode(hashlib.sha256(scripts[0].encode()).digest()).decode()
        self.assertIn(
            f"'sha256-{digest}'",
            CONTENT_SECURITY_POLICY["DIRECTIVES"]["script-src"],
        )

    def test_local_authority_step_labels_las_as_in_the_reassignment_flow(self):
        self.client.force_login(get_mhclg_user())

        response = self.post_region(self.unassigned_ar, "England")

        self.assertContains(response, "English LTLA (LTLA)")

    def test_a_local_authority_must_be_selected(self):
        self.client.force_login(get_mhclg_user())
        self.post_region(self.unassigned_ar, "England")

        response = self.post_local_authority(self.unassigned_ar, "")

        self.assertContains(response, "You must select a local authority.")

    def test_a_local_authority_outside_the_selected_region_is_rejected(self):
        self.client.force_login(get_mhclg_user())
        self.post_region(self.unassigned_ar, "England")

        response = self.post_local_authority(
            self.unassigned_ar, self.welsh_la.ltla_name
        )

        self.assertContains(response, "You must select a local authority.")

    def test_selecting_a_local_authority_leaves_the_form(self):
        self.client.force_login(get_mhclg_user())
        self.post_region(self.unassigned_ar, "England")

        response = self.post_local_authority(
            self.unassigned_ar, self.english_la.ltla_name
        )

        self.assertRedirects(
            response,
            reverse(
                "accommodation-requests:detail-overview",
                args=[self.unassigned_ar.id],
            ),
        )

    def test_re_entering_the_form_with_reset_starts_from_the_region_step(self):
        self.client.force_login(get_mhclg_user())
        self.post_region(self.unassigned_ar, "England")

        response = self.get_form(self.unassigned_ar, query_string="?reset=true")

        self.assertRedirects(
            response,
            reverse(
                "unassigned-accommodation-requests:assign-local-authority-step",
                kwargs={
                    "pk": self.unassigned_ar.id,
                    "step": AssignLocalAuthorityFormSteps.REGION,
                },
            )
            + "?reset=true",
        )
        self.assertIsNone(response.context["form"].initial.get("region"))

    def test_re_entering_the_form_without_reset_keeps_the_answers(self):
        self.client.force_login(get_mhclg_user())
        self.post_region(self.unassigned_ar, "England")

        response = self.get_form(self.unassigned_ar)

        self.assertRedirects(
            response,
            reverse(
                "unassigned-accommodation-requests:assign-local-authority-step",
                kwargs={
                    "pk": self.unassigned_ar.id,
                    "step": AssignLocalAuthorityFormSteps.LOCAL_AUTHORITY,
                },
            ),
        )
