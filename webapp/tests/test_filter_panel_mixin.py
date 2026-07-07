from django.db import models
from django.db.models import CharField, IntegerField
from django.test import RequestFactory, TestCase
from django_filters import (
    CharFilter,
    DateFilter,
    FilterSet,
    MultipleChoiceFilter,
    NumberFilter,
    RangeFilter,
)

from webapp.mixins import Filter, FilterPanelMixin
from webapp.widgets import DatePicker


class TestModel(models.Model):
    name: CharField = models.CharField(max_length=100)
    age: IntegerField = models.IntegerField()


class TestFilterSet(FilterSet, FilterPanelMixin):
    name = CharFilter(field_name="name", lookup_expr="icontains", label="Name label")
    age = NumberFilter(field_name="age", lookup_expr="icontains", label="Age label")
    height = RangeFilter(field_name="height", label="Height label")
    hair_colour = MultipleChoiceFilter(
        choices=[
            ("brown_value", "Brown"),
            ("ginger_value", "Ginger"),
        ],
        null_label="Unspecified",
        null_value="None",
        label="Hair colour",
    )
    latest_arrival_date = DateFilter(
        label="",
        field_name="latest_arrival_date",
        widget=DatePicker(
            attrs={"hint": "Hint text"},
        ),
        distinct=True,
    )

    class Meta:
        model = TestModel
        fields = [
            "name",
            "age",
            "height",
            "hair_colour",
            "latest_arrival_date",
        ]


class FilterPanelMixinTestCase(TestCase):
    def setUp(self):
        self.test_filter_set = TestFilterSet()

    def test_applied_filters_have_correct_labels_when_none_is_set(self):
        """
        Tests applied_filters method returns filter passed as a query parameter
         along with its label, value, and the url to clear the filter when the Filter
         does not contain a label.
        """
        self.test_filter_set.request = RequestFactory().get(
            "/", query_params={"latest_arrival_date": "01/01/2025"}
        )

        applied_filters = self.test_filter_set.applied_filters

        self.assertEqual(
            applied_filters, [Filter("Latest Arrival Date", [("01/01/2025", "/?")])]
        )

    def test_applied_filters_returns_single_filter_passed_in_request(self):
        """
        Tests applied_filters method returns filter passed as a query parameter
         along with its label, value, and the url to clear the filter.
        """
        self.test_filter_set.request = RequestFactory().get(
            "/", query_params={"name": "bob"}
        )

        applied_filters = self.test_filter_set.applied_filters

        self.assertEqual(applied_filters, [Filter("Name label", [("bob", "/?")])])

    def test_applied_filters_returns_multiple_filters_passed_in_request(self):
        """
        Tests applied_filters method returns correct chips for filters passed
         as query parameters including for each filter label, value, and the
         url to clear the filter.
        """
        self.test_filter_set.request = RequestFactory().get(
            "/", query_params={"name": "bob", "age": 23}
        )

        applied_filters = self.test_filter_set.applied_filters

        self.assertEqual(
            applied_filters,
            [
                Filter("Name label", [("bob", "/?age=23")]),
                Filter("Age label", [("23", "/?name=bob")]),
            ],
        )

    def test_applied_filters_returns_range_sub_filter_passed_in_request(self):
        """
        Tests applied_filters method returns any filters part of a range filter
         along with its label, value, and the url to clear the filter.
        """
        self.test_filter_set.request = RequestFactory().get(
            "/", query_params={"height_0": "2"}
        )

        applied_filters = self.test_filter_set.applied_filters

        self.assertEqual(applied_filters, [Filter("Height label from", [("2", "/?")])])

    def test_applied_filters_does_not_return_non_filter_params_passed_in_request(self):
        """
        Tests applied_filters method does not incorrectly return non-filter
         query parameters as a filter
        """
        self.test_filter_set.request = RequestFactory().get(
            "/", query_params={"csrf_token": "my_token"}
        )

        self.assertEqual(self.test_filter_set.applied_filters, [])

    def test_show_selected_filters_section_is_true_when_a_filter_is_applied(self):
        """
        Tests that the `show_selected_filters_section` method returns True when
         a filter is applied
        """
        self.test_filter_set.request = RequestFactory().get(
            "/", query_params={"name": "bob"}
        )

        self.assertTrue(self.test_filter_set.show_selected_filters_section)

    def test_show_selected_filters_section_is_false_when_no_filter_is_applied(self):
        """
        Tests that the `show_selected_filters_section` method returns False when
         no filters are applied
        """
        self.test_filter_set.request = RequestFactory().get("/")

        self.assertFalse(self.test_filter_set.show_selected_filters_section)

    def test_delete_individual_filter_link_is_correctly_generated(self):
        """
        Tests at the delete filter link for a filter chip is correctly generated.
         It should be a url that includes all query parameters excluding the
         parameter corresponding to that specific filter.
        """
        self.test_filter_set.request = RequestFactory().get(
            "/a/page/of/the/application",
            query_params={"name": "bob", "not_a_filter": True},
        )

        applied_filters = self.test_filter_set.applied_filters

        self.assertEqual(
            applied_filters,
            [
                Filter(
                    "Name label",
                    [("bob", "/a/page/of/the/application?not_a_filter=True")],
                ),
            ],
        )

    def test_clear_filters_link_is_correctly_generated(self):
        """
        Tests that url is generated correctly to redirect the user
         to a page with no filters applied, but including non-filter params
        """
        self.test_filter_set.request = RequestFactory().get(
            "/a/page/of/the/application",
            query_params={
                "name": "bob",
                "age": 23,
                "height_0": 2,
                "not_a_filter": True,
            },
        )

        self.assertEqual(
            self.test_filter_set.clear_filters_link,
            "/a/page/of/the/application?not_a_filter=True",
        )

    def test_show_filters_panel_returns_true_when_query_param_is_present(self):
        """
        Tests that `show_filters_panel` returns True when the
         show_filters_panel query parameter is present.
        """
        self.test_filter_set.request = RequestFactory().get(
            "/", query_params={"show_filters_panel": True}
        )

        self.assertTrue(self.test_filter_set.show_filters_panel)

    def test_show_filters_panel_returns_false_when_query_param_is_not_present(self):
        """
        Tests that `show_filters_panel` returns False when the
         show_filters_panel query parameter is not present.
        """
        self.test_filter_set.request = RequestFactory().get("/", query_params={})

        self.assertFalse(self.test_filter_set.show_filters_panel)

    def test_applied_filters_returns_correct_null_label_for_multichoice_filter(self):
        """
        Tests applied_filters method returns the correct human readable names
          for the null/undefined option of a MultipleChoiceFilter.
        """
        self.test_filter_set.request = RequestFactory().get(
            "/", query_params={"hair_colour": "None"}
        )

        applied_filters = self.test_filter_set.applied_filters

        self.assertEqual(
            applied_filters, [Filter("Hair colour", [("Unspecified", "/?")])]
        )

    def test_applied_filters_returns_correct_option_labels_for_multichoice_filter(self):
        """
        Tests applied_filters method returns the correct human readable names
          for regular options of a MultipleChoiceFilter.
        """
        self.test_filter_set.request = RequestFactory().get(
            "/", query_params={"hair_colour": "ginger_value"}
        )

        applied_filters = self.test_filter_set.applied_filters

        self.assertEqual(applied_filters, [Filter("Hair colour", [("Ginger", "/?")])])
