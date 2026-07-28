from django.contrib.messages import get_messages
from django.urls import reverse

from accommodation_requests.tests.base import AccommodationRequestsBaseTestCase
from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import MvAccommodationRequestFactory
from user_management.tests.base import get_admin_user


class MultiLABannerMixinTests(TestSessionTokenMixin, AccommodationRequestsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = get_admin_user()
        self.client.force_login(self.user)
        self.multi_la_request = MvAccommodationRequestFactory(
            ltla_name=["LA One", "LA Two"], checks_status="Checks Required"
        )
        self.pk = self.multi_la_request.pk

    def get_banner_messages(self, url_name, pk):
        url = reverse(f"accommodation-requests:{url_name}", args=[pk])
        response = self.client.get(url)
        messages = list(get_messages(response.wsgi_request))
        return [m for m in messages if "linked to multiple local authorities" in str(m)]

    def assert_multi_la_banner(self, url_name):
        assert self.get_banner_messages(url_name, self.pk)

    def test_detail_overview_banner(self):
        self.assert_multi_la_banner("detail-overview")

    def test_detail_safeguarding_checks_banner(self):
        self.assert_multi_la_banner("detail-safeguarding-checks")

    def test_detail_actions_banner(self):
        self.assert_multi_la_banner("detail-actions")

    def test_detail_linked_records_banner(self):
        self.assert_multi_la_banner("detail-linked-records")

    def test_detail_properties_banner(self):
        self.assert_multi_la_banner("detail-properties")

    def test_detail_history_banner(self):
        self.assert_multi_la_banner("detail-history")

    def test_detail_comments_banner(self):
        self.assert_multi_la_banner("detail-comments")

    def test_no_banner_when_ltla_name_empty(self):
        empty_ltla_request = MvAccommodationRequestFactory(
            ltla_name=[], checks_status="Checks Required"
        )
        assert not self.get_banner_messages("detail-overview", empty_ltla_request.pk)

    def test_no_banner_for_single_ltla(self):
        single_ltla_request = MvAccommodationRequestFactory(
            ltla_name=["LA One"], checks_status="Checks Required"
        )
        assert not self.get_banner_messages("detail-overview", single_ltla_request.pk)
