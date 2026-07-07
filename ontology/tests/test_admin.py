from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.base import UamsBaseTestCase, VisaApplicationBaseTestCase
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
