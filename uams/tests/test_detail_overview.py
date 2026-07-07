import http.client
from datetime import datetime, timezone

from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import SponsorshipCertificationForm
from ontology.tests.base import UamsBaseTestCase
from ontology.tests.factories import SponsorshipCertificationFormFactory
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class UamDetailOverviewViewTests(TestSessionTokenMixin, UamsBaseTestCase):
    def setUp(self):
        super().setUp()

        id_type = SponsorshipCertificationForm.IdentificationType.BIOMETRIC_RESIDENCE
        self.overview_tab_uam = SponsorshipCertificationFormFactory(
            given_name="Steven",
            family_name="Davis",
            sponsor_date_of_birth=datetime(1990, 2, 1, tzinfo=timezone.utc),
            email="test@example.com",
            phone_number="1234567890",
            nationality=["Ukrainian"],
            identification_type=id_type,
            identification_number="0987654321",
            residential_postcode="NW5 1TL",
            ltla_name=["Somerset"],
            reference="000000",
            certificate_reference="111111",
            created_at=datetime(2025, 8, 1, tzinfo=timezone.utc),
        )

    def test_renders_correctly(self):
        admin_user = get_admin_user()
        self.client.force_login(admin_user)
        response = self.client.get(
            reverse("uams:detail-overview", kwargs={"pk": self.overview_tab_uam.pk})
        )

        self.assertContains(
            response,
            "Application to sponsor a child record for",
        )
        self.assertContains(
            response,
            "Steven Davis",
        )
        self.assertContains(response, "First name")
        self.assertContains(response, "Steven")
        self.assertContains(response, "Last name")
        self.assertContains(response, "Davis")
        self.assertContains(response, "Date of birth")
        self.assertContains(response, "1 February 1990")
        self.assertContains(response, "Email address")
        self.assertContains(response, "test@example.com")
        self.assertContains(response, "Phone number")
        self.assertContains(response, "1234567890")
        self.assertContains(response, "Nationality")
        self.assertContains(response, "Ukrainian")
        self.assertContains(response, "Identification type")
        self.assertContains(response, "Biometric Residence Permit or Card")
        self.assertContains(response, "Identification number")
        self.assertContains(response, "0987654321")
        self.assertContains(response, "Postcode")
        self.assertContains(response, "NW5 1TL")
        self.assertContains(response, "Local authority")
        self.assertContains(response, "Somerset")
        self.assertContains(response, "Application Number")
        self.assertContains(response, "000000")
        self.assertContains(response, "Child sponsorship approval number")
        self.assertContains(response, "111111")
        self.assertContains(response, "Date created")
        self.assertContains(response, "1 August 2025 at 1:00am")

    def test_user_without_access_to_requested_uam_is_denied_access(self):
        la_user = self.ltla_two_a_user
        self.client.force_login(la_user)
        response = self.client.get(
            reverse("uams:detail-overview", kwargs={"pk": self.ltla_one_a_uam.pk})
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_dev_user_is_granted_access(self):
        user = get_admin_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("uams:detail-overview", kwargs={"pk": self.ltla_one_a_uam.pk})
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_granted_access(self):
        user = self.ltla_one_a_user
        self.client.force_login(user)
        response = self.client.get(
            reverse("uams:detail-overview", kwargs={"pk": self.ltla_one_a_uam.pk})
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_granted_access(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("uams:detail-overview", kwargs={"pk": self.scotland_da_uam.pk})
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_mhclg_user_is_granted_access(self):
        user = get_mhclg_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("uams:detail-overview", kwargs={"pk": self.ltla_one_a_uam.pk})
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_ukvi_user_is_granted_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("uams:detail-overview", kwargs={"pk": self.ltla_one_a_uam.pk})
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_service_support_user_is_granted_access(self):
        user = get_service_support_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("uams:detail-overview", kwargs={"pk": self.ltla_one_a_uam.pk})
        )

        self.assertEqual(response.status_code, http.client.OK)
