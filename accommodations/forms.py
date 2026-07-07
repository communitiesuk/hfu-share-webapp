from datetime import datetime, timedelta

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Field, Fieldset, Fluid, Layout
from crispy_forms_gds.layout.constants import Size
from django import forms
from django.urls import reverse

from ontology.models import MvAccommodation, MvUkPostcode
from webapp.mixins import ReadOnlyFieldsMixin
from webapp.widgets import DatePicker, SearchableSelectLazy


class AccommodationEditForm(ReadOnlyFieldsMixin, forms.ModelForm):
    full_address = forms.CharField(
        label="Address",
        widget=forms.Textarea(attrs={"required": True, "rows": 4}),
        error_messages={"required": "Please enter a valid UK address"},
    )

    postcode = forms.CharField(
        label="Postcode",
        required=False,
        widget=SearchableSelectLazy(
            attrs={
                "required": False,
                "error_messages": {"required": "Please select a valid UK postcode"},
            }
        ),
    )

    current_capacity = forms.IntegerField(
        label="Current capacity (optional)",
        widget=forms.TextInput(attrs={"inputmode": "numeric"}),
        required=False,
    )

    availability_start_date = forms.DateField(
        label="Availability start date (optional)",
        widget=DatePicker(
            attrs={
                "hint": f"For example "
                f"{(datetime.today() - timedelta(days=20)).strftime('%d/%m/%Y')}",
            }
        ),
        required=False,
    )

    availability_end_date = forms.DateField(
        label="Availability end date (optional)",
        widget=DatePicker(
            attrs={
                "hint": f"For example "
                f"{(datetime.today() + timedelta(days=20)).strftime('%d/%m/%Y')}",
            }
        ),
        required=False,
    )

    wheelchair_accessible = forms.BooleanField(
        label="Yes, accommodation is wheelchair accessible",
        widget=forms.CheckboxInput(),
        required=False,
        initial=False,
    )

    def __init__(self, *args, user=None, accommodation=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user

        default_value = (
            MvUkPostcode.objects.get_for_user(user)
            .filter(id=accommodation.postcode_id)
            .only("id", "postcode_formatted")
            .first()
        )

        self.fields["postcode"].widget.attrs.update(
            {
                "data_ajax_url": reverse("accommodations:postcode-search"),
                "default": default_value.postcode_formatted if default_value else "",
            }
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.text("full_address", label_size=Size.SMALL),
            Field.text("postcode", label_size=Size.SMALL),
            Field.text(
                "current_capacity", label_size=Size.SMALL, field_width=Fluid.ONE_THIRD
            ),
            Field(
                "availability_start_date",
                context={
                    "label_size": "govuk-fieldset__legend--s",
                },
            ),
            Field(
                "availability_end_date",
                context={
                    "label_size": "govuk-fieldset__legend--s",
                },
            ),
            Fieldset(
                Field.checkboxes("wheelchair_accessible", legend_size=Size.SMALL),
                legend="Wheelchair accessible (optional)",
                legend_size=Size.SMALL,
            ),
            HTML(self.render_readonly_field("Upper tier LA", "utla_name")),
            HTML(self.render_readonly_field("Lower tier LA", "ltla_name")),
            HTML(
                '<div class="govuk-button-group">'
                '    <button type="submit" class="govuk-button">Update</button>'
                '    <a class="govuk-link govuk-link--no-visited-state"\n'
                '       href="{{ cancel_url }}">Cancel</a>'
                "</div>"
            ),
        )

    def clean_postcode(self):
        postcode_value = self.cleaned_data.get("postcode")

        postcode = (
            MvUkPostcode.objects.get_for_user(self.user)
            .filter(postcode_formatted=postcode_value)
            .first()
        )

        if postcode is None:
            raise forms.ValidationError("Invalid postcode selected.")

        return postcode

    @staticmethod
    def postcode_label_from_instance(obj):
        return obj.postcode_formatted

    class Meta:
        model = MvAccommodation
        template_name = "accommodations/edit_view/edit_view_question.html"
        fields = (
            "full_address",
            "postcode",
            "current_capacity",
            "availability_start_date",
            "availability_end_date",
            "wheelchair_accessible",
        )
