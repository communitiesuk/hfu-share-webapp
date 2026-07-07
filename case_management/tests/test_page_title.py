from django.test import RequestFactory, TestCase
from django.urls import ResolverMatch

from accommodation_requests.views import (
    AccommodationRequestDetailOverviewView,
    AccommodationRequestReopenRequestView,
    AccommodationRequestsListView,
)
from case_management.page_title import (
    apply_record_name,
    apply_section_title,
    apply_service_name,
    apply_tab_title,
    get_section_title,
    get_short_record_name,
    get_tab_title,
    get_title,
    is_home_page,
    slug_to_title,
)


class SlugToTitleTestCase(TestCase):
    def test_slug_to_title(self):
        test_cases = {
            "accessibility-statement": "Accessibility statement",
            "cookies": "Cookies",
            "landing-page": "Landing page",
            "overview": "Overview",
            "properties": "Properties",
            "linked_records": "Linked records",
        }

        for slug, expected_title in test_cases.items():
            with self.subTest(slug=slug):
                self.assertEqual(expected_title, slug_to_title(slug))


class IsHomePageTestCase(TestCase):
    def test_is_home_page_with_landing_page_route(self):
        resolver_match = ResolverMatch(
            route="landing-page",
            func=lambda: None,
            args=(),
            kwargs={},
        )

        self.assertTrue(is_home_page(resolver_match))

    def test_is_home_page_with_other_route(self):
        resolver_match = ResolverMatch(
            route="other-page",
            func=lambda: None,
            args=(),
            kwargs={},
        )

        self.assertFalse(is_home_page(resolver_match))


class GetShortRecordNameTestCase(TestCase):
    def test_get_short_record_name_within_limit(self):
        record_name = "Short Name"
        max_length = 20

        self.assertEqual(record_name, get_short_record_name(record_name, max_length))

    def test_get_short_record_name_exceeding_limit(self):
        record_name = "This is a very long record name that exceeds the limit"
        max_length = 20
        expected_short_name = "This is a very lo..."

        self.assertEqual(
            expected_short_name, get_short_record_name(record_name, max_length)
        )


class GetSectionTitleTestCase(TestCase):
    def test_get_section_title_with_webapp_route(self):
        resolver_match = ResolverMatch(
            route="accessibility-statement",
            func=lambda: None,
            args=(),
            kwargs={},
            app_names=["webapp"],
        )

        self.assertEqual("Accessibility statement", get_section_title(resolver_match))

    def test_get_section_title_with_app_name_non_webapp(self):
        resolver_match = ResolverMatch(
            route="",
            func=lambda: None,
            args=(),
            kwargs={},
            app_names=["accommodation-requests"],
        )

        self.assertEqual("Accommodation requests", get_section_title(resolver_match))

    def test_get_section_title_with_app_name_when_mapped(self):
        resolver_match = ResolverMatch(
            route="",
            func=lambda: None,
            args=(),
            kwargs={},
            app_names=["sponsors"],
        )

        self.assertEqual("Sponsors and hosts", get_section_title(resolver_match))


class ApplySectionTitleTestCase(TestCase):
    def test_apply_section_title_adds_section_title(self):
        resolver_match = ResolverMatch(
            route="accessibility-statement",
            func=lambda: None,
            args=(),
            kwargs={},
            app_names=["webapp"],
        )

        title = "Any title"
        updated_title = apply_section_title(title, resolver_match)

        self.assertEqual(updated_title, "Accessibility statement")

    def test_apply_section_title_no_section_title(self):
        resolver_match = ResolverMatch(
            route="",
            func=lambda: None,
            args=(),
            kwargs={},
            app_names=[""],
        )

        title = "Initial Title"
        updated_title = apply_section_title(title, resolver_match)

        self.assertEqual(updated_title, "Initial Title")


class ApplyTabTitleTestCase(TestCase):
    def test_apply_tab_title_adds_tab_title(self):
        resolver_match = ResolverMatch(
            route="",
            func=AccommodationRequestsListView.as_view(),
            args=(),
            kwargs={},
            app_names=["accommodation-request"],
        )

        title = "Accommodation request"
        title = apply_tab_title(title, resolver_match)

        self.assertEqual("Accommodation request: List view", title)

    def test_apply_tab_title_no_tab_title(self):
        resolver_match = ResolverMatch(
            route="",
            func=AccommodationRequestReopenRequestView.as_view(),
            args=(),
            kwargs={},
            app_names=["accommodation-request"],
        )

        title = apply_tab_title("Accommodation request", resolver_match)

        self.assertEqual("Accommodation request", title)


class GetTabTitleTestCase(TestCase):
    def test_get_tab_title_with_list_view(self):
        resolver_match = ResolverMatch(
            route="",
            func=AccommodationRequestsListView.as_view(),
            args=(),
            kwargs={},
            app_names=["accommodation-request"],
        )

        self.assertEqual("List view", get_tab_title(resolver_match))

    def test_get_tab_title_with_overview_view(self):
        resolver_match = ResolverMatch(
            route="",
            func=AccommodationRequestDetailOverviewView.as_view(),
            args=(),
            kwargs={},
            app_names=["accommodation-request"],
        )

        self.assertEqual("Overview", get_tab_title(resolver_match))

    def test_get_tab_title_with_unmatched_view(self):
        resolver_match = ResolverMatch(
            route="",
            func=AccommodationRequestReopenRequestView.as_view(),
            args=(),
            kwargs={},
            app_names=["accommodation-request"],
        )

        self.assertEqual("", get_tab_title(resolver_match))


class ApplyServiceNameTestCase(TestCase):
    def test_apply_service_name_with_title(self):
        title = "Section Title"
        service_name = "Share Homes for Ukraine data"
        updated_title = apply_service_name(title, service_name)

        self.assertEqual(
            updated_title,
            "Section Title - Share Homes for Ukraine data",
        )

    def test_apply_service_name_without_title(self):
        title = ""
        service_name = "Share Homes for Ukraine data"
        updated_title = apply_service_name(title, service_name)

        self.assertEqual(
            updated_title,
            "Share Homes for Ukraine data",
        )


class ApplyRecordNameTestCase(TestCase):
    def test_apply_record_name_with_record_name(self):
        request = RequestFactory()
        request.record_name = "Lorem ipsum dolor sit amet"
        request.resolver_match = ResolverMatch(
            route="",
            func=lambda: None,
            args=(),
            kwargs={},
            app_names=[""],
        )

        title = "Accommodation request"
        updated_title = apply_record_name(title, request)

        self.assertEqual(
            updated_title,
            "Accommodation request: Lorem ipsum dolor...",
        )

    def test_apply_record_name_without_record_name(self):
        request = RequestFactory()
        request.resolver_match = ResolverMatch(
            route="",
            func=lambda: None,
            args=(),
            kwargs={},
            app_names=[""],
        )

        title = "Accommodation request"

        updated_title = apply_record_name(title, request)

        self.assertEqual(updated_title, "Accommodation request")


class GetTitleTestCase(TestCase):
    def test_get_title_without_resolve_match(self):
        request = RequestFactory()
        request.resolver_match = None

        service_name = "Share Homes for Ukraine data"

        title = get_title(request, service_name)

        self.assertEqual(title, "Share Homes for Ukraine data")

    def test_get_title_home_page(self):
        request = RequestFactory()
        request.resolver_match = ResolverMatch(
            route="landing-page",
            func=lambda: None,
            args=(),
            kwargs={},
            app_names=["webapp"],
        )

        service_name = "Share Homes for Ukraine data"

        title = get_title(request, service_name)

        self.assertEqual(title, "Share Homes for Ukraine data")

    def test_get_title_with_section_title(self):
        request = RequestFactory()
        request.resolver_match = ResolverMatch(
            route="cookies",
            func=lambda: None,
            args=(),
            kwargs={},
            app_names=["webapp"],
        )

        service_name = "Share Homes for Ukraine data"

        title = get_title(request, service_name)

        self.assertEqual(title, "Cookies - Share Homes for Ukraine data")

    def test_get_title_with_no_section_title_applies_only_service_name(self):
        request = RequestFactory()
        request.resolver_match = ResolverMatch(
            route="",
            func=lambda: None,
            args=(),
            kwargs={},
            app_names=[""],
        )

        service_name = "Share Homes for Ukraine data"

        title = get_title(request, service_name)

        self.assertEqual(title, "Share Homes for Ukraine data")

    def test_get_title_with_section_and_list_view_tab_title(self):
        request = RequestFactory()
        request.resolver_match = ResolverMatch(
            route="",
            func=AccommodationRequestsListView.as_view(),
            args=(),
            kwargs={},
            app_names=["accommodation-request"],
        )

        service_name = "Share Homes for Ukraine data"

        title = get_title(request, service_name)

        self.assertEqual(
            title, "Accommodation request: List view - Share Homes for Ukraine data"
        )

    def test_get_title_with_section_and_overview_tab_title(self):
        request = RequestFactory()
        request.resolver_match = ResolverMatch(
            route="",
            func=AccommodationRequestDetailOverviewView.as_view(),
            args=(),
            kwargs={},
            app_names=["accommodation-request"],
        )

        service_name = "Share Homes for Ukraine data"

        title = get_title(request, service_name)

        self.assertEqual(
            title, "Accommodation request: Overview - Share Homes for Ukraine data"
        )

    def test_get_title_with_section_and_unmatched_tab_title(self):
        request = RequestFactory()
        request.resolver_match = ResolverMatch(
            route="",
            func=AccommodationRequestReopenRequestView.as_view(),
            args=(),
            kwargs={},
            app_names=["accommodation-request"],
        )

        service_name = "Share Homes for Ukraine data"

        title = get_title(request, service_name)

        self.assertEqual(title, "Accommodation request - Share Homes for Ukraine data")

    def test_get_title_without_apply_record_name(self):
        request = RequestFactory()
        request.resolver_match = ResolverMatch(
            route="",
            func=AccommodationRequestDetailOverviewView.as_view(),
            args=(),
            kwargs={},
            app_names=["accommodation-request"],
        )

        service_name = "Share Homes for Ukraine data"

        title = get_title(request, service_name)

        self.assertEqual(
            title, "Accommodation request: Overview - Share Homes for Ukraine data"
        )

    def test_get_title_with_section_record_name_and_tab_title(self):
        request = RequestFactory()
        request.record_name = "Lorem ipsum dolor sit amet"
        request.resolver_match = ResolverMatch(
            route="",
            func=AccommodationRequestDetailOverviewView.as_view(),
            args=(),
            kwargs={},
            app_names=["accommodation-request"],
        )

        service_name = "Share Homes for Ukraine data"

        title = get_title(request, service_name)

        self.assertEqual(
            title,
            "Accommodation request: Lorem ipsum dolor..., Overview - "
            "Share Homes for Ukraine data",
        )
