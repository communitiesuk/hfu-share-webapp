from datetime import datetime, timedelta

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Field, Fieldset, Layout
from crispy_forms_gds.layout.constants import Size
from django import forms

from ontology.models import MvPerson
from webapp.mixins import ReadOnlyFieldsMixin
from webapp.widgets import DatePicker, MultiValueWidget

GENDERS = (
    ("", ""),
    ("Female", "Female"),
    ("Male", "Male"),
)


class GuestBaseForm(ReadOnlyFieldsMixin, forms.ModelForm):
    class Meta:
        model = MvPerson
        fields: list[str] = []

    def get_upe_visa_status_field_layout(self):
        return [
            Field(
                "upe_visa_status",
                context={"legend_size": "govuk-fieldset__legend--s"},
            ),
        ]

    def get_readonly_summary_fields_layout(self):
        return [
            HTML(self.render_readonly_field("Visa Status", "visa_status")),
            HTML(self.render_readonly_field("Arrival Date", "arrival_date")),
            HTML(
                self.render_readonly_field("Latest Arrival Date", "latest_arrival_date")
            ),
            HTML(
                self.render_readonly_field(
                    "Unique Application Number (UAN)", "application_number"
                )
            ),
            HTML(self.render_readonly_field("Global Web Form number (GWF)", "gwf")),
        ]

    def get_button_layout(self):
        return [
            HTML(
                '<div class="govuk-button-group">'
                '    <button type="submit" class="govuk-button">Update</button>'
                '    <a class="govuk-link govuk-link--no-visited-state"\n'
                '       href="{{ cancel_url }}">Cancel</a>'
                "</div>"
            ),
        ]


class GuestEditForm(GuestBaseForm):
    first_name = forms.CharField(
        label="First Name",
        widget=forms.Textarea(attrs={"required": True, "rows": 1}),
        error_messages={"required": "Please enter a valid name"},
    )
    last_name = forms.CharField(
        label="Last Name",
        widget=forms.Textarea(attrs={"required": True, "rows": 1}),
        error_messages={"required": "Please enter a valid last name"},
    )
    date_of_birth = forms.DateField(
        label="Date of Birth",
        widget=DatePicker(
            attrs={
                "required": True,
                "hint": f"For example "
                f"{(datetime.today() - timedelta(days=4000)).strftime('%d/%m/%Y')}",
            }
        ),
        error_messages={"required": "Please enter a valid date of birth"},
    )
    gender = forms.ChoiceField(
        choices=GENDERS,
        label="Sex (optional)",
        widget=forms.Select(attrs={"required": False}),
        required=False,
    )
    email = forms.Field(
        label="Email address",
        required=True,
        widget=MultiValueWidget(
            attrs={"label": "email", "required": True, "input_type": "email"}
        ),
        error_messages={
            "required": "Please enter an email address",
            "invalid": "Please enter a valid email address",
        },
    )
    phone = forms.Field(
        label="Phone number (optional)",
        required=False,
        widget=MultiValueWidget(attrs={"label": "phone number"}),
    )
    passport_id = forms.Field(
        label="Passport number",
        required=True,
        widget=MultiValueWidget(attrs={"label": "passport number", "required": True}),
    )
    disability_flag = forms.BooleanField(
        label="Yes",
        required=False,
        initial=False,
    )

    class Meta:
        model = MvPerson
        fields = [
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "disability_flag",
            "email",
            "phone",
            "passport_id",
        ]

    def get_editable_fields_layout(self):
        return [
            Field.text("first_name", legend_size=Size.SMALL, label_size=Size.SMALL),
            Field.text("last_name", legend_size=Size.SMALL, label_size=Size.SMALL),
            Field.text("date_of_birth", legend_size=Size.SMALL, label_size=Size.SMALL),
            Field(
                "gender",
                context={"label_size": "govuk-fieldset__legend--s"},
            ),
            Field(
                "email",
                context={
                    "label_size": "govuk-fieldset__legend--s",
                    "hint": "Enter up to 5 email addresses",
                },
            ),
            Field(
                "phone",
                context={
                    "label_size": "govuk-fieldset__legend--s",
                    "hint": "Enter up to 5 phone numbers",
                },
            ),
            Field(
                "passport_id",
                context={
                    "label_size": "govuk-fieldset__legend--s",
                    "hint": "Enter up to 5 passport numbers",
                },
            ),
            Fieldset(
                Field.checkboxes("disability_flag", legend_size=Size.SMALL),
                legend="Disability",
                legend_size=Size.SMALL,
            ),
        ]

    def clean_disability_flag(self):
        return self.cleaned_data.get("disability_flag")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            *self.get_editable_fields_layout(),
            *self.get_readonly_summary_fields_layout(),
            *self.get_button_layout(),
        )


class UPEVisaStatusFieldMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["upe_visa_status"].widget = forms.RadioSelect()
        self.fields["upe_visa_status"].choices = MvPerson.UPEVisaStatus.choices
        self.fields["upe_visa_status"].label = "UPE visa status"
        self.fields["upe_visa_status"].required = True
        self.fields["upe_visa_status"].error_messages = {
            "required": "Please select a UPE visa status"
        }


class GuestEditUKVIForm(UPEVisaStatusFieldMixin, GuestBaseForm):
    class Meta:
        model = MvPerson
        fields = ["upe_visa_status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML(self.render_readonly_field("First Name", "first_name")),
            HTML(self.render_readonly_field("Last Name", "last_name")),
            HTML(self.render_readonly_field("Date of Birth", "date_of_birth")),
            HTML(self.render_readonly_field("Email", "email")),
            HTML(self.render_readonly_field("Phone", "phone")),
            HTML(self.render_readonly_field("Passport number", "passport_id")),
            *self.get_upe_visa_status_field_layout(),
            *self.get_readonly_summary_fields_layout(),
            *self.get_button_layout(),
        )


class GuestEditAdminForm(UPEVisaStatusFieldMixin, GuestEditForm):
    class Meta(GuestEditForm.Meta):
        fields = GuestEditForm.Meta.fields + ["upe_visa_status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            *self.get_editable_fields_layout(),
            *self.get_upe_visa_status_field_layout(),
            *self.get_readonly_summary_fields_layout(),
            *self.get_button_layout(),
        )
