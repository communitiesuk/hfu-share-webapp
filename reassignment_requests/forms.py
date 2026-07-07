from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Button, Div, Field, Fieldset, Layout
from crispy_forms_gds.layout.constants import Size
from django.forms import BooleanField, forms

from ontology.models import ReassignmentRequest


class CancelReassignmentRequestForm(forms.Form):
    confirmation = BooleanField(
        label="Yes, cancel the request",
        required=True,
        error_messages={
            "required": "Tick the box to confirm you want to cancel the request",
        },
    )

    def __init__(self, *args, reassignment_request: ReassignmentRequest, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                Field.checkbox("confirmation"),
                legend=f"Are you sure you want to cancel the request to move "
                f"{reassignment_request.formatted_guest_names()} to "
                f"{reassignment_request.destination_ltla_name}?",
                legend_size=Size.LARGE,
            ),
            Div(
                Button("submit", "Cancel request"),
                HTML(
                    '<a href="{{ cancel_url }}" class="govuk-link '
                    'govuk-link--no-visited-state govuk-body">'
                    "Go back"
                    "</a>"
                ),
                css_class="govuk-button-group",
            ),
        )
