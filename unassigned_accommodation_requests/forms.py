from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Button, Div, Field, Layout, Size
from django import forms

from accounts.enums import GroupType
from accounts.models import GroupInfo
from user_management.templatetags.access_request_extras import (
    render_name_label_from_group_info,
)
from webapp.widgets import SearchableSelect


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
            Field.radios("region", legend_size=Size.LARGE),
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


class AssignToLocalAuthorityFormSelectLocalAuthorityStep(forms.Form):
    local_authority = forms.ModelChoiceField(
        queryset=GroupInfo.objects.none(),
        to_field_name="ltla_name",
        empty_label="",
        label="Local authority",
        widget=SearchableSelect(),
        error_messages={
            "required": "You must select a local authority.",
            "invalid_choice": "You must select a local authority.",
        },
    )

    def __init__(self, *args, region=None, **kwargs):
        super().__init__(*args, **kwargs)

        if region is not None:
            self.fields["local_authority"].queryset = GroupInfo.objects.filter(
                group_type=GroupType.LOCAL_AUTHORITY,
                is_utla=False,
                da_name=region,
            ).order_by("group__name")

        self.fields[
            "local_authority"
        ].label_from_instance = render_name_label_from_group_info

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Field.text("local_authority", label_size=Size.LARGE),
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
