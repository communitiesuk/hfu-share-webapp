from crispy_forms_gds.choices import Choice
from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import (
    Button,
    Div,
    Field,
    Layout,
    Size,
)
from django import forms

from ontology.models import (
    SponsorshipCertificationForm,
)
from webapp.layout import Link


class PreApprovalCheckStatusForm(forms.Form):
    check_name: str
    check_hint: str

    status = forms.ChoiceField(
        choices=[
            Choice(
                label=status,
                value=status.value,
            )
            for status in SponsorshipCertificationForm.PreApprovalCheckStatus
        ],
        widget=forms.RadioSelect(),
    )

    def __init__(self, check_label, check_hint, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["status"].label = check_label
        self.fields["status"].help_text = check_hint
        self.fields["status"].error_messages["required"] = (
            f"Select a new status for {check_label} or select cancel."
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios(
                "status",
                legend_size=Size.MEDIUM,
            ),
            Div(
                Button("submit", "Save check"),
                Link.cancel(),
                css_class="govuk-button-group",
            ),
        )


class SponsorCertificationCodeEmailedForm(forms.Form):
    status = forms.BooleanField(
        widget=forms.CheckboxInput(),
        label="Sponsor certification code emailed to sponsor.",
        help_text="Once all sponsor suitability checks have been passed, email the "
        "Sponsor Certification code to the sponsor.",
        error_messages={
            "required": "Select the check box to confirm you have emailed the sponsor."
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.initial.get("status") is True:
            self.fields["status"].required = False

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.checkboxes(
                "status",
                legend="Approval sent",
                legend_size=Size.MEDIUM,
            ),
            Div(
                Button("submit", "Save check"),
                Link.cancel(),
                css_class="govuk-button-group",
            ),
        )
