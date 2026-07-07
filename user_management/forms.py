from crispy_forms_gds.choices import Choice
from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Button, Div, Field, Layout, Size
from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse

from accounts.enums import GroupType
from accounts.models import AccessRequest, GroupInfo
from user_management.templatetags.access_request_extras import (
    render_name_label_from_group_info,
)
from webapp.fields import ConditionalRadioField
from webapp.widgets import ConditionalRadioWidget, SearchableSelect

GROUP_TYPE_HINTS = {
    GroupType.LOCAL_AUTHORITY: (
        "You can select a specific upper tier or lower tier "
        "local authority in the next step."
    ),
    GroupType.DEVOLVED_ADMINISTRATION: (
        "You can select the country in the next step. "
        "You can also select a local authority if needed."
    ),
}


class AccessRequestFormGroupTypeStep(forms.Form):
    group_type = forms.ChoiceField(
        choices=[
            Choice(
                label=label,
                value=value,
                hint=GROUP_TYPE_HINTS.get(GroupType(value)),
            )
            for value, label in list(
                filter(
                    lambda group: group[0]
                    not in [
                        GroupType.DEV,
                        GroupType.MHCLG_EARLY_ADOPTERS,
                        GroupType.DEVOLVED_ADMINISTRATION_EARLY_ADOPTERS,
                        GroupType.HOME_OFFICE_EARLY_ADOPTERS,
                        GroupType.LOCAL_AUTHORITY_EARLY_ADOPTERS,
                        GroupType.SERVICE_SUPPORT_EARLY_ADOPTERS,
                    ],
                    GroupType.choices,
                )
            )
        ],
        label="",
        widget=forms.RadioSelect(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios("group_type"),
            Div(
                Button("button", "Next"),
                HTML(
                    f'<a href="{reverse("webapp:landing-page")}"'
                    f'class="govuk-link govuk-link--no-visited-state govuk-body">'
                    f"Cancel"
                    f"</a>"
                ),
                style="display: flex; gap: 16px; align-items: baseline",
            ),
        )


class AccessRequestFormDaGroupTypeStep(forms.Form):
    da_group_type = forms.ChoiceField(
        choices=AccessRequest.DaGroupType.choices,
        label="Select devolved administrator user group",
        widget=forms.RadioSelect(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios("da_group_type", legend_size=Size.LARGE),
            Button("button", "Next"),
        )


class AccessRequestFormDevolvedAdministrationStep(forms.Form):
    devolved_administration = forms.ModelChoiceField(
        queryset=GroupInfo.objects.filter(
            group_type=GroupType.DEVOLVED_ADMINISTRATION
        ).exclude(group__name="da_england"),
        label="Select relevant devolved administration",
        widget=forms.RadioSelect(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields[
            "devolved_administration"
        ].label_from_instance = render_name_label_from_group_info
        self.helper.layout = Layout(
            Field.radios("devolved_administration", legend_size=Size.LARGE),
            Button("button", "Next"),
        )


class AccessRequestFormLocalAuthorityStep(forms.Form):
    local_authority = forms.ModelChoiceField(
        queryset=GroupInfo.objects.filter(
            group_type=GroupType.LOCAL_AUTHORITY
        ).order_by("group__name"),
        empty_label="",
        label="Select an upper tier or lower tier local authority",
        help_text=(
            "You can only select one. If you need to select more you "
            "will need to start a new data access request for each area.</br></br>"
            "If you are from a unitary authority you can select either LTLA or UTLA "
            "for the relevant area you need to access to.</br></br>"
            "UTLA users only need to select their relevant UTLA. They will also get "
            "access to the LTLA data for that area, they do not need to submit "
            "another data access request for LTLA data."
        ),
        widget=SearchableSelect(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[
            "local_authority"
        ].label_from_instance = render_name_label_from_group_info
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.text("local_authority", label_size=Size.MEDIUM),
            Button("button", "Next"),
        )


class AccessRequestFormJustificationStep(forms.Form):
    justification = forms.CharField(
        label="Tell us why access is needed",
        help_text="For example, I am working on the Homes for Ukraine scheme in (your "
        "local authority) and need access to the records.",
        widget=forms.Textarea(),
        error_messages={"required": "Enter why you need access"},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.textarea("justification", label_size=Size.LARGE, rows=5),
            Button("button", "Next"),
        )


class AccessRequestFormReviewStep(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Button("submit", "Confirm and submit"),
        )


class AccessRequestApprovalForm(forms.Form):
    approval_status = ConditionalRadioField(
        choices=[
            (AccessRequest.Status.APPROVED, "Approve request"),
            (AccessRequest.Status.REJECTED, "Deny request"),
        ],
        widget=ConditionalRadioWidget(),
        label="",
        conditional_inputs={
            AccessRequest.Status.REJECTED: [
                {
                    "type": "textarea",
                    "label": "Reason",
                    "required": True,
                }
            ],
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("approval_status"),
            Div(
                Button("submit", "Confirm"),
                HTML(
                    f'<a href="{reverse("user-management:access-requests")}"'
                    f'class="govuk-link govuk-link--no-visited-state govuk-body">'
                    f"Cancel"
                    f"</a>"
                ),
                style="display: flex; gap: 16px; align-items: baseline",
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        approval_status = cleaned_data.get("approval_status")
        approval_status_additional_text = self.data.get(
            f"approval-approval_status_extra_{approval_status}", ""
        )

        if (
            approval_status == AccessRequest.Status.REJECTED
            and approval_status_additional_text.strip() == ""
        ):
            msg = "Please provide a reason."
            self.add_error("approval_status", ValidationError(msg))

        if approval_status == AccessRequest.Status.REJECTED:
            cleaned_data["rejection_justification"] = approval_status_additional_text
        return cleaned_data
