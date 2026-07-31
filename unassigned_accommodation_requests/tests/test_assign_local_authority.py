import base64
import hashlib
import re
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from accounts.enums import GroupType
from accounts.models import GroupInfo
from accounts.tests.base import TestSessionTokenMixin
from accounts.tests.factories import GroupInfoFactory
from case_management.settings import CONTENT_SECURITY_POLICY
from ontology.models import MvAccommodation, MvAccommodationRequest
from ontology.tests.factories import MvAccommodationFactory, VisaApplicationFactory
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

        self.english_la = GroupInfo.objects.get(ltla_name="Boston", is_utla=False)
        self.english_utla = GroupInfo.objects.get(
            utla_name="Lincolnshire", is_utla=True
        )
        self.welsh_la = GroupInfo.objects.get(ltla_name="Cardiff", is_utla=False)

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

    def link_records_to(
        self,
        accommodation_request,
        application_numbers=("1313-0000-0133-4633", "1313-8241-0067-9315"),
        accommodation_count=2,
    ):
        accommodations = [MvAccommodationFactory() for _ in range(accommodation_count)]

        *listed_accommodations, primary_accommodation = accommodations
        accommodation_request.accommodation_id = [
            accommodation.id for accommodation in listed_accommodations
        ]
        accommodation_request.primary_accommodation = primary_accommodation
        accommodation_request.unique_application_number = list(application_numbers)
        accommodation_request.save()

        visa_applications = [
            VisaApplicationFactory(application_unique_application_number=number)
            for number in application_numbers
        ]

        return accommodations, visa_applications

    def complete_form(self, accommodation_request, local_authority):
        self.post_region(accommodation_request, local_authority.da_name)
        return self.post_local_authority(
            accommodation_request, local_authority.ltla_name
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

        self.assertContains(response, "Boston (LTLA)")

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

    def test_completing_the_form_assigns_the_local_authority_to_the_record(self):
        self.client.force_login(get_mhclg_user())

        self.complete_form(self.unassigned_ar, self.english_la)

        self.unassigned_ar.refresh_from_db()
        self.assertEqual(self.unassigned_ar.ltla_name, ["Boston"])
        self.assertEqual(self.unassigned_ar.utla_name, ["Lincolnshire"])

    def test_completing_the_form_assigns_the_local_authority_to_the_accommodations(
        self,
    ):
        self.client.force_login(get_mhclg_user())
        accommodations, _visa_applications = self.link_records_to(self.unassigned_ar)

        self.complete_form(self.unassigned_ar, self.english_la)

        for accommodation in accommodations:
            accommodation.refresh_from_db()
            self.assertEqual(accommodation.ltla_name, "Boston")
            self.assertEqual(accommodation.utla_name, "Lincolnshire")

    def test_completing_the_form_assigns_the_local_authority_to_the_visa_applications(
        self,
    ):
        self.client.force_login(get_mhclg_user())
        _accommodations, visa_applications = self.link_records_to(self.unassigned_ar)

        self.complete_form(self.unassigned_ar, self.english_la)

        for visa_application in visa_applications:
            visa_application.refresh_from_db()
            self.assertEqual(visa_application.ltla_name, "Boston")
            self.assertEqual(visa_application.utla_name, "Lincolnshire")
            self.assertEqual(visa_application.country, "England")

    def test_completing_the_form_assigns_every_unassigned_related_record(self):
        self.client.force_login(get_mhclg_user())
        accommodations, visa_applications = self.link_records_to(
            self.unassigned_ar,
            application_numbers=(
                "1313-0000-0133-4633",
                "1313-8241-0067-9315",
                "1313-2947-1105-7360",
            ),
            accommodation_count=3,
        )
        for record in accommodations + visa_applications:
            self.assertIsNone(record.ltla_name)
            self.assertIsNone(record.utla_name)

        self.complete_form(self.unassigned_ar, self.english_la)

        for record in accommodations + visa_applications:
            record.refresh_from_db()
            self.assertEqual(record.ltla_name, "Boston")
            self.assertEqual(record.utla_name, "Lincolnshire")

    def test_completing_the_form_makes_locked_accommodations_editable_and_assigns_them(
        self,
    ):
        self.client.force_login(get_mhclg_user())
        accommodations, _visa_applications = self.link_records_to(self.unassigned_ar)
        MvAccommodation.objects.filter(
            id__in=[accommodation.id for accommodation in accommodations]
        ).update(is_editable=False)

        self.complete_form(self.unassigned_ar, self.english_la)

        for accommodation in accommodations:
            accommodation.refresh_from_db()
            self.assertTrue(accommodation.is_editable)
            self.assertEqual(accommodation.ltla_name, "Boston")
            self.assertEqual(accommodation.utla_name, "Lincolnshire")

    def test_completing_the_form_leaves_the_utla_empty_when_the_la_has_no_parent_utla(
        self,
    ):
        self.client.force_login(get_mhclg_user())
        la_without_utla = GroupInfoFactory(
            group_type=GroupType.LOCAL_AUTHORITY,
            da_name="England",
            is_utla=False,
            ltla_name="Orphan LTLA",
        )
        _accommodations, visa_applications = self.link_records_to(self.unassigned_ar)

        self.complete_form(self.unassigned_ar, la_without_utla)

        self.unassigned_ar.refresh_from_db()
        self.assertEqual(self.unassigned_ar.ltla_name, ["Orphan LTLA"])
        self.assertEqual(self.unassigned_ar.utla_name, [])
        for visa_application in visa_applications:
            visa_application.refresh_from_db()
            self.assertIsNone(visa_application.utla_name)

    def test_completing_the_form_leaves_records_of_other_requests_alone(self):
        self.client.force_login(get_mhclg_user())
        other_accommodations, other_visa_applications = self.link_records_to(
            AccReqFactory(title="Another record"),
            application_numbers=("1313-5079-3312-6408", "1313-6634-8850-1729"),
        )
        self.link_records_to(self.unassigned_ar)

        self.complete_form(self.unassigned_ar, self.english_la)

        for record in other_accommodations + other_visa_applications:
            record.refresh_from_db()
            self.assertIsNone(record.ltla_name)
            self.assertIsNone(record.utla_name)

    def test_users_without_access_cannot_submit_the_form(self):
        self.client.force_login(get_la_user())
        accommodations, visa_applications = self.link_records_to(self.unassigned_ar)

        response = self.complete_form(self.unassigned_ar, self.english_la)

        self.assertEqual(response.status_code, 404)
        self.unassigned_ar.refresh_from_db()
        self.assertIsNone(self.unassigned_ar.ltla_name)
        for record in accommodations + visa_applications:
            record.refresh_from_db()
            self.assertIsNone(record.ltla_name)
            self.assertIsNone(record.utla_name)

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

    @mock.patch("ontology.models.MvAccommodationRequest.sentry_sdk.metrics.count")
    def test_completing_the_form_sends_a_sentry_metric(self, sentry_metrics):
        user = get_mhclg_user()
        self.client.force_login(user)

        self.complete_form(self.unassigned_ar, self.english_la)

        sentry_metrics.assert_called_once_with(
            "accommodation_request.assigned_local_authority",
            1,
            attributes={"ltla_name": "Boston", "user_id": user.id},
        )

    @mock.patch("ontology.models.MvAccommodationRequest.log_event")
    def test_completing_the_form_logs_the_assignment_event(self, mock_log_event):
        user = get_mhclg_user()
        self.client.force_login(user)

        self.complete_form(self.unassigned_ar, self.english_la)

        mock_log_event.assert_called_once_with(
            "assign_local_authority: unassigned accommodation request assigned",
            ar_pk=self.unassigned_ar.pk,
            ltla_name="Boston",
            user_pk=user.pk,
        )

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
