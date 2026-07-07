from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import MvAccommodationRequest
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class AccommodationRequestDetailViewsTabsTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.accommodation_request = MvAccommodationRequestFactory(
            title="Test Accommodation Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

        self.ltla_accommodation_request = MvAccommodationRequestFactory(
            title="LTLA Accommodation Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            ltla_name=["ltla_somerset"],
        )

        self.da_accommodation_request = MvAccommodationRequestFactory(
            title="LTLA Accommodation Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            ltla_name=["Aberdeenshire"],
            utla_name=["Aberdeenshire"],
        )

        self.accommodation_request_detail_views_tab_urls = [
            "accommodation-requests:detail-overview",
            "accommodation-requests:detail-safeguarding-checks",
            "accommodation-requests:detail-actions",
            "accommodation-requests:detail-linked-records",
            "accommodation-requests:detail-properties",
            "accommodation-requests:detail-comments",
            "accommodation-requests:detail-history",
        ]

    def test_on_each_view_all_tabs_render_for_admin_user(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        for tab_url in self.accommodation_request_detail_views_tab_urls:
            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.accommodation_request.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Safeguarding checks")
            self.assertContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "Comments")
            self.assertContains(response, "History")

    def test_on_each_view_all_tabs_render_for_mhclg_user(
        self,
    ):
        user = get_mhclg_user()
        self.client.force_login(user)

        for tab_url in self.accommodation_request_detail_views_tab_urls:
            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.accommodation_request.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Safeguarding checks")
            self.assertContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "Comments")
            self.assertContains(response, "History")

    def test_on_each_view_history_tab_does_render_for_la_user(
        self,
    ):
        user = get_la_user()
        self.client.force_login(user)

        for tab_url in self.accommodation_request_detail_views_tab_urls:
            if tab_url == "accommodation-requests:detail-history":
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.ltla_accommodation_request.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Safeguarding checks")
            self.assertContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "Comments")
            self.assertContains(response, "History")

    def test_on_each_view_history_tab_does_render_for_da_user(
        self,
    ):
        user = get_da_user()
        self.client.force_login(user)

        for tab_url in self.accommodation_request_detail_views_tab_urls:
            if tab_url == "accommodation-requests:detail-history":
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.da_accommodation_request.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Safeguarding checks")
            self.assertContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "Comments")
            self.assertContains(response, "History")

    def test_on_each_view_history_tab_does_render_for_ukvi_user(
        self,
    ):
        user = get_ukvi_user()
        self.client.force_login(user)

        for tab_url in self.accommodation_request_detail_views_tab_urls:
            if (
                tab_url == "accommodation-requests:detail-history"
                or tab_url == "accommodation-requests:detail-actions"
            ):
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.accommodation_request.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Safeguarding checks")
            self.assertNotContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "Comments")
            self.assertContains(response, "History")

    def test_on_each_view_history_tab_does_render_for_service_support_user(
        self,
    ):
        user = get_service_support_user()
        self.client.force_login(user)

        for tab_url in self.accommodation_request_detail_views_tab_urls:
            if tab_url == "accommodation-requests:detail-history":
                continue

            response = self.client.get(
                reverse(
                    tab_url,
                    args=[self.accommodation_request.pk],
                )
            )

            self.assertContains(response, "Overview")
            self.assertContains(response, "Safeguarding checks")
            self.assertContains(response, "Actions")
            self.assertContains(response, "Linked records")
            self.assertContains(response, "Properties")
            self.assertContains(response, "Comments")
            self.assertContains(response, "History")
