from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import MvVolunteerFactory
from user_management.tests.base import get_admin_user


class SponsorsPageTitlesTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sponsor = MvVolunteerFactory(
            first_name="Test",
            last_name="Sponsor",
        )
        self.sponsor2 = MvVolunteerFactory(first_name="Test")
        self.sponsor3 = MvVolunteerFactory(email="testemail@example.com")

    def test_sponsor_detail_tab_titles(self):
        pages_and_titles = [
            (
                "sponsors:detail-overview",
                "Sponsors and hosts: TS, Overview - Share Homes for Ukraine data",
            ),
            (
                "sponsors:detail-actions",
                "Sponsors and hosts: TS, Actions - Share Homes for Ukraine data",
            ),
            (
                "sponsors:detail-linked-records",
                "Sponsors and hosts: TS, Linked records - Share Homes for Ukraine data",
            ),
            (
                "sponsors:detail-properties",
                "Sponsors and hosts: TS, Properties - Share Homes for Ukraine data",
            ),
            (
                "sponsors:detail-history",
                "Sponsors and hosts: TS, History - Share Homes for Ukraine data",
            ),
        ]
        user = get_admin_user()
        self.client.force_login(user)

        for view_name, expected_title in pages_and_titles:
            with self.subTest(view_name=view_name):
                response = self.client.get(
                    reverse(
                        view_name,
                        args=[self.sponsor.pk],
                    )
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["TITLE"], expected_title)

    def test_sponsor_with_missing_surname(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor2.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["TITLE"],
            "Sponsors and hosts: T, Overview - Share Homes for Ukraine data",
        )

    def test_sponsor_with_missing_names(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-overview",
                args=[self.sponsor3.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["TITLE"],
            "Sponsors and hosts: Overview - Share Homes for Ukraine data",
        )
