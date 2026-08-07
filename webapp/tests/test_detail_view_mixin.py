from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, TestCase
from django.views.generic import DetailView

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


class DetailViewMixinTests(TestCase):
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
