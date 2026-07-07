import http.client

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import SponsorshipCertificationFormFactory
from user_management.tests.base import get_admin_user


class UAMSPageTitlesTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.service_name = settings.SERVICE_NAME
        self.overview_tab_uam = SponsorshipCertificationFormFactory(
            given_name="Test",
            family_name="User",
        )

        self.overview_tab_uam_no_surname = SponsorshipCertificationFormFactory(
            given_name="Test",
        )

        self.overview_tab_uam_no_names = SponsorshipCertificationFormFactory()

    def test_uam_detail_tab_titles(self):
        pages_and_titles = [
            ("uams:detail-overview", f"UAMs: TU, Overview - {self.service_name}"),
            ("uams:detail-properties", f"UAMs: TU, Properties - {self.service_name}"),
            (
                "uams:detail-linked-records",
                f"UAMs: TU, Linked records - {self.service_name}",
            ),
            ("uams:detail-files", f"UAMs: TU, Files - {self.service_name}"),
        ]

        user = get_admin_user()
        self.client.force_login(user)

        for view_name, expected_title in pages_and_titles:
            with self.subTest(view_name=view_name):
                response = self.client.get(
                    reverse(
                        view_name,
                        args=[self.overview_tab_uam.pk],
                    )
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["TITLE"], expected_title)

    def test_guest_with_missing_surname(self):
        user = get_admin_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "uams:detail-overview",
                kwargs={"pk": self.overview_tab_uam_no_surname.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(
            response.context["TITLE"], f"UAMs: T, Overview - {self.service_name}"
        )

    def test_guest_with_missing_names(self):
        user = get_admin_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "uams:detail-overview", kwargs={"pk": self.overview_tab_uam_no_names.pk}
            )
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(
            response.context["TITLE"], f"UAMs: Overview - {self.service_name}"
        )
