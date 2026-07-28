from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Button, Div, Field, Layout, Size
from django import forms


class AssignToLocalAuthorityFormSelectRegionStep(forms.Form):
    region = forms.ChoiceField(
        choices=[
            ("England", "England"),
            ("Scotland", "Scotland"),
            ("Northern Ireland", "Northern Ireland"),
            ("Wales", "Wales"),
        ],
        label="Region",
        help_text="You will select a local authority at the next step.",
        widget=forms.RadioSelect(),
        error_messages={
            "required": "You must select a region.",
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            HTML.h2("Assign to local authority"),
            Field.radios("region", legend_size=Size.MEDIUM),
            Div(
                Button.primary("button", "Continue"),
                HTML(
                    '<a href="{{ cancel_url }}"'
                    'class="govuk-link govuk-link--no-visited-state govuk-body">'
                    "Cancel"
                    "</a>"
                ),
                css_class="govuk-button-group",
            ),
        )
