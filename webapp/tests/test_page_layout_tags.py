from django.template import Context, Template

from test_utils.base import BaseSimpleTestCase


class GridRowTagTests(BaseSimpleTestCase):
    def render(self, body, column="two-thirds"):
        template = Template(
            "{% load page_layout_tags %}"
            f'{{% grid_row "{column}" %}}{body}{{% endgrid_row %}}'
        )
        return template.render(Context())

    def test_grid_row_renders_nothing_when_body_is_empty(self):
        self.assertEqual(self.render(""), "")

    def test_grid_row_renders_nothing_when_body_is_only_whitespace(self):
        self.assertEqual(self.render("  \n  "), "")

    def test_grid_row_wraps_body_in_row_and_column(self):
        result = self.render("<p>Content</p>", column="full")

        expected = (
            '<div class="govuk-grid-row">'
            '<div class="govuk-grid-column-full"><p>Content</p></div>'
            "</div>"
        )
        self.assertHTMLEqual(result, expected)
