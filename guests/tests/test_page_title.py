from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import MvPersonFactory as GuestFactory
from user_management.tests.base import get_admin_user


class GuestsPageTitlesTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.guest1 = GuestFactory(
            first_name="John",
            last_name="Doe",
            email=["guest1@example.com"],
            passport_id=["ID123"],
            application_number=["AN123"],
        )
        self.guest2 = GuestFactory(
            first_name="John",
            last_name="",
            email=["guest1@example.com"],
            passport_id=["ID123"],
            application_number=["AN123"],
        )
        self.guest3 = GuestFactory(
            email=["guest1@example.com"],
            passport_id=["ID123"],
            application_number=["AN123"],
        )

    def test_guest_detail_tab_titles(self):
        pages_and_titles = [
            (
                "guests:detail-overview",
                "Guests: JD, Overview - Share Homes for Ukraine data",
            ),
            (
                "guests:detail-actions",
                "Guests: JD, Actions - Share Homes for Ukraine data",
            ),
            (
                "guests:detail-linked-records",
                "Guests: JD, Linked records - Share Homes for Ukraine data",
            ),
            (
                "guests:detail-properties",
                "Guests: JD, Properties - Share Homes for Ukraine data",
            ),
            (
                "guests:detail-history",
                "Guests: JD, History - Share Homes for Ukraine data",
            ),
        ]

        user = get_admin_user()
        self.client.force_login(user)

        for view_name, expected_title in pages_and_titles:
            with self.subTest(view_name=view_name):
                response = self.client.get(
                    reverse(
                        view_name,
                        args=[self.guest1.pk],
                    )
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["TITLE"], expected_title)

    def test_guest_with_missing_surname(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-overview",
                args=[self.guest2.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["TITLE"],
            "Guests: J, Overview - Share Homes for Ukraine data",
        )

    def test_guest_with_missing_names(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-overview",
                args=[self.guest3.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["TITLE"], "Guests: Overview - Share Homes for Ukraine data"
        )
