import http.client
from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.base import UamsBaseTestCase, VisaApplicationBaseTestCase
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvPersonFactory,
    MvVolunteerFactory,
)
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
    BaseArchivedModelAdminAccessTest, TestCase
):
    factory = MvAccommodationFactory
    model_url_name = "mvaccommodation"


class ArchivedMvPersonAdminAccessTest(BaseArchivedModelAdminAccessTest, TestCase):
    factory = MvPersonFactory
    model_url_name = "mvperson"


class ArchivedMvVolunteerAdminAccessTest(BaseArchivedModelAdminAccessTest, TestCase):
    factory = MvVolunteerFactory
    model_url_name = "mvvolunteer"
