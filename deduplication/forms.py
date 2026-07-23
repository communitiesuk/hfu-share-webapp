from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Field, Fieldset, Layout
from crispy_forms_gds.layout.constants import Size
from django import forms
from django.forms import (
    ChoiceField,
    ModelChoiceField,
    ModelMultipleChoiceField,
    MultipleChoiceField,
    RadioSelect,
)
from django.forms.widgets import CheckboxSelectMultiple, Input
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from ontology.models import (
    MvAccommodation,
    MvAccommodationRequest,
    MvPerson,
    MvVolunteer,
    VisaApplication,
)
from webapp.mixins import ReadOnlyFieldsMixin


class SelectRecordTypeForm(forms.Form):
    def __init__(self, *args, show_guests_option=False, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [
            ("Accommodation", "Accommodation"),
        ]
        if show_guests_option:
            choices.append(("Guests", "Guests"))
        choices.append(("Sponsors and hosts", "Sponsors and hosts"))
        self.fields["object_choice"] = ChoiceField(
            label="",
            choices=choices,
            widget=RadioSelect(),
        )
        home_url = reverse("webapp:landing-page")
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("object_choice"),
            HTML(
                '<p class="govuk-body">'
                "Continue to find records using filter and search, "
                "and deduplicate them.</p>"
            ),
            HTML(
                '<div class="govuk-button-group">'
                '<button type="submit"'
                'class="govuk-button">'
                "Continue"
                "</button>"
                '<a class="govuk-button govuk-button--secondary "'
                f"href={home_url}>"
                "Cancel"
                "</a>"
                "</div>"
            ),
        )


class SelectAndReviewRecordStepForm(forms.Form):
    sponsor_record = ModelMultipleChoiceField(
        queryset=MvVolunteer.objects.all(),
        widget=CheckboxSelectMultiple(),
        required=False,
    )
    guest_record = ModelMultipleChoiceField(
        queryset=MvPerson.objects.all(), widget=CheckboxSelectMultiple(), required=False
    )
    accommodation_record = ModelMultipleChoiceField(
        queryset=MvAccommodation.objects.all(),
        widget=CheckboxSelectMultiple(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ViewSelectedRecordsStepForm(forms.Form):
    sponsor_record_to_remove = ModelChoiceField(
        queryset=MvVolunteer.objects.all(), widget=Input(), required=False
    )
    guest_record_to_remove = ModelChoiceField(
        queryset=MvPerson.objects.all(), widget=Input(), required=False
    )
    accommodation_record_to_remove = ModelChoiceField(
        queryset=MvAccommodation.objects.all(), widget=Input(), required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML(
                '<button class="govuk-button govuk-button--secondary"'
                'name="wizard_goto_step"'
                'type="submit"'
                'value="{{ wizard.steps.prev }}"'
                "{% if object_list|length > 1 %}disabled{% endif %}>"
                "Select another record"
                "</button>"
            ),
            HTML(
                '<button type="submit"'
                'class="govuk-button"'
                "{% if object_list|length < 2 %}disabled{% endif %}>"
                "Confirm selection"
                "</button>"
            ),
            HTML(
                '<a class="govuk-link govuk-link--no-visited-state" '
                'href="{{ cancel_url }}">Cancel</a>'
            ),
        )


class ReviewSelectedRecordsStepForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<button type="submit"class="govuk-button">Continue</button>'),
            HTML(
                '<a class="govuk-link govuk-link--no-visited-state" '
                'href="{{ cancel_url }}">Cancel</a>'
            ),
        )


class SelectAccommodationRequestStepForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.records = kwargs.pop("queryset")
        super().__init__(*args, **kwargs)

        unique_ars = {
            record.accommodation_request
            for record in self.records
            if record.accommodation_request
        }

        ar_choices = [(ar.pk, ar) for ar in unique_ars]
        self.fields["accommodation_request"] = ChoiceField(
            choices=ar_choices,
            label="Accommodation request",
            widget=RadioSelect(),
            help_text=(
                "Select which accommodation request record to link to the new "
                "principal guest record, or cancel to return to the guest selection "
                "screen."
                if len(ar_choices) > 1
                else ""
                if len(ar_choices) == 1
                else "No accommodation request to select."
            ),
            error_messages={"required": "Select an accommodation request."},
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                Field.checkboxes("accommodation_request", legend_size=Size.SMALL),
                legend_size=Size.SMALL,
            ),
            HTML(
                '<div class="govuk-button-group">'
                '<button type="submit"'
                'class="govuk-button">'
                "Continue deduplication"
                "</button>"
                '<a class="govuk-link govuk-link--no-visited-state" '
                'href="{{ cancel_url }}">'
                "Cancel"
                "</a>"
                "</div>"
            ),
        )


class SelectCorrectDetailsStepForm(ReadOnlyFieldsMixin, forms.Form):
    def __init__(self, *args, **kwargs):
        self.records = kwargs.pop("queryset")
        if kwargs.get("select_ar_data"):
            self.select_ar_data = kwargs.pop("select_ar_data")

        super().__init__(*args, **kwargs)

        is_sponsor = all(isinstance(obj, MvVolunteer) for obj in self.records)
        is_guest = all(isinstance(obj, MvPerson) for obj in self.records)
        is_accommodation = all(isinstance(obj, MvAccommodation) for obj in self.records)

        layout_items = []
        form_options = []

        if is_sponsor:
            form_options = self.get_sponsor_form_options()
        elif is_guest:
            form_options = self.get_guest_form_options()
        elif is_accommodation:
            form_options = self.get_accommodation_form_options()

        for form_option in form_options:
            self.append_form_options(
                data=form_option["data"],
                field_name=form_option["field_name"],
                label=form_option["label"],
                layout_items=layout_items,
            )

        if is_guest:
            self.append_guest_application_number(layout_items)
            self.append_guest_accommodation_request(layout_items)

        layout_items.append(
            HTML(
                '<div class="govuk-button-group">'
                '    <button type="submit" class="govuk-button">'
                "       Continue deduplication"
                "    </button>"
                '    <a class="govuk-link govuk-link--no-visited-state"\n'
                '       href="{{ cancel_url }}">Cancel</a>'
                "</div>"
            ),
        )

        # Render the layout
        self.helper = FormHelper()
        self.helper.layout = Layout(*layout_items)

    def append_form_options(self, data, field_name, label, layout_items):
        if len(data) < 2:
            self.fields[field_name].required = False

        if len(data) == 1:
            value = data.pop()
            if field_name == "date_of_birth":
                submitted_value = formatted_value = value.strftime("%-d %B %Y")
            else:
                submitted_value = value.id if hasattr(value, "id") else value
                formatted_value = value
            layout_items.append(
                HTML(
                    render_to_string(
                        "webapp/components/forms/readonly_input_form_field.html",
                        {
                            "label": label,
                            "help_text": self.fields[field_name].help_text,
                            "value": submitted_value,
                            "formatted_value": formatted_value,
                            "name": self[field_name].html_name,
                        },
                    )
                )
            )
        else:
            (
                layout_items.append(
                    Fieldset(
                        Field.checkboxes(field_name, legend_size=Size.SMALL),
                        legend_size=Size.SMALL,
                    )
                ),
            )

    def get_sponsor_form_options(self) -> list[dict]:
        # Work out which fields already match
        unique_first_names = {
            record.first_name for record in self.records if record.first_name
        }
        unique_last_names = {
            record.last_name for record in self.records if record.last_name
        }
        unique_sex = {record.sex for record in self.records if record.sex}
        unique_date_of_birth = {
            record.date_of_birth for record in self.records if record.date_of_birth
        }
        unique_emails = {record.email for record in self.records if record.email}
        unique_phone_numbers = {
            number
            for record in self.records
            if record.phone_number
            for number in record.phone_number
        }
        unique_postcodes = {
            postcode
            for record in self.records
            if record.residential_postcodes
            for postcode in record.residential_postcodes
        }

        # Create the form options
        first_name_choices = [
            (first_name, first_name) for first_name in unique_first_names
        ]
        self.fields["first_name"] = ChoiceField(
            choices=first_name_choices,
            label="First name",
            widget=RadioSelect(),
            help_text=(
                "Select a first name."
                if len(first_name_choices) > 1
                else ""
                if len(first_name_choices) == 1
                else "No first name to select."
            ),
            error_messages={"required": "Select a first name."},
        )

        last_name_choices = [(last_name, last_name) for last_name in unique_last_names]
        self.fields["last_name"] = ChoiceField(
            choices=last_name_choices,
            label="Last name",
            widget=RadioSelect(),
            help_text=(
                "Select a last name."
                if len(last_name_choices) > 1
                else ""
                if len(last_name_choices) == 1
                else "No last name to select."
            ),
            required=True,
            initial=False,
            error_messages={"required": "Select a last name."},
        )

        sex_choices = [(sex, sex) for sex in unique_sex]
        self.fields["sex"] = ChoiceField(
            choices=sex_choices,
            label="Sex",
            widget=RadioSelect(),
            help_text=(
                (
                    "Select a sex or 'no data'."
                    if any(record.sex == "No data" for record in self.records)
                    else "Select a sex."
                )
                if len(sex_choices) > 1
                else ""
                if len(sex_choices) == 1
                else "No sex to select."
            ),
            required=True,
            initial=False,
            error_messages={
                "required": (
                    "Select a sex or 'no data'."
                    if any(record.sex == "No data" for record in self.records)
                    else "Select a sex."
                )
            },
        )

        date_of_birth_choices = [
            (
                f"{date_of_birth.strftime('%-d %B %Y')}",
                f"{date_of_birth.strftime('%-d %B %Y')}",
            )
            for date_of_birth in unique_date_of_birth
        ]
        self.fields["date_of_birth"] = ChoiceField(
            choices=date_of_birth_choices,
            label="Date of birth",
            widget=RadioSelect(),
            help_text=(
                "Select a date of birth."
                if len(date_of_birth_choices) > 1
                else ""
                if len(date_of_birth_choices) == 1
                else "No date of birth to select."
            ),
            required=True,
            initial=False,
            error_messages={"required": "Select a date of birth."},
        )

        email_address_choices = [(email, email) for email in unique_emails]
        self.fields["email_address"] = ChoiceField(
            choices=email_address_choices,
            label="Email address",
            widget=RadioSelect(),
            help_text=(
                "Select an email address."
                if len(email_address_choices) > 1
                else ""
                if len(email_address_choices) == 1
                else "No email address to select."
            ),
            required=True,
            initial=False,
            error_messages={"required": "Select an email address."},
        )

        phone_number_choices = [
            (phone_number, phone_number) for phone_number in unique_phone_numbers
        ]
        self.fields["phone_numbers"] = MultipleChoiceField(
            choices=phone_number_choices,
            label="Phone number",
            widget=CheckboxSelectMultiple(),
            help_text=(
                "Select one or more phone numbers."
                if len(phone_number_choices) > 1
                else ""
                if len(phone_number_choices) == 1
                else "No phone number to select."
            ),
            required=True,
            initial=False,
            error_messages={"required": "Select at least one phone number."},
        )

        postcode_choices = [(postcode, postcode) for postcode in unique_postcodes]
        self.fields["residential_postcodes"] = MultipleChoiceField(
            choices=postcode_choices,
            label="Residential postcode",
            widget=CheckboxSelectMultiple(),
            help_text=(
                "Select one or more postcodes."
                if len(postcode_choices) > 1
                else ""
                if len(postcode_choices) == 1
                else "No postcode to select."
            ),
            required=True,
            initial=False,
            error_messages={"required": "Select at least one residential postcode."},
        )

        # Conditionally append form options or read only fields to the layout
        form_options = [
            {
                "data": unique_first_names,
                "field_name": "first_name",
                "label": "First name",
            },
            {
                "data": unique_last_names,
                "field_name": "last_name",
                "label": "Last name",
            },
            {"data": unique_sex, "field_name": "sex", "label": "Sex"},
            {
                "data": unique_date_of_birth,
                "field_name": "date_of_birth",
                "label": "Date of birth",
            },
            {
                "data": unique_emails,
                "field_name": "email_address",
                "label": "Email addresses",
            },
            {
                "data": unique_phone_numbers,
                "field_name": "phone_numbers",
                "label": "Phone numbers",
            },
            {
                "data": unique_postcodes,
                "field_name": "residential_postcodes",
                "label": "Residential postcodes",
            },
        ]

        return form_options

    def get_guest_form_options(self) -> list[dict]:
        # Work out which fields already match
        unique_first_names = {
            record.first_name for record in self.records if record.first_name
        }
        unique_last_names = {
            record.last_name for record in self.records if record.last_name
        }
        unique_sex = {record.gender for record in self.records if record.gender}
        unique_date_of_birth = {
            record.date_of_birth for record in self.records if record.date_of_birth
        }
        unique_emails = {
            email for record in self.records if record.email for email in record.email
        }
        unique_phone_numbers = {
            number for record in self.records if record.phone for number in record.phone
        }
        unique_passport_numbers = {
            passport_number
            for record in self.records
            if record.passport_id
            for passport_number in record.passport_id
        }
        unique_application_numbers = {
            application_number
            for record in self.records
            if record.application_number
            for application_number in record.application_number
        }
        unique_visa_statuses = {
            record.visa_status for record in self.records if record.visa_status
        }

        # Create the form options
        first_name_choices = [
            (first_name, first_name) for first_name in unique_first_names
        ]
        self.fields["first_name"] = ChoiceField(
            choices=first_name_choices,
            label="First name",
            widget=RadioSelect(),
            help_text=(
                "Select a first name."
                if len(first_name_choices) > 1
                else ""
                if len(first_name_choices) == 1
                else "No first name to select."
            ),
            error_messages={"required": "Select a first name."},
        )

        last_name_choices = [(last_name, last_name) for last_name in unique_last_names]
        self.fields["last_name"] = ChoiceField(
            choices=last_name_choices,
            label="Last name",
            widget=RadioSelect(),
            help_text=(
                "Select a last name."
                if len(last_name_choices) > 1
                else ""
                if len(last_name_choices) == 1
                else "No last name to select."
            ),
            required=True,
            initial=False,
            error_messages={"required": "Select a last name."},
        )

        sex_choices = [(sex, sex) for sex in unique_sex]
        self.fields["sex"] = ChoiceField(
            choices=sex_choices,
            label="Sex",
            widget=RadioSelect(),
            help_text=(
                (
                    "Select a sex or 'no data'."
                    if any(record.gender == "No data" for record in self.records)
                    else "Select a sex."
                )
                if len(sex_choices) > 1
                else ""
                if len(sex_choices) == 1
                else "No sex to select."
            ),
            required=True,
            initial=False,
            error_messages={
                "required": (
                    "Select a sex or 'no data'."
                    if any(record.gender == "No data" for record in self.records)
                    else "Select a sex."
                )
            },
        )

        date_of_birth_choices = [
            (
                f"{date_of_birth.strftime('%-d %B %Y')}",
                f"{date_of_birth.strftime('%-d %B %Y')}",
            )
            for date_of_birth in unique_date_of_birth
        ]
        self.fields["date_of_birth"] = ChoiceField(
            choices=date_of_birth_choices,
            label="Date of birth",
            widget=RadioSelect(),
            help_text=(
                "Select a date of birth."
                if len(date_of_birth_choices) > 1
                else ""
                if len(date_of_birth_choices) == 1
                else "No date of birth to select."
            ),
            required=True,
            initial=False,
            error_messages={"required": "Select a date of birth."},
        )

        email_address_choices = [(email, email) for email in unique_emails]
        self.fields["email_address"] = MultipleChoiceField(
            choices=email_address_choices,
            label="Email address",
            widget=CheckboxSelectMultiple(),
            help_text=(
                "Select one or more email addresses."
                if len(email_address_choices) > 1
                else ""
                if len(email_address_choices) == 1
                else "No email address to select."
            ),
            required=True,
            initial=False,
            error_messages={"required": "Select at least one email address."},
        )

        phone_number_choices = [
            (phone_number, phone_number) for phone_number in unique_phone_numbers
        ]
        self.fields["phone_numbers"] = MultipleChoiceField(
            choices=phone_number_choices,
            label="Phone number",
            widget=CheckboxSelectMultiple(),
            help_text=(
                "Select one or more phone numbers."
                if len(phone_number_choices) > 1
                else ""
                if len(phone_number_choices) == 1
                else "No phone number to select."
            ),
            required=True,
            initial=False,
            error_messages={"required": "Select at least one phone number."},
        )

        passport_number_choices = [
            (passport_number, passport_number)
            for passport_number in unique_passport_numbers
        ]
        self.fields["passport_number"] = MultipleChoiceField(
            choices=passport_number_choices,
            label="Passport number",
            widget=CheckboxSelectMultiple(),
            help_text=(
                "Select one or more passport numbers."
                if len(passport_number_choices) > 1
                else ""
                if len(passport_number_choices) == 1
                else "No passport number to select."
            ),
            required=True,
            initial=False,
            error_messages={"required": "Select at least one passport number."},
        )

        application_number_choices = [
            (application_number, application_number)
            for application_number in unique_application_numbers
        ]
        self.fields["application_numbers"] = MultipleChoiceField(
            choices=application_number_choices,
            label="Visa application number and status",
            widget=CheckboxSelectMultiple(),
            help_text=(
                "All visas will be linked to the new principal record. "
                "The guest will be labelled with their latest visa status."
            ),
            required=False,
            initial=False,
        )

        chosen_visa_status = self.get_priority_visa_status(unique_visa_statuses)
        visa_status_choices = [(chosen_visa_status, chosen_visa_status)]
        self.fields["visa_status"] = ChoiceField(
            choices=visa_status_choices,
            label="Visa status",
            widget=RadioSelect(),
            help_text="All visas will be linked to the new principal record. "
            "The guest will be labelled with their latest visa status.",
            required=False,
            initial=False,
        )

        # Conditionally append form options or read only fields to the layout
        form_options = [
            {
                "data": unique_first_names,
                "field_name": "first_name",
                "label": "First name",
            },
            {
                "data": unique_last_names,
                "field_name": "last_name",
                "label": "Last name",
            },
            {"data": unique_sex, "field_name": "sex", "label": "Sex"},
            {
                "data": unique_date_of_birth,
                "field_name": "date_of_birth",
                "label": "Date of birth",
            },
            {
                "data": unique_emails,
                "field_name": "email_address",
                "label": "Email addresses",
            },
            {
                "data": unique_phone_numbers,
                "field_name": "phone_numbers",
                "label": "Phone numbers",
            },
            {
                "data": unique_passport_numbers,
                "field_name": "passport_number",
                "label": "Passport numbers",
            },
        ]

        return form_options

    def get_priority_visa_status(self, statuses: set) -> str:
        if len(statuses) == 0:
            return ""
        if len(statuses) < 2:
            return next(iter(statuses))
        rank = {
            "Arrived": 1,
            "Issued": 2,
            "Confirmed": 3,
            "Flow Visa Pending": 4,
            "Pending": 5,
            "Refused": 6,
            "Withdrawn": 7,
            "Lapsed": 8,
            "Missing Application": 9,
        }
        return min(statuses, key=lambda v: rank[v])

    def append_guest_application_number(self, layout_items):
        application_numbers_with_visa_status = (
            self.get_zipped_application_and_visa_status()
        )

        layout_items.append(
            HTML(
                render_to_string(
                    "webapp/components/forms/readonly_input_form_field.html",
                    {
                        "label": self.fields["application_numbers"].label,
                        "help_text": self.fields["application_numbers"].help_text,
                        "value": [
                            an
                            for record in self.records
                            for an in (record.application_number or [])
                        ],
                        "formatted_value": [
                            format_html(
                                "{} {}",
                                an,
                                mark_safe(
                                    render_to_string(
                                        "webapp/components/visa_status_tag/visa_status_tag.html",
                                        {"visa_status": vs},
                                    )
                                ),
                            )
                            for an, vs in application_numbers_with_visa_status
                        ],
                        "name": self["application_numbers"].html_name,
                    },
                )
            )
        )

        layout_items.append(
            HTML(
                render_to_string(
                    "webapp/components/forms/readonly_input_form_field.html",
                    {
                        "label": self.fields["visa_status"].label,
                        "help_text": self.fields["visa_status"].help_text,
                        "value": self.get_priority_visa_status(
                            {
                                record.visa_status
                                for record in self.records
                                if record.visa_status
                            }
                        ),
                        "name": self["visa_status"].html_name,
                    },
                )
            )
        )

    def append_guest_accommodation_request(self, layout_items):
        ar = MvAccommodationRequest.objects.get(
            pk=self.select_ar_data["accommodation_request"]
        )
        layout_items.append(
            HTML(
                render_to_string(
                    "webapp/components/forms/readonly_input_form_field.html",
                    {
                        "label": "Accommodation request",
                        "help_text": "This accommodation request you selected will be "
                        "linked to the new principal guest record.",
                        "value": ar.title,
                        "formatted_value": format_html(
                            "{} {}",
                            ar.title,
                            mark_safe(
                                render_to_string(
                                    "webapp/components/checks_status_tag/accommodation_checks_status_tag.html",
                                    {"accommodation_checks_status": ar.checks_status},
                                )
                            ),
                        ),
                    },
                )
            )
        )

    def get_accommodation_form_options(self) -> list[dict]:
        unique_full_addresses = {
            (record.id, record.full_address)
            for record in self.records
            if record.full_address
        }
        unique_postcodes = {
            record.postcode for record in self.records if record.postcode
        }
        unique_ltla_names = {
            record.ltla_name for record in self.records if record.ltla_name
        }
        unique_utla_names = {
            record.utla_name for record in self.records if record.utla_name
        }

        full_address_choices = [
            (record_id, full_address)
            for record_id, full_address in sorted(
                unique_full_addresses, key=lambda a: a[1]
            )
        ]
        self.fields["full_address"] = ChoiceField(
            choices=full_address_choices,
            label="Address",
            widget=RadioSelect(),
            help_text=(
                "Select an address."
                if len(full_address_choices) > 0
                else "No address to select."
            ),
            required=True,
            initial=False,
            error_messages={"required": "Select an address."},
        )

        postcode_choices = [
            (postcode.id, postcode.postcode_formatted)
            for postcode in sorted(unique_postcodes, key=lambda p: p.postcode)
        ]
        self.fields["postcode"] = ChoiceField(
            choices=postcode_choices,
            label="Postcode",
            widget=RadioSelect(),
            help_text=(
                "Select a postcode."
                if len(postcode_choices) > 1
                else ""
                if len(postcode_choices) == 1
                else "No postcode to select."
            ),
            required=True,
            initial=False,
            error_messages={"required": "Select a postcode."},
        )

        ltla_name_choices = [
            (ltla_name, ltla_name)
            for ltla_name in sorted(unique_ltla_names, key=lambda n: n)
        ]
        self.fields["ltla_name"] = ChoiceField(
            choices=ltla_name_choices,
            label="Lower tier LA",
            widget=RadioSelect(),
            help_text=(
                "Select a lower tier LA."
                if len(ltla_name_choices) > 1
                else "The lower tier authority is linked to the accommodation postcode."
                if len(ltla_name_choices) == 1
                else "No lower tier LA to select."
            ),
            required=True,
            initial=False,
            error_messages={"required": "Select a lower tier LA."},
        )

        utla_name_choices = [
            (utla_name, utla_name)
            for utla_name in sorted(unique_utla_names, key=lambda n: n)
        ]
        self.fields["utla_name"] = ChoiceField(
            choices=utla_name_choices,
            label="Upper tier LA",
            widget=RadioSelect(),
            help_text=(
                "Select an upper tier LA."
                if len(utla_name_choices) > 1
                else "The upper tier authority is linked to the accommodation postcode."
                if len(utla_name_choices) == 1
                else "No upper tier LA to select."
            ),
            required=True,
            initial=False,
            error_messages={"required": "Select an upper tier LA."},
        )

        form_options = [
            {
                "data": unique_full_addresses,
                "field_name": "full_address",
                "label": "Address",
            },
            {
                "data": unique_postcodes,
                "field_name": "postcode",
                "label": "Postcode",
            },
            {
                "data": unique_ltla_names,
                "field_name": "ltla_name",
                "label": "Lower tier LA",
            },
            {
                "data": unique_utla_names,
                "field_name": "utla_name",
                "label": "Upper tier LA",
            },
        ]
        return form_options

    def get_zipped_application_and_visa_status(self) -> list[tuple[str, str]]:
        application_number_list = [record.application_number for record in self.records]

        application_numbers = []
        for a in application_number_list:
            if isinstance(a, list):
                application_numbers.extend(a)
            else:
                application_numbers.append(a)

        visa_statuses = [
            app.visa_status
            if (
                app := VisaApplication.objects.filter(
                    application_unique_application_number=an
                ).first()
            )
            else ""
            for an in application_numbers
        ]

        return list(zip(application_numbers, visa_statuses, strict=False))


class CheckAndCompleteStepForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML(
                '<div class="govuk-button-group">'
                '<button type="submit"class="govuk-button">'
                "Yes, confirm and deduplicate</button>"
                '<button type="submit"class="govuk-button govuk-button--secondary"'
                'name="wizard_goto_step"'
                'type="submit"'
                'value="{{ wizard.steps.prev }}">'
                "No, go back to select correct information"
                "</button>"
                "</div>"
            ),
        )


class UndoDeduplicationRecordsStepForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.pop("record_id")
        self.cancel_url = kwargs.pop("cancel_url")
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML(
                '<button type="submit"class="govuk-button">Undo deduplication</button>'
            ),
            HTML(
                '<a class="govuk-link govuk-link--no-visited-state" '
                f'href="{self.cancel_url}">Cancel</a>'
            ),
        )


class UndoDeduplicateRecordsStepForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.pop("record_id")
        self.cancel_url = kwargs.pop("cancel_url")
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML(
                '<button type="submit" class="govuk-button">'
                "Yes, undo deduplication"
                "</button>"
            ),
            HTML(
                '<a class="govuk-button govuk-button--secondary" '
                f'href="{self.cancel_url}">'
                "No, return to the record</a>"
            ),
        )
