from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import VisaApplicationFactory
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class DeduplicationVisaApplicationListViewTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.visa_application = VisaApplicationFactory(
            title="Test sponsored by Test to Test",
            visa_status="Arrived",
            application_event_datetime=datetime(1999, 11, 11, tzinfo=timezone.utc),
            visa_decision_date=datetime(1999, 11, 11, tzinfo=timezone.utc),
            Q97c_sponsor_name="Test sponsor",
            ltla_name="Test LTLA",
            gwf="Test GWF",
            application_unique_application_number="0000-1111-2222-3333",
        )

    def test_renders_visa_application_list_with_correct_layout(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:visa-applications",
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Name")
        self.assertContains(response, "Visa status")
        self.assertContains(response, "Application date")
        self.assertContains(response, "Decision date")
        self.assertContains(response, "Sponsor name")
        self.assertContains(response, "Local authority")
        self.assertContains(response, "Global web form number (GWF)")
        self.assertContains(response, "Unique application number (UAN)")

    def test_renders_visa_application_list_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:visa-applications",
            )
        )

        self.assertContains(response, self.visa_application.title)
        self.assertContains(response, self.visa_application.visa_status)
        self.assertContains(
            response,
            self.visa_application.application_event_datetime.strftime("%-d %b %Y"),
        )
        self.assertContains(
            response, self.visa_application.visa_decision_date.strftime("%-d %b %Y")
        )
        self.assertContains(response, self.visa_application.Q97c_sponsor_name)
        self.assertContains(response, self.visa_application.ltla_name)
        self.assertContains(response, self.visa_application.gwf)
        self.assertContains(
            response, self.visa_application.application_unique_application_number
        )

    def test_admin_user_can_access_list_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:visa-applications",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_la_user_can_access_list_view(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:visa-applications",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_da_user_can_access_list_view(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:visa-applications",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_mhclg_user_can_access_list_view(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:visa-applications",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_service_support_user_can_access_list_view(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:visa-applications",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_ukvi_user_can_access_list_view(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:visa-applications",
            )
        )

        self.assertEqual(response.status_code, 200)
