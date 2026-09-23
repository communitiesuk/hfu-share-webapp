from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Button, Div, Field, Layout, Size
from django import forms
from django.forms import ChoiceField, RadioSelect

from ontology.models import SafeguardingReferral
from webapp.layout import Link


class CentralSafeguardingAlertedStatusForm(forms.Form):
    alerted_status = ChoiceField(
        choices=SafeguardingReferral.AlertedStatus.choices,
        widget=RadioSelect(),
        required=True,
        label="Alerted status",
        help_text=("Change the status of these alerts to update the record."),
        error_messages={
            "required": "Please select an alerted status.",
        },
    )

    def __init__(self, *args, alerted_status=None, user_can_edit=True, **kwargs):
        super().__init__(*args, **kwargs)
        answer_options_order = [
            "Not Alerted",
            "Some Alerted",
            "Alerted",
        ]
        choices = list(self.fields["alerted_status"].choices)
        choices_dict = {c[0]: c for c in choices}
        self.fields["alerted_status"].choices = [
            choices_dict[k] for k in answer_options_order if k in choices_dict
        ]
        if alerted_status:
            self.fields["alerted_status"].initial = alerted_status

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios(
                "alerted_status",
                legend_size=Size.MEDIUM,
            ),
            Div(
                Button.primary(
                    "submit",
                    "Save",
                    css_class="govuk-button",
                    disabled=not user_can_edit,
                ),
                Link.cancel(
                    **{
                        "css_class": "app-link--disabled",
                        "tabindex": "-1",
                        "aria_disabled": "true",
                    }
                    if not user_can_edit
                    else {}
                ),
                css_class="govuk-button-group",
            ),
        )
