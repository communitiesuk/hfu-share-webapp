from django.utils.html import format_html
from django_tables2 import CheckBoxColumn


class GovUkCheckboxColumn(CheckBoxColumn):
    def render(self, value, bound_column, record):
        return format_html(
            """
            <div class="govuk-checkboxes govuk-checkboxes--small"
                    data-module="govuk-checkboxes">
                <div class="govuk-checkboxes__item">
                    <input class="govuk-checkboxes__input" type="checkbox" value="{}">
                     <label class="govuk-label govuk-checkboxes__label">
                        <span class="govuk-visually-hidden">Select this row</span>
                     </label>
                    </input>
                </div>
            </div>""",
            value,
        )

    @property
    def header(self):
        return format_html(
            """
            <div class="govuk-checkboxes govuk-checkboxes--small"
                    data-module="govuk-checkboxes">
                <div class="govuk-checkboxes__item">
                    <input class="govuk-checkboxes__input" type="checkbox"
                        value="{}" id="select-all">
                     <label class="govuk-label govuk-checkboxes__label">
                        <span class="govuk-visually-hidden">Select all rows</span>
                     </label>
                    </input>
                </div>
            </div>""",
            "all",
        )
