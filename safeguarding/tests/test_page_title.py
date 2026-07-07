from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import MvPersonFactory, SafeguardingReferralFactory
from user_management.tests.base import get_admin_user


class SafeguardingPageTitlesTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.service_name = settings.SERVICE_NAME
        self.guest = MvPersonFactory(
            first_name="Guest",
            last_name="Person",
        )
        self.referral = SafeguardingReferralFactory(person=self.guest)

        self.guest2 = MvPersonFactory(first_name="Guest")
        self.referral2 = SafeguardingReferralFactory(person=self.guest2)

        self.guest3 = MvPersonFactory(email=["guest1@example.com"])
        self.referral3 = SafeguardingReferralFactory(person=self.guest3)

    def test_safeguarding_detail_tab_titles(self):
        pages_and_titles = [
            (
                "safeguarding:detail-overview",
                f"Escalated checks: GP, Overview - {self.service_name}",
            ),
            (
                "safeguarding:detail-central-safeguarding",
                f"Escalated checks: GP, Central safeguarding - {self.service_name}",
            ),
            (
                "safeguarding:detail-safeguarding-checks",
                f"Escalated checks: GP, Safeguarding checks - {self.service_name}",
            ),
            (
                "safeguarding:detail-linked-records",
                f"Escalated checks: GP, Linked records - {self.service_name}",
            ),
            (
                "safeguarding:detail-properties",
                f"Escalated checks: GP, Properties - {self.service_name}",
            ),
        ]

        user = get_admin_user()
        self.client.force_login(user)

        for view_name, expected_title in pages_and_titles:
            with self.subTest(view_name=view_name):
                response = self.client.get(
                    reverse(
                        view_name,
                        args=[self.guest.pk, self.referral.pk],
                    )
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["TITLE"], expected_title)

    def test_guest_with_missing_surname(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "safeguarding:detail-overview",
                args=[self.guest2.pk, self.referral2.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["TITLE"],
            f"Escalated checks: G, Overview - {self.service_name}",
        )

    def test_guest_with_missing_names(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "safeguarding:detail-overview",
                args=[self.guest3.pk, self.referral3.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["TITLE"],
            f"Escalated checks: Overview - {self.service_name}",
        )
