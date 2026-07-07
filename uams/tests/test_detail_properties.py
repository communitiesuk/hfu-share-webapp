import http.client
from datetime import datetime, timezone

from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import SponsorshipCertificationForm
from ontology.tests.base import UamsBaseTestCase
from ontology.tests.factories import (
    SponsorshipCertificationFormFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class UamDetailPropertiesViewTests(TestSessionTokenMixin, UamsBaseTestCase):
    def setUp(self):
        super().setUp()

        id_type = SponsorshipCertificationForm.IdentificationType.BIOMETRIC_RESIDENCE
        self.properties_tab_uam = SponsorshipCertificationFormFactory(
            # sponsor_details
            given_name="Steven",
            family_name="Davis",
            has_other_names=False,
            other_names=["Other Name"],
            sponsor_date_of_birth=datetime(1990, 2, 1, tzinfo=timezone.utc),
            different_address=False,
            nationality=["British"],
            has_other_nationalities=False,
            identification_type=id_type,
            identification_number="0987654321",
            email="test@example.com",
            phone_number="1234567890",
            sponsor_declaration="I do declare!",
            # cohabitant_details
            cohabitant_given_name=["John"],
            cohabitant_family_name=["Doe"],
            cohabitant_date_of_birth=["1985-05-15"],
            cohabitant_nationality=["Ukrainian"],
            cohabitant_id=["1234567890"],
            cohabitant_id_type_and_number=["Passport 1234567890"],
            # accommodation_details
            residential_line_1="123 Main St",
            residential_line_2="Apt 4B",
            residential_postcode="NW5 1TL",
            residential_town="Somerset",
            ltla_name=["ltla_somerset"],
            # child_guest_details
            minor_contact_type=["Email"],
            minor_date_of_birth=datetime(2015, 1, 1),
            minor_email="jane.doe@example.com",
            minor_family_name="Doe",
            minor_given_name="Jane",
            minor_phone_number="0987654321",
            # reference_details
            reference="000000",
            certificate_reference="111111",
            created_at=datetime(2025, 8, 1, tzinfo=timezone.utc),
            started_at=datetime(2025, 7, 1, tzinfo=timezone.utc),
            notification_sent=True,
            notification_timestamp=datetime(2025, 8, 1, tzinfo=timezone.utc),
            ingestion_time=datetime(2025, 8, 1, tzinfo=timezone.utc),
            notional_data=False,
            viewer_group_names=["group1", "group2"],
            # parental_consent_details
            has_parental_consent=True,
            uk_parental_consent_file_type="application/pdf",
            uk_parental_consent_filename="uk_parental_consent.pdf",
            uk_parental_consent_saved_filename="uk_parental_consent_saved.pdf",
            uk_parental_consent_file_size=100001,
            ukraine_parental_consent_file_type="application/xpdf",
            ukraine_parental_consent_filename="ukraine_parental_consent.pdf",
            ukraine_parental_consent_saved_filename=(
                "ukraine_parental_consent_saved.pdf"
            ),
            ukraine_parental_consent_file_size=200002,
            # qualifying_details
            is_under_18=True,
            is_living_december=True,
            is_unaccompanied=False,
            is_committed=False,
            is_consent=True,
            is_permitted=True,
        )

    def test_dev_user_is_granted_access(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-properties",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_user_without_access_to_requested_uam_is_denied_access(self):
        la_user = self.ltla_two_a_user
        self.client.force_login(la_user)

        response = self.client.get(
            reverse(
                "uams:detail-properties",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_la_user_is_granted_access(self):
        user = self.ltla_one_a_user
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-properties",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_granted_access(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-properties",
                kwargs={"pk": self.scotland_da_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_mhclg_user_is_granted_access(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-properties",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_ukvi_user_is_granted_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-properties",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_service_support_user_is_granted_access(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-properties",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_renders_properties_headings_correctly(self):
        admin_user = get_admin_user()
        self.client.force_login(admin_user)

        response = self.client.get(
            reverse(
                "uams:detail-properties",
                kwargs={"pk": self.properties_tab_uam.pk},
            )
        )

        # Check headings
        self.assertContains(response, "Sponsor details")
        self.assertContains(response, "Over 16s at the accommodation")
        self.assertContains(response, "Accommodation")
        self.assertContains(response, "Child guest")
        self.assertContains(response, "Reference numbers and key details")
        self.assertContains(response, "Parental consent")
        self.assertContains(response, "Qualifying details")

    def test_renders_sponsor_details_correctly(self):
        admin_user = get_admin_user()
        self.client.force_login(admin_user)

        response = self.client.get(
            reverse(
                "uams:detail-properties",
                kwargs={"pk": self.properties_tab_uam.pk},
            )
        )

        # given_name
        self.assertContains(response, "Steven")
        # family_name
        self.assertContains(response, "Davis")
        # sponsor_date_of_birth
        self.assertContains(response, "1 February 1990")
        # nationality
        self.assertContains(response, "British")
        # identification_type
        self.assertContains(response, "Biometric Residence Permit or Card")
        # identification_number
        self.assertContains(response, "0987654321")
        # email
        self.assertContains(response, "test@example.com")
        # phone_number
        self.assertContains(response, "1234567890")
        # sponsor_declaration
        self.assertContains(response, "I do declare!")

    def test_renders_cohabitant_details_correctly(self):
        admin_user = get_admin_user()
        self.client.force_login(admin_user)

        response = self.client.get(
            reverse(
                "uams:detail-properties",
                kwargs={"pk": self.properties_tab_uam.pk},
            )
        )

        # cohabitant_given_name
        self.assertContains(response, "John")
        # cohabitant_family_name
        self.assertContains(response, "Doe")
        # cohabitant_date_of_birth
        self.assertContains(response, "1985-05-15")
        # cohabitant_nationality
        self.assertContains(response, "Ukrainian")
        # cohabitant_id_type_and_number
        self.assertContains(response, "Passport 1234567890")

    def test_renders_accommodation_details_correctly(self):
        admin_user = get_admin_user()
        self.client.force_login(admin_user)

        response = self.client.get(
            reverse(
                "uams:detail-properties",
                kwargs={"pk": self.properties_tab_uam.pk},
            )
        )

        # residential_line_1
        self.assertContains(response, "123 Main St")
        # residential_line_2
        self.assertContains(response, "Apt 4B")
        # residential_postcode
        self.assertContains(response, "NW5 1TL")
        # residential_town
        self.assertContains(response, "Somerset")
        # ltla_name
        self.assertContains(response, "ltla_somerset")

    def test_renders_child_guest_details_correctly(self):
        admin_user = get_admin_user()
        self.client.force_login(admin_user)

        response = self.client.get(
            reverse(
                "uams:detail-properties",
                kwargs={"pk": self.properties_tab_uam.pk},
            )
        )

        # minor_contact_type
        self.assertContains(response, "Email")
        # minor_date_of_birth
        self.assertContains(response, "1 January 2015")
        # minor_email
        self.assertContains(response, "jane.doe@example.com")
        # minor_given_name
        self.assertContains(response, "Jane")
        # minor_phone_number
        self.assertContains(response, "0987654321")

    def test_renders_reference_details_correctly(self):
        admin_user = get_admin_user()
        self.client.force_login(admin_user)

        response = self.client.get(
            reverse(
                "uams:detail-properties",
                kwargs={"pk": self.properties_tab_uam.pk},
            )
        )

        # reference
        self.assertContains(response, "000000")
        # certificate_reference
        self.assertContains(response, "111111")
        # created_at
        self.assertContains(response, "1 August 2025")
        # started_at
        self.assertContains(response, "1 July 2025")
        # viewer_group_names
        self.assertContains(response, "group1")
        self.assertContains(response, "group2")

    def test_renders_parental_consent_details_correctly(self):
        admin_user = get_admin_user()
        self.client.force_login(admin_user)

        response = self.client.get(
            reverse(
                "uams:detail-properties",
                kwargs={"pk": self.properties_tab_uam.pk},
            )
        )

        # uk parental file details
        self.assertContains(response, "application/pdf")
        self.assertContains(response, "uk_parental_consent.pdf")
        self.assertContains(response, "uk_parental_consent_saved.pdf")
        self.assertContains(response, "100001")
        # ukraine parental file details
        self.assertContains(response, "application/xpdf")
        self.assertContains(response, "ukraine_parental_consent.pdf")
        self.assertContains(response, "ukraine_parental_consent_saved.pdf")
        self.assertContains(response, "200002")
