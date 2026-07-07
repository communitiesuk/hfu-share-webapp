from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import (
    VisaApplicationFactory,
)
from user_management.tests.base import get_admin_user


class VisaApplicationsPageTitlesTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.service_name = settings.SERVICE_NAME

        self.uan = VisaApplicationFactory(
            Q44b_given_name="Test",
            Q44c_family_name="Guest",
        )
        self.uan_no_surname = VisaApplicationFactory(
            Q44b_given_name="Test",
        )
        self.uan_no_name = VisaApplicationFactory()

    def test_visa_applications_detail_tab_titles(self):
        pages_and_titles = [
            (
                "visa-applications:detail-overview",
                f"Visa applications: TG, Overview - {self.service_name}",
            ),
            (
                "visa-applications:detail-properties",
                f"Visa applications: TG, Properties - {self.service_name}",
            ),
            (
                "visa-applications:detail-linked-records",
                f"Visa applications: TG, Linked records - {self.service_name}",
            ),
            (
                "visa-applications:detail-vir",
                f"Visa applications: TG, Visa Information Request - "
                f"{self.service_name}",
            ),
        ]

        user = get_admin_user()
        self.client.force_login(user)

        for view_name, expected_title in pages_and_titles:
            with self.subTest(view_name=view_name):
                response = self.client.get(
                    reverse(
                        view_name,
                        args=[self.uan.pk],
                    ),
                    follow=True,
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["TITLE"], expected_title)

    def test_guest_with_missing_surname(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:detail-overview",
                args=[self.uan_no_surname.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["TITLE"],
            f"Visa applications: T, Overview - {self.service_name}",
        )

    def test_guest_with_missing_names(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "visa-applications:detail-overview",
                args=[self.uan_no_name.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["TITLE"],
            f"Visa applications: Overview - {self.service_name}",
        )
