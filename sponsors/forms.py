from datetime import datetime, timedelta

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Field, Layout
from crispy_forms_gds.layout.constants import Size
from django import forms

from ontology.models import MvVolunteer
from webapp.mixins import ReadOnlyFieldsMixin
from webapp.widgets import DatePicker, MultiValueWidget


class SponsorEditForm(ReadOnlyFieldsMixin, forms.ModelForm):
    first_name = forms.CharField(
        label="First Name",
        widget=forms.Textarea(attrs={"rows": 1}),
        required=True,
        error_messages={"required": "Please enter a valid first name"},
    )

    last_name = forms.CharField(
        label="Last Name",
        widget=forms.Textarea(attrs={"rows": 1}),
        required=True,
        error_messages={"required": "Please enter a valid last name"},
    )

    date_of_birth = forms.DateField(
        label="Date of Birth",
        widget=DatePicker(
            attrs={
                "hint": f"For example "
                f"{(datetime.today() - timedelta(days=20)).strftime('%d/%m/%Y')}",
            }
        ),
        required=True,
        error_messages={"required": "Please enter a valid date of birth"},
    )

    GENDERS = (
        ("", ""),
        ("Female", "Female"),
        ("Male", "Male"),
    )
    sex = forms.ChoiceField(
        choices=GENDERS,
        label="Sex (optional)",
        widget=forms.Select(),
        required=False,
    )

    email = forms.EmailField(
        label="Email address",
        required=True,
        error_messages={
            "required": "Please enter an email address",
            "invalid": "Please enter a valid email address",
        },
    )

    phone_number = forms.Field(
        label="Phone number (optional)",
        required=False,
        widget=MultiValueWidget(
            attrs={
                "label": "phone number",
            }
        ),
    )

    passport_details = forms.Field(
        label="Passport number (optional)",
        required=False,
        widget=MultiValueWidget(
            attrs={
                "label": "passport number",
            }
        ),
    )

    STATUSES = (
        ("Married or a civil partner", "Married or a civil partner"),
        ("Single", "Single"),
        (
            "Married or civil partnership dissolved",
            "Married or civil partnership dissolved",
        ),
        ("Unmarried partner", "Unmarried partner"),
        (
            "Widowed or a surviving civil partner",
            "Widowed or a surviving civil partner",
        ),
        ("Separated", "Separated"),
    )
    family_situation = forms.ChoiceField(
        choices=STATUSES,
        label="Relationship status",
        widget=forms.Select(),
        required=False,
    )

    class Meta:
        model = MvVolunteer
        fields = [
            "first_name",
            "last_name",
            "date_of_birth",
            "sex",
            "email",
            "phone_number",
            "passport_details",
            "family_situation",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.text(
                "first_name",
                legend_size=Size.SMALL,
                label_size=Size.SMALL,
            ),
            Field.text(
                "last_name",
                legend_size=Size.SMALL,
                label_size=Size.SMALL,
            ),
            Field.text(
                "date_of_birth",
                legend_size=Size.SMALL,
                label_size=Size.SMALL,
            ),
            Field(
                "sex",
                context={
                    "label_size": "govuk-fieldset__legend--s",
                },
            ),
            Field.text(
                "email",
                legend_size=Size.SMALL,
                label_size=Size.SMALL,
            ),
            Field(
                "phone_number",
                context={
                    "label_size": "govuk-fieldset__legend--s",
                    "hint": "Enter up to 5 phone numbers",
                },
            ),
            Field(
                "passport_details",
                context={
                    "label_size": "govuk-fieldset__legend--s",
                    "hint": "Enter up to 5 passport numbers",
                },
            ),
            Field(
                "family_situation",
                context={
                    "label_size": "govuk-fieldset__legend--s",
                },
            ),
            HTML(self.render_readonly_field("Host", "is_eoi")),
            HTML(self.render_readonly_field("Sponsor", "is_sponsor")),
            HTML(
                '<div class="govuk-button-group">'
                '    <button type="submit" class="govuk-button">Update</button>'
                '    <a class="govuk-link govuk-link--no-visited-state"\n'
                '       href="{{ cancel_url }}">Cancel</a>'
                "</div>"
            ),
        )
