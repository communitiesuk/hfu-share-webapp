from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.test import RequestFactory
from django.views.generic import DetailView

from test_utils.base import BaseTestCase
from webapp.mixins import DetailViewMixin


class DetailViewMixinTestView(DetailViewMixin, DetailView):  # pylint: disable=W1351
    namespace = "test-app"
    singular_name = "Test record"
    plural_name = "Test records"

    @property
    def views_for_record(self):
        return (
            TestOverviewView,
            TestLinkedRecordsView,
            TestPropertiesView,
            TestActionsView,
        )

    def should_show_tab_for_user(self, view_name: str) -> bool:
        return view_name != "actions"


class TestOverviewView(DetailViewMixinTestView):  # pylint: disable=W1351
    view_name = "overview"

    @property
    def page_heading(self):
        return "Overview heading"


class TestLinkedRecordsView(DetailViewMixinTestView):  # pylint: disable=W1351
    view_name = "linked-records"

    @property
    def page_heading(self):
        return "Linked records heading"


class TestPropertiesView(DetailViewMixinTestView):  # pylint: disable=W1351
    view_name = "properties"

    @property
    def page_heading(self):
        return "Properties heading"


class TestActionsView(DetailViewMixinTestView):  # pylint: disable=W1351
    view_name = "actions"

    @property
    def page_heading(self):
        return "Actions heading"


class DetailViewMixinTests(BaseTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.object = SimpleNamespace(id=123, title="Test record")

    def setup_test_view_class(self, view_cls):
        view = view_cls()
        view.request = self.request
        view.object = self.object
        view.kwargs = {}

        return view

    def test_unexpected_tab_raises_error(
        self,
    ):
        view = self.setup_test_view_class(TestOverviewView)

        with self.assertRaisesRegex(
            ImproperlyConfigured, "No tab text exists for 'not-valid-tab'"
        ):
            view.get_tab_text("not-valid-tab")

    def test_get_template_names_uses_namespaced_template_path(self):
        for view_class, view_name in (
            (TestOverviewView, "overview"),
            (TestLinkedRecordsView, "linked_records"),
            (TestPropertiesView, "properties"),
            (TestActionsView, "actions"),
        ):
            with self.subTest(view_name=view_name):
                view = view_class()

                template_names = view.get_template_names()

                self.assertEqual(
                    template_names,
                    [f"test_app/detail_view/detail_view_{view_name}.html"],
                )

    def test_get_context_data_adds_breadcrumbs_back_button_and_tabs(self):
        view = self.setup_test_view_class(TestOverviewView)

        with patch(
            "webapp.mixins.reverse",
            side_effect=lambda name, args=None, kwargs=None: f"/{name}",
        ):
            context = view.get_context_data()

        self.assertEqual(
            context["breadcrumbs"],
            [
                {"text": "Test records", "url": "/test-app:test-app"},
                {"text": "Test record record"},
            ],
        )
        self.assertEqual(
            context["back_button"],
            {"url": "/test-app:test-app", "text": "Back to list of test records"},
        )
        self.assertEqual(
            [tab["text"] for tab in context["tabs"]],
            ["Overview", "Linked records", "Properties"],
        )
        self.assertEqual(
            [tab["url"] for tab in context["tabs"]],
            [
                "/test-app:detail-overview",
                "/test-app:detail-linked-records",
                "/test-app:detail-properties",
            ],
        )
        self.assertEqual(
            [tab["current"] for tab in context["tabs"]], [True, False, False]
        )
        self.assertEqual(context["page_heading"], "Overview heading")
        self.assertEqual(context["page_caption"], "Test record record for")
        self.assertFalse(context["use_full_width"])

    def test_get_context_data_marks_current_tab_and_full_width_for_properties(self):
        view = self.setup_test_view_class(TestPropertiesView)

        with patch(
            "webapp.mixins.reverse",
            side_effect=lambda name, args=None, kwargs=None: f"/{name}",
        ):
            context = view.get_context_data()

        self.assertEqual(
            context["breadcrumbs"],
            [
                {"text": "Test records", "url": "/test-app:test-app"},
                {"text": "Test record record"},
            ],
        )
        self.assertEqual(
            context["back_button"],
            {"url": "/test-app:test-app", "text": "Back to list of test records"},
        )
        self.assertEqual(
            [tab["text"] for tab in context["tabs"]],
            ["Overview", "Linked records", "Properties"],
        )
        self.assertEqual(
            [tab["url"] for tab in context["tabs"]],
            [
                "/test-app:detail-overview",
                "/test-app:detail-linked-records",
                "/test-app:detail-properties",
            ],
        )
        self.assertEqual(
            [tab["current"] for tab in context["tabs"]], [False, False, True]
        )
        self.assertEqual(context["page_heading"], "Properties heading")
        self.assertEqual(context["page_caption"], "Test record record for")
        self.assertTrue(context["use_full_width"])


class DetailLayoutMixinTests(BaseTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def make_view(self, request):
        view = TestOverviewView()
        view.setup(request)
        return view

    def make_request_with_cookie(self, value):
        request = self.factory.get("/records/1/")
        request.COOKIES["detail_layout"] = value
        return request

    def test_detail_layout_is_new_without_cookie(self):
        view = self.make_view(self.factory.get("/records/1/"))

        self.assertEqual(view.detail_layout, "new")

    def test_detail_layout_follows_cookie(self):
        for value in ("classic", "new"):
            with self.subTest(value=value):
                view = self.make_view(self.make_request_with_cookie(value))

                self.assertEqual(view.detail_layout, value)

    def test_detail_layout_ignores_unknown_cookie_value(self):
        view = self.make_view(self.make_request_with_cookie("fancy"))

        self.assertEqual(view.detail_layout, "new")

    def test_detail_layout_ignores_cookie_when_switch_disabled(self):
        view = self.make_view(self.make_request_with_cookie("classic"))

        with patch.object(TestOverviewView, "detail_layout_switch_enabled", False):
            self.assertEqual(view.detail_layout, "new")

    def test_switch_sets_cookie_logs_and_redirects_without_parameter(self):
        request = self.factory.get(
            "/records/1/", {"detail_layout": "classic", "page": "2"}
        )
        request.user = SimpleNamespace(pk=7)
        view = self.make_view(request)

        with self.assertLogs("webapp.mixins", level="INFO") as logs:
            response = view.dispatch(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/records/1/?page=2")
        cookie = response.cookies["detail_layout"]
        self.assertEqual(cookie.value, "classic")
        self.assertEqual(cookie["max-age"], 60 * 60 * 24 * 90)
        self.assertTrue(cookie["secure"])
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertIn("Detail layout switched to classic by user ID 7.", logs.output[0])

    def test_dispatch_renders_page_without_cookie_when_switch_not_valid(self):
        cases = (
            ("unknown layout", {"detail_layout": "fancy"}, True),
            ("switch disabled", {"detail_layout": "classic"}, False),
        )
        for name, params, switch_enabled in cases:
            with self.subTest(name):
                request = self.factory.get("/records/1/", params)
                view = self.make_view(request)

                with (
                    patch.object(
                        TestOverviewView,
                        "detail_layout_switch_enabled",
                        switch_enabled,
                    ),
                    patch(
                        "django.views.generic.base.View.dispatch",
                        return_value=HttpResponse("record page"),
                    ) as parent_dispatch,
                ):
                    response = view.dispatch(request)

                parent_dispatch.assert_called_once()
                self.assertNotIn("detail_layout", response.cookies)

    def test_add_detail_layout_uses_layout_base_and_offers_the_other_layout(self):
        view = self.make_view(self.make_request_with_cookie("classic"))
        context = {}

        view.add_detail_layout(context)

        self.assertEqual(context["detail_layout"], "classic")
        self.assertEqual(
            context["detail_layout_base"],
            "webapp/components/record_tabs/record_overview_base_classic.html",
        )
        self.assertEqual(
            context["detail_layout_toggle_url"], "/records/1/?detail_layout=new"
        )
