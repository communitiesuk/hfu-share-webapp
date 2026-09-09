from crispy_forms_gds.choices import Choice
from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Button, Div, Field, Layout, Size
from django import forms
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
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
                    lambda group: (
                        group[0]
                        not in [
                            GroupType.DEV,
                            GroupType.LOCAL_AUTHORITY_BROWSER_TEST,
                            GroupType.MHCLG_EARLY_ADOPTERS,
                            GroupType.DEVOLVED_ADMINISTRATION_EARLY_ADOPTERS,
                            GroupType.HOME_OFFICE_EARLY_ADOPTERS,
                            GroupType.LOCAL_AUTHORITY_EARLY_ADOPTERS,
                            GroupType.SERVICE_SUPPORT_EARLY_ADOPTERS,
                        ]
                    ),
                    GroupType.choices,
                )
            )
        ],
        label="Select user group",
        widget=forms.RadioSelect(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios("group_type", legend_size=Size.EXTRA_LARGE, legend_tag="h1"),
            Div(
                Button("button", "Next"),
                HTML(
                    render_to_string(
                        "user_management/access_request_form/buttons/cancel_link.html",
                        {"cancel_url": reverse("webapp:landing-page")},
                    )
                ),
                style="display: flex; gap: 16px; align-items: baseline",
            ),
        )


class AccessRequestFormDaGroupTypeStep(forms.Form):
    da_group_type = forms.ChoiceField(
        choices=AccessRequest.DaGroupType.choices,
        label="Select user group",
        help_text=render_to_string(
            "user_management/access_request_form/help_text/da_group_type_hint.html"
        ),
        widget=forms.RadioSelect(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios(
                "da_group_type", legend_size=Size.EXTRA_LARGE, legend_tag="h1"
            ),
            Div(
                Button("button", "Next"),
                HTML(
                    render_to_string(
                        "user_management/access_request_form/buttons/cancel_button.html",
                        {"value": "group_type"},
                    )
                ),
                css_class="govuk-button-group",
            ),
        )


class AccessRequestFormDevolvedAdministrationStep(forms.Form):
    devolved_administration = forms.ModelChoiceField(
        queryset=GroupInfo.objects.filter(group_type=GroupType.DEVOLVED_ADMINISTRATION)
        .exclude(group__name="da_england")
        .exclude(da_name__isnull=True)
        .exclude(da_name=""),
        label="Select a devolved administration",
        widget=forms.RadioSelect(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields[
            "devolved_administration"
        ].label_from_instance = render_name_label_from_group_info
        self.helper.layout = Layout(
            Field.radios("devolved_administration", legend_size=Size.MEDIUM),
            Div(
                Button("button", "Next"),
                HTML(
                    render_to_string(
                        "user_management/access_request_form/buttons/cancel_button.html",
                        {"value": "da_group_type"},
                    )
                ),
                css_class="govuk-button-group",
            ),
        )


class AccessRequestFormLocalAuthorityStep(forms.Form):
    local_authority = forms.ModelChoiceField(
        queryset=GroupInfo.objects.filter(
            group_type=GroupType.LOCAL_AUTHORITY
        ).order_by("group__name"),
        empty_label="",
        label="Select an upper tier or lower tier local authority",
        help_text=render_to_string(
            "user_management/access_request_form/help_text/local_authority_hint.html"
        ),
        error_messages={"required": "You must select one."},
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
        label="Tell us why you need access",
        help_text=render_to_string(
            "user_management/access_request_form/help_text/justification_hint.html",
        ),
        widget=forms.Textarea(),
        error_messages={"required": "Enter why you need access"},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field(
                "justification",
                label_tag="h1",
                rows="5",
                context={"label_tag": "h1", "label_size": "govuk-label--xl"},
            ),
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
                    render_to_string(
                        "user_management/access_request_form/buttons/cancel_link.html",
                        {"cancel_url": reverse("user-management:access-requests")},
                    )
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
