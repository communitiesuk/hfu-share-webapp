from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class SponsorsDetailViewsTabsTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sponsor = MvVolunteerFactory(
            first_name="Test",
            last_name="Sponsor",
            date_of_birth="2002-06-03",
            sex="Female",
            email="testemail@example.com",
            phone_number=["0123456789"],
            family_situation="Single",
            passport_details=["123456"],
            is_eoi=True,
            is_sponsor=False,
        )

        self.ltla_sponsor = MvVolunteerFactory(
            first_name="LA Sponsor",
            last_name="Spon",
        )
        self.ltla_accommodation = MvAccommodationFactory(
            full_address="Somerset LTLA Address",
            ltla_name="ltla_somerset",
        )
        self.ltla_accommodation.hosts.set([self.ltla_sponsor.id])

        self.da_sponsor = MvVolunteerFactory(
            first_name="DA Sponsor",
            last_name="Spon",
        )
        self.da_accommodation = MvAccommodationFactory(
            full_address="Scotland DA address",
            ltla_name="Aberdeenshire",
            utla_name="Aberdeenshire",
        )
        self.da_accommodation.hosts.set([self.da_sponsor.id])

        self.sponsor_detail_views_tab_urls = [
            "sponsors:detail-overview",
            "sponsors:detail-actions",
            "sponsors:detail-linked-records",
            "sponsors:detail-properties",
            "sponsors:detail-history",
        ]

    def test_on_each_view_all_tabs_render_for_admin_user(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        for tab_url in self.sponsor_detail_views_tab_urls:
            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.sponsor.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "History")

    def test_on_each_view_correct_tabs_render_for_mhclg_user(
        self,
    ):
        user = get_mhclg_user()
        self.client.force_login(user)

        for tab_url in self.sponsor_detail_views_tab_urls:
            if tab_url == "sponsors:detail-actions":
                continue
            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.sponsor.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertNotContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "History")

    def test_on_each_view_correct_tabs_render_for_la_user(
        self,
    ):
        user = get_la_user()
        self.client.force_login(user)

        for tab_url in self.sponsor_detail_views_tab_urls:
            if (
                tab_url == "sponsors:detail-history"
                or tab_url == "sponsors:detail-actions"
            ):
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.ltla_sponsor.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertNotContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "History")

    def test_on_each_view_correct_tabs_render_for_da_user(
        self,
    ):
        user = get_da_user()
        self.client.force_login(user)

        for tab_url in self.sponsor_detail_views_tab_urls:
            if (
                tab_url == "sponsors:detail-history"
                or tab_url == "sponsors:detail-actions"
            ):
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.da_sponsor.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertNotContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "History")

    def test_on_each_view_correct_tabs_render_for_ukvi_user(
        self,
    ):
        user = get_ukvi_user()
        self.client.force_login(user)

        for tab_url in self.sponsor_detail_views_tab_urls:
            if (
                tab_url == "sponsors:detail-history"
                or tab_url == "sponsors:detail-actions"
            ):
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.sponsor.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertNotContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "History")

    def test_on_each_view_correct_tabs_render_for_service_support_user(
        self,
    ):
        user = get_service_support_user()
        self.client.force_login(user)

        for tab_url in self.sponsor_detail_views_tab_urls:
            if (
                tab_url == "sponsors:detail-history"
                or tab_url == "sponsors:detail-actions"
            ):
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.sponsor.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertNotContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "History")
