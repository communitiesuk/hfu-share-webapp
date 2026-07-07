from enum import StrEnum

from crispy_forms_gds.choices import Choice
from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import (
    HTML,
    ConditionalQuestion,
    ConditionalRadios,
    Div,
    Field,
    Layout,
)
from django import forms

from webapp.widgets import DatePicker


class DownloadType(StrEnum):
    ALL = "all"
    VISA_APPLICATIONS = "visa_applications"
    GUESTS = "guests"
    SPONSORS = "sponsors"
    UAMS = "uams"
    ACCOMMODATION = "accommodation"


class DownloadsTypeForm(forms.Form):
    date_to = forms.DateField(
        required=False,
        label="Date to",
        widget=DatePicker(
            attrs={
                "required": False,
            }
        ),
    )

    date_from = forms.DateField(
        required=False,
        label="Date from",
        widget=DatePicker(
            attrs={
                "required": False,
            }
        ),
    )

    download_type = forms.ChoiceField(
        choices=[
            Choice(
                label="All data",
                value=DownloadType.ALL,
                hint=(
                    "Includes all accommodation requests and the linked records for "
                    "visa applications, guests, sponsors and hosts, and accommodation."
                ),
            ),
            Choice(
                label="Visa applications",
                value=DownloadType.VISA_APPLICATIONS,
            ),
            Choice(
                label="Guests",
                value=DownloadType.GUESTS,
            ),
            Choice(
                label="Sponsors and hosts",
                value=DownloadType.SPONSORS,
            ),
            Choice(
                label="Accommodation",
                value=DownloadType.ACCOMMODATION,
            ),
            Choice(
                label="Applications to sponsor a child",
                value=DownloadType.UAMS,
                hint="Includes data only and not related files.",
            ),
        ],
        label="Select data",
        widget=forms.RadioSelect(),
        error_messages={"required": "Select which data to download."},
    )

    def __init__(self, *args, user_can_download=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            ConditionalRadios(
                "download_type",
                ConditionalQuestion(
                    "All data",
                    Div(
                        Div(
                            Field("date_from"),
                            css_class="govuk-form-group govuk-!-display-inline-block govuk-!-margin-right-2",  # noqa: E501
                        ),
                        Div(
                            Field("date_to"),
                            css_class="govuk-form-group govuk-!-display-inline-block",
                        ),
                        css_class="govuk-grid-row",
                    ),
                ),
                "Visa applications",
                "Guests",
                "Sponsors and hosts",
                "Accommodation",
                "Applications to sponsor a child",
            ),
            Div(
                HTML(
                    '<p class="govuk-body">'
                    "Your data will be downloaded to your device in a comma separated"
                    " value (CSV) file."
                    "</p>"
                    '<div class="govuk-warning-text">'
                    '    <span class="govuk-warning-text__icon" aria-hidden="true">'
                    "    !"
                    "    </span>"
                    '    <strong class="govuk-warning-text__text">'
                    '        <span class="govuk-visually-hidden">Warning</span>'
                    "        Stay on this page until your download is complete."
                    "    </strong>"
                    "</div>"
                ),
            ),
            HTML(
                f'<div class="govuk-button-group">'
                f'    <button type="submit" class="govuk-button"'
                f"{'' if user_can_download else ' disabled'}"
                f">Download data</button>"
                "</div>"
            ),
        )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("download_type") == DownloadType.ALL:
            df, dt = cleaned.get("date_from"), cleaned.get("date_to")
            if df and dt and df > dt:
                self.add_error(
                    "date_to",
                    "The end date must be the same as or later than the start date.",
                )
        else:
            cleaned["date_from"] = None
            cleaned["date_to"] = None
        return cleaned
