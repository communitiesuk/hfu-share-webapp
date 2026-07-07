from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Button, Div, Field, Layout
from crispy_forms_gds.layout.constants import Size
from django import forms

from ontology.models import VisaInformationRequest, VisaInformationRequestComments


class StartVIRForm(forms.ModelForm):
    request_type = forms.ChoiceField(
        label="Select the type of request",
        choices=VisaInformationRequest.RequestType.choices,
        widget=forms.RadioSelect(),
        required=True,
        help_text="You can only select one option.",
        error_messages={
            "required": "You must select a request type.",
        },
    )
    requested_check_type_id = forms.MultipleChoiceField(
        label="Select the check you need",
        choices=VisaInformationRequest.RequestedCheckType.choices,
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        help_text="You can select more than one option.",
        error_messages={
            "required": "You must select at least one check.",
        },
    )
    comment = forms.CharField(
        label="Add a comment",
        widget=forms.Textarea(),
        required=True,
        help_text="You can add a reason for the options you selected if needed. "
        "The text you enter should be short and clear.",
        max_length=500,
        error_messages={
            "required": "You must start a VIR with a comment.",
        },
    )

    class Meta:
        model = VisaInformationRequest
        fields = ["request_type", "requested_check_type_id"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios(
                "request_type",
                legend_size=Size.SMALL,
            ),
            Field.checkboxes(
                "requested_check_type_id",
                legend_size=Size.SMALL,
            ),
            Field.textarea(
                "comment",
                legend_size=Size.SMALL,
                label_size=Size.SMALL,
                rows=5,
                max_characters=500,
            ),
            Div(
                Button("start_vir_submit", "Start VIR"),
            ),
        )


class AddVIRCommentForm(forms.ModelForm):
    comment = forms.CharField(
        label="Add a comment",
        widget=forms.Textarea(attrs={"aria-describedby": ""}),
        required=True,
        max_length=500,
        error_messages={
            "required": "You must enter a comment.",
        },
    )

    class Meta:
        model = VisaInformationRequestComments
        fields = [
            "comment",
        ]

    def __init__(self, *args, user_can_close_vir=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        buttons = [
            Button("add_comment_submit", "Add comment"),
        ]
        if user_can_close_vir:
            buttons.append(
                Button(
                    "close_vir_submit",
                    "Close VIR",
                    css_class="govuk-button--secondary govuk-!-margin-left-2",
                )
            )
        self.helper.layout = Layout(
            Field.textarea(
                "comment",
                legend_size=Size.SMALL,
                label_size=Size.SMALL,
                rows=5,
                max_characters=500,
            ),
            Div(*buttons),
        )


class VIRCloseConfirmForm(forms.Form):
    confirm_close = forms.ChoiceField(
        label="Are you sure you want to close this VIR?",
        required=True,
        choices=[("true", "Yes, close VIR"), ("false", "No, return to VIR")],
        widget=forms.RadioSelect,
        help_text="You can re-open this VIR later if needed.",
        error_messages={"required": "You must select an option."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios(
                "confirm_close",
                legend_size=Size.MEDIUM,
            ),
            Div(
                Button("confirm_close_submit", "Confirm"),
                HTML(
                    '<a href="{{ return_url }}"'
                    'class="govuk-link govuk-link--no-visited-state govuk-body">'
                    "Cancel"
                    "</a>"
                ),
                css_class="govuk-button-group",
            ),
        )

    def clean_confirm_close(self):
        value = self.cleaned_data["confirm_close"]
        return value == "true"


class VIRReopenConfirmForm(forms.Form):
    confirm_reopen = forms.ChoiceField(
        label="Are you sure you want to re-open this VIR?",
        required=True,
        choices=[("true", "Yes, re-open VIR"), ("false", "No, return to VIR")],
        widget=forms.RadioSelect,
        help_text="",
        error_messages={"required": "You must select an option."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios(
                "confirm_reopen",
                legend_size=Size.MEDIUM,
            ),
            Div(
                Button("confirm_reopen_submit", "Confirm"),
                HTML(
                    '<a href="{{ return_url }}"'
                    'class="govuk-link govuk-link--no-visited-state govuk-body">'
                    "Cancel"
                    "</a>"
                ),
                css_class="govuk-button-group",
            ),
        )

    def clean_confirm_reopen(self):
        value = self.cleaned_data["confirm_reopen"]
        return value == "true"
