from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import (
    MvAccommodationFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class AccommodationDetailViewsTabsTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.accommodation = MvAccommodationFactory(
            full_address="123 Street",
            ltla_name="ltla_somerset",
        )
        self.ltla_accommodation = MvAccommodationFactory(
            full_address="Somerset LTLA Address",
            ltla_name="ltla_somerset",
        )
        self.da_accommodation = MvAccommodationFactory(
            full_address="Scotland DA address",
            ltla_name="Aberdeenshire",
            utla_name="Aberdeenshire",
        )

        self.accommodation_detail_views_tab_urls = [
            "accommodations:detail-overview",
            "accommodations:detail-actions",
            "accommodations:detail-linked-records",
            "accommodations:detail-properties",
            "accommodations:detail-history",
        ]

    def test_on_each_view_all_tabs_render_for_admin_user(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        for tab_url in self.accommodation_detail_views_tab_urls:
            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.accommodation.pk],
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

        for tab_url in self.accommodation_detail_views_tab_urls:
            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.accommodation.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "History")

    def test_on_each_view_correct_tabs_render_for_la_user(
        self,
    ):
        user = get_la_user()
        self.client.force_login(user)

        for tab_url in self.accommodation_detail_views_tab_urls:
            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.ltla_accommodation.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "History")

    def test_on_each_view_correct_tabs_render_for_da_user(
        self,
    ):
        user = get_da_user()
        self.client.force_login(user)

        for tab_url in self.accommodation_detail_views_tab_urls:
            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.da_accommodation.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "History")

    def test_on_each_view_correct_tabs_render_for_ukvi_user(
        self,
    ):
        user = get_ukvi_user()
        self.client.force_login(user)

        for tab_url in self.accommodation_detail_views_tab_urls:
            if tab_url == "accommodations:detail-actions":
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.accommodation.pk],
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

        for tab_url in self.accommodation_detail_views_tab_urls:
            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.accommodation.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "History")
