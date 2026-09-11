import http.client
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from django.contrib.admin import AdminSite
from django.db import DatabaseError
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.admin import MvPersonAdmin, MvVolunteerAdmin
from ontology.models import MvPerson, MvVolunteer
from ontology.tests.base import (
    MvPersonBaseTestCase,
    UamsBaseTestCase,
    VisaApplicationBaseTestCase,
)
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvPersonFactory,
    MvVolunteerFactory,
)
from test_utils.base import BaseTestCase
from user_management.tests.base import get_admin_user


class UAMsAdminReadOnlyModelsTestCase(TestSessionTokenMixin, UamsBaseTestCase):
    def test_admin_users_cannot_edit_sponsorship_forms_in_admin_view(self):
        user = get_admin_user()
        user.is_staff = True
        user.is_superuser = True  # Give permissions to view this admin table
        user.save()
        self.client.force_login(user)

        admin_change_url = reverse(
            "admin:ontology_sponsorshipcertificationform_change",
            args=[self.ltla_one_a_uam.pk],
        )
        response = self.client.get(admin_change_url, follow=True)

        self.assertEqual(response.context_data["has_change_permission"], False)
        self.assertContains(response, "<h1>View Uam</h1>")

        # No form submit buttons rendered
        self.assertNotContains(response, "Save")
        self.assertNotContains(response, "Save and add another")
        self.assertNotContains(response, "Save and continue editing")


class VisaApplicationsAdminReadOnlyModelsTestCase(
    TestSessionTokenMixin, VisaApplicationBaseTestCase
):
    def test_admin_users_cannot_edit_visa_applications_in_admin_view(self):
        user = get_admin_user()
        user.is_staff = True
        user.is_superuser = True  # Give permissions to view this admin table
        user.save()
        self.client.force_login(user)

        admin_change_url = reverse(
            "admin:ontology_visaapplication_change",
            args=[self.ltla_one_a_visa_application.pk],
        )

        response = self.client.get(admin_change_url, follow=True)

        self.assertEqual(response.context_data["has_change_permission"], False)
        self.assertContains(response, "<h1>View Visa Application</h1>")

        # No form submit buttons rendered
        self.assertNotContains(response, "Save")
        self.assertNotContains(response, "Save and add another")
        self.assertNotContains(response, "Save and continue editing")


class BaseArchivedModelAdminAccessTest(TestSessionTokenMixin):
    def setUp(self):
        super().setUp()

        self.record = self.factory()
        self.archived_record = self.factory(
            is_archived=True,
            archived_at=datetime(2025, 12, 25, tzinfo=timezone.utc),
        )

    def test_can_see_archived_record_in_changelist(self):
        user = get_admin_user()
        user.is_staff = True
        user.is_superuser = True  # Give permissions to view this admin table
        user.save()
        self.client.force_login(user)

        response = self.client.get(
            reverse(f"admin:ontology_{self.model_url_name}_changelist")
        )

        self.assertEqual(response.status_code, http.client.OK)

        self.assertIn(self.record, response.context["cl"].queryset)
        self.assertIn(self.archived_record, response.context["cl"].queryset)

    def test_can_see_archived_record_change(self):
        user = get_admin_user()
        user.is_staff = True
        user.is_superuser = True  # Give permissions to view this admin table
        user.save()
        self.client.force_login(user)

        # Test for normal record
        response = self.client.get(
            reverse(
                f"admin:ontology_{self.model_url_name}_change", args=[self.record.pk]
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

        # Test for archived record
        response = self.client.get(
            reverse(
                f"admin:ontology_{self.model_url_name}_change",
                args=[self.archived_record.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)


class ArchivedMvAccommodationAdminAccessTest(
    BaseArchivedModelAdminAccessTest, BaseTestCase
):
    factory = MvAccommodationFactory
    model_url_name = "mvaccommodation"


class ArchivedMvPersonAdminAccessTest(BaseArchivedModelAdminAccessTest, BaseTestCase):
    factory = MvPersonFactory
    model_url_name = "mvperson"


class ArchivedMvVolunteerAdminAccessTest(
    BaseArchivedModelAdminAccessTest, BaseTestCase
):
    factory = MvVolunteerFactory
    model_url_name = "mvvolunteer"


class MvPersonAdminReadOnlyModelsTestCase(TestSessionTokenMixin, MvPersonBaseTestCase):
    def test_db_error_on_guest_title_update(self):
        person_admin = MvPersonAdmin(MvPerson, AdminSite())

        with patch(
            "ontology.admin.process_update_guest_titles", side_effect=DatabaseError
        ):
            with patch.object(person_admin, "message_user") as mock_message:
                person_admin.update_guest_titles_action({}, [MvPerson()])

        expected_summary = (
            "Guest title processing complete: "
            "0 updated successfully, "
            "0 already correct (skipped), "
            "1 failed due to errors."
        )
        mock_message.assert_called_once_with({}, expected_summary)


class MvVolunteerAdminActionTestCase(BaseTestCase):
    def setUp(self):
        self.request = Mock()
        self.admin = MvVolunteerAdmin(MvVolunteer, AdminSite())
        self.admin.message_user = Mock()

    def test_redact_personal_information(self):
        queryset = MvVolunteer.objects.none()
        self.admin.redact_personal_information(self.request, queryset)
        self.admin.message_user.assert_called_once_with(
            self.request, "Successfully redacted personal information."
        )

    def test_redact_personal_information_text_fields(self):
        volunteer = MvVolunteerFactory(
            first_name="Jane",
            last_name="Doe",
            full_name="Jane Doe",
            email="jane.doe@example.com",
            family_situation="Single parent with child",
            sex="Female",
        )
        queryset = MvVolunteer.objects.filter(pk=volunteer.pk)
        self.admin.redact_personal_information(self.request, queryset)
        volunteer.refresh_from_db()

        self.assertEqual(volunteer.first_name, "REDACTED")
        self.assertEqual(volunteer.last_name, "REDACTED")
        self.assertEqual(volunteer.full_name, "REDACTED")
        self.assertEqual(volunteer.email, "REDACTED")
        self.assertEqual(volunteer.family_situation, "REDACTED")
        self.assertEqual(volunteer.sex, "REDACTED")

    def test_redact_personal_information_int_and_date_fields(self):
        volunteer = MvVolunteerFactory(
            age=35,
            date_of_birth="1990-01-01",
        )
        queryset = MvVolunteer.objects.filter(pk=volunteer.pk)
        self.admin.redact_personal_information(self.request, queryset)
        volunteer.refresh_from_db()

        self.assertIsNone(volunteer.age)
        self.assertIsNone(volunteer.date_of_birth)

    def test_redact_personal_information_array_fields(self):
        volunteer = MvVolunteerFactory(
            national_identity_card_number=["ID-123456"],
            nationality=["British"],
            other_nationalities=["French"],
            passport_details=["PASS-98765"],
            phone_number=["+447000000000"],
            residential_postcodes=["SW1A 1AA"],
        )
        queryset = MvVolunteer.objects.filter(pk=volunteer.pk)
        self.admin.redact_personal_information(self.request, queryset)
        volunteer.refresh_from_db()

        self.assertIsNone(volunteer.national_identity_card_number)
        self.assertIsNone(volunteer.nationality)
        self.assertIsNone(volunteer.other_nationalities)
        self.assertIsNone(volunteer.passport_details)
        self.assertIsNone(volunteer.phone_number)
        self.assertIsNone(volunteer.residential_postcodes)

    def test_redact_personal_information_preserves_control_fields(self):
        volunteer = MvVolunteerFactory(is_sponsor=True)
        queryset = MvVolunteer.objects.filter(pk=volunteer.pk)
        self.admin.redact_personal_information(self.request, queryset)
        volunteer.refresh_from_db()

        self.assertTrue(volunteer.is_sponsor)
