from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvPersonFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class GuestsDetailViewsTabsTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.guest = MvPersonFactory(
            pk="person-1",
            first_name="First",
            last_name="Last",
        )

        self.ltla_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["ltla_somerset"],
            person_id=["person-2"],
            number_of_people=1,
        )
        self.ltla_guest = MvPersonFactory(
            pk="person-2",
            first_name="LTLA",
            last_name="Last",
            accommodation_request=self.ltla_accommodation_request,
        )

        self.da_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["Aberdeenshire"],
            utla_name=["Aberdeenshire"],
            person_id=["person-3"],
            number_of_people=1,
        )
        self.da_guest = MvPersonFactory(
            pk="person-3",
            first_name="DA",
            last_name="Last",
            accommodation_request=self.da_accommodation_request,
        )

        self.guest_detail_views_tab_urls = [
            "guests:detail-overview",
            "guests:detail-linked-records",
            "guests:detail-properties",
            "guests:detail-history",
        ]

    def test_on_each_view_all_tabs_render_for_admin_user(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        for tab_url in self.guest_detail_views_tab_urls:
            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.guest.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "History")

    def test_on_each_view_all_tabs_render_for_mhclg_user(
        self,
    ):
        user = get_mhclg_user()
        self.client.force_login(user)

        for tab_url in self.guest_detail_views_tab_urls:
            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.guest.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "History")

    def test_on_each_view_history_tab_does_not_render_for_la_user(
        self,
    ):
        user = get_la_user()
        self.client.force_login(user)

        for tab_url in self.guest_detail_views_tab_urls:
            if tab_url == "guests:detail-history":
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.ltla_guest.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertNotContains(response, "History")

    def test_on_each_view_history_tab_does_not_render_for_da_user(
        self,
    ):
        user = get_da_user()
        self.client.force_login(user)

        for tab_url in self.guest_detail_views_tab_urls:
            if tab_url == "guests:detail-history":
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.da_guest.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertNotContains(response, "History")

    def test_on_each_view_history_tab_does_render_for_ukvi_user(
        self,
    ):
        user = get_ukvi_user()
        self.client.force_login(user)

        for tab_url in self.guest_detail_views_tab_urls:
            if tab_url == "guests:detail-history":
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.guest.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "History")

    def test_on_each_view_history_tab_does_render_for_service_support_user(
        self,
    ):
        user = get_service_support_user()
        self.client.force_login(user)

        for tab_url in self.guest_detail_views_tab_urls:
            if tab_url == "guests:detail-history":
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.guest.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "History")

    def test_on_each_view_actions_tab_does_not_render_for_la_user(
        self,
    ):
        user = get_la_user()
        self.client.force_login(user)

        for tab_url in self.guest_detail_views_tab_urls:
            if tab_url == "guests:detail-actions" or tab_url == "guests:detail-history":
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.ltla_guest.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertNotContains(response, "Actions")

    def test_on_each_view_actions_tab_does_not_render_for_da_user(
        self,
    ):
        user = get_da_user()
        self.client.force_login(user)

        for tab_url in self.guest_detail_views_tab_urls:
            if tab_url == "guests:detail-actions" or tab_url == "guests:detail-history":
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.da_guest.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertNotContains(response, "Actions")

    def test_on_each_view_actions_tab_does_not_render_for_ukvi_user(
        self,
    ):
        user = get_ukvi_user()
        self.client.force_login(user)

        for tab_url in self.guest_detail_views_tab_urls:
            if tab_url == "guests:detail-actions":
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.guest.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertNotContains(response, "Actions")

    def test_on_each_view_actions_tab_does_not_render_for_service_support_user(
        self,
    ):
        user = get_service_support_user()
        self.client.force_login(user)

        for tab_url in self.guest_detail_views_tab_urls:
            if tab_url == "guests:detail-actions":
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.guest.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertNotContains(response, "Actions")
