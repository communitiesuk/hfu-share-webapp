import uuid

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Button, Div, Field, Layout, Size
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Case, IntegerField, When
from django.forms import (
    CharField,
    CheckboxSelectMultiple,
    ChoiceField,
    ModelChoiceField,
    MultipleChoiceField,
    RadioSelect,
)
from django.forms.widgets import Input
from django.utils import timezone

from accommodation_requests.enums import MoveGuestsTypes
from accommodation_requests.safeguarding_utils import (
    NotificationData,
    loop_and_raise,
)
from accounts.enums import GroupType
from accounts.models import GroupInfo
from case_management.settings import sentry_sdk
from ontology.models import (
    CheckType,
    DevCheckV2,
    MvAccommodation,
    MvAccommodationRequest,
    MvPerson,
    MvVolunteer,
    SafeguardingNotification,
)
from ontology.models.DevCheckV2 import validate_sponsor_dbs_passed_subtype
from user_management.templatetags.access_request_extras import (
    render_name_label_from_group_info,
)
from webapp.utils import normalize_empty_to_none
from webapp.widgets import SearchableSelect


class CheckTypeModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        if obj.id == "1":
            return "Accommodation exists"
        if obj.id == "2":
            return "Accommodation suitable"
        if obj.id == "3":
            return "DBS check and Sponsor suitable"
        if obj.id == "4":
            return "Guests have arrived in their accommodation"
        return obj.check_name


class AccommodationRequestUpdateSafeguardingChecksForm(forms.ModelForm):
    check_type = CheckTypeModelChoiceField(
        queryset=CheckType.objects.filter(
            id__in=CheckType.ALL_REQUIRED_CHECK_IDS
        ).order_by(
            Case(
                When(id="2", then=0),
                When(id="1", then=1),
                When(id="3", then=2),
                When(id="4", then=3),
                default=4,
                output_field=IntegerField(),
            )
        ),
        initial=None,
        label="Check type",
    )

    @staticmethod
    def get_available_status_choices():
        return [
            c
            for c in DevCheckV2.CheckStatus.choices
            if c[0] != DevCheckV2.CheckStatus.UNAVAILABLE
        ]

    status = ChoiceField(
        choices=get_available_status_choices(),
        initial=DevCheckV2.CheckStatus.NOT_STARTED,
        label="Status",
    )

    accommodation_exists_failure = ChoiceField(
        choices=[
            (choice.value, choice.label)
            for choice in sorted(
                DevCheckV2.AccommExistsFailureReason,
                key=lambda choice: choice.label,
            )
        ],
        required=False,
        label="Failure reason",
    )

    accommodation_suitable_failure = ChoiceField(
        choices=[
            (choice.value, choice.label)
            for choice in sorted(
                DevCheckV2.SuitabilityFailure,
                key=lambda choice: choice.label,
            )
        ],
        required=False,
        label="Failure reason",
    )

    sponsor_dbs_passed = ChoiceField(
        choices=[
            (choice.value, choice.label)
            for choice in sorted(
                DevCheckV2.SponsorDBSPassedType,
                key=lambda choice: choice.label,
            )
        ],
        required=False,
        label="Sponsor DBS type",
    )

    sponsor_dbs_failure = ChoiceField(
        choices=[
            (choice.value, choice.label)
            for choice in sorted(
                DevCheckV2.SponsorDBSFailureReason,
                key=lambda choice: choice.label,
            )
        ],
        required=False,
        label="Failure reason",
    )

    notes = CharField(
        label="Comments",
        widget=forms.Textarea(),
        required=False,
        help_text="""
            You must enter a reason if you select
            'Sponsor is not suitable - other reasons'.
            For any other option you select, adding a comment is
            optional. The text you enter should be short and clear.
        """,
        max_length=500,
    )

    accommodations = forms.ModelChoiceField(
        queryset=MvAccommodation.objects.none(), required=False, label="Accommodation"
    )

    sponsors = forms.ModelChoiceField(
        queryset=MvVolunteer.objects.none(), required=False, label="Sponsor"
    )

    def __init__(self, *args, dev_check_v2_id=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields[
            "accommodations"
        ].queryset = self.instance.get_accommodations_restrict_for_user(self.user)
        self.fields[
            "sponsors"
        ].queryset = self.instance.get_host_and_active_sponsors_restrict_for_user(
            self.user
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.text(
                "check_type",
                legend_size=Size.SMALL,
                label_size=Size.SMALL,
            ),
            Field.text(
                "status",
                legend_size=Size.SMALL,
                label_size=Size.SMALL,
            ),
            Field.text(
                "accommodation_exists_failure",
                legend_size=Size.SMALL,
                label_size=Size.SMALL,
            ),
            Field.text(
                "accommodation_suitable_failure",
                legend_size=Size.SMALL,
                label_size=Size.SMALL,
            ),
            Field.text(
                "sponsor_dbs_failure",
                legend_size=Size.SMALL,
                label_size=Size.SMALL,
            ),
            Field.text(
                "accommodations",
                legend_size=Size.SMALL,
                label_size=Size.SMALL,
            ),
            Field.text(
                "sponsors",
                legend_size=Size.SMALL,
                label_size=Size.SMALL,
            ),
            Field.text(
                "sponsor_dbs_passed",
                legend_size=Size.SMALL,
                label_size=Size.SMALL,
            ),
            Field.textarea(
                "notes",
                legend_size=Size.SMALL,
                label_size=Size.SMALL,
                rows=5,
                max_characters=500,
            ),
            Div(
                Button.primary(
                    "submit_and_leave", "Submit and return to safeguarding checks"
                ),
                css_class="govuk-button-group govuk-!-margin-bottom-0",
            ),
            Div(
                Button.secondary("submit_and_stay", "Save and add another check"),
                HTML(
                    '<a class="govuk-link govuk-link--no-visited-state" '
                    'href="{{ cancel_url }}">Cancel</a>'
                ),
                css_class="govuk-button-group  govuk-!-margin-top-0",
            ),
        )
        self.should_raise_escalation = False
        self.escalate_sponsor = None
        self.escalate_accommodation = None
        self.dev_check_v2_id = dev_check_v2_id
        self.populate_initial()

    class Meta:
        model = DevCheckV2
        template_name = (
            "accommodation_requests/"
            "add_update_safeguarding_checks/"
            "add_update_safeguarding_checks_page.html"
        )
        fields = ()

    def populate_initial(self):
        if not self.dev_check_v2_id:
            return

        check = DevCheckV2.objects.get(id=self.dev_check_v2_id)

        self.initial.update(
            {
                "check_type": check.check_type,
                "status": check.check_status,
                "accommodations": (
                    check.accommodation.first()
                    if check.accommodation.exists()
                    else None
                ),
                "sponsors": check.sponsor.first() if check.sponsor.exists() else None,
                "sponsor_dbs_passed": (
                    validate_sponsor_dbs_passed_subtype(check.check_subtype)
                    if check.check_type_id == CheckType.Id.SPONSOR_DBS
                    and check.check_status == DevCheckV2.CheckStatus.PASSED
                    else None
                ),
                "sponsor_dbs_failure": (
                    check.check_subtype
                    if check.check_type_id == CheckType.Id.SPONSOR_DBS
                    and check.check_status == DevCheckV2.CheckStatus.FAILED
                    else None
                ),
                "accommodation_exists_failure": (
                    check.check_subtype
                    if check.check_type_id == CheckType.Id.ACCOMM_EXISTS
                    else None
                ),
                "accommodation_suitable_failure": (
                    check.check_subtype
                    if check.check_type_id == CheckType.Id.ACCOMM_SUITABLE
                    else None
                ),
                "notes": check.note,
            }
        )

    def sg_loop_and_raise(self, check):
        sponsor = self.escalate_sponsor
        accommodation = self.escalate_accommodation
        notification_data = NotificationData(
            alert_type=SafeguardingNotification.AlertType.SAFEGUARDING_CHECK,
            check=check,
            sponsor=sponsor,
            accommodation=accommodation,
        )
        loop_and_raise(self.instance, notification_data)

    def clean(self):  # noqa: C901
        cleaned = super().clean()
        check_type = cleaned.get("check_type")
        status = cleaned.get("status")

        if not check_type:
            self.add_error("check_type", "Check type is required.")
        if not status:
            self.add_error("status", "Status is required.")

        # Conditional validations
        if check_type and status:
            # ACCOM_EXISTS
            if check_type.id == CheckType.Id.ACCOMM_EXISTS:
                if not cleaned.get("accommodations"):
                    self.add_error(
                        "accommodations",
                        "Accommodation is required for this check type.",
                    )
                if status == DevCheckV2.CheckStatus.FAILED and not cleaned.get(
                    "accommodation_exists_failure"
                ):
                    self.add_error(
                        "accommodation_exists_failure",
                        "Failure reason is required when status is failed.",
                    )

            # ACCOM_SUITABLE
            elif check_type.id == CheckType.Id.ACCOMM_SUITABLE:
                if not cleaned.get("accommodations"):
                    self.add_error(
                        "accommodations",
                        "Accommodation is required for this check type.",
                    )
                if status == DevCheckV2.CheckStatus.FAILED and not cleaned.get(
                    "accommodation_suitable_failure"
                ):
                    self.add_error(
                        "accommodation_suitable_failure",
                        "Failure reason is required when status is failed.",
                    )

            # SPONSOR_DBS
            elif check_type.id == CheckType.Id.SPONSOR_DBS:
                if not cleaned.get("sponsors"):
                    self.add_error(
                        "sponsors", "Sponsor is required for this check type."
                    )
                if status == DevCheckV2.CheckStatus.PASSED and not cleaned.get(
                    "sponsor_dbs_passed"
                ):
                    self.add_error(
                        "sponsor_dbs_passed",
                        "Sponsor DBS passed type is required when status is passed.",
                    )
                if status == DevCheckV2.CheckStatus.FAILED and not cleaned.get(
                    "sponsor_dbs_failure"
                ):
                    self.add_error(
                        "sponsor_dbs_failure",
                        "Sponsor DBS failure reason is required when status is failed.",
                    )

            # GROUP_ARRIVED
            elif check_type.id == CheckType.Id.GROUP_ARRIVED:
                group = self.instance.get_group()
                if not group:
                    raise ValidationError(
                        "We are unable to find the group for this check. "
                        "Please check the accommodation request is attached to a group."
                    )

            # Check for duplicate checks (if not editing)
            if not self.dev_check_v2_id:
                qs = DevCheckV2.objects.filter(
                    check_type=check_type,
                )

                if check_type.id in [
                    CheckType.Id.ACCOMM_EXISTS,
                    CheckType.Id.ACCOMM_SUITABLE,
                ]:
                    accommodations = cleaned.get("accommodations")
                    if accommodations:
                        qs = qs.filter(accommodation=accommodations).filter(
                            AR=self.instance
                        )
                    else:
                        raise ValidationError(
                            "Accommodation is required for this check type."
                        )

                if check_type.id == CheckType.Id.SPONSOR_DBS:
                    sponsors = cleaned.get("sponsors")
                    if sponsors:
                        qs = qs.filter(sponsor=sponsors)
                    else:
                        raise ValidationError(
                            "Sponsor is required for this check type."
                        )

                if check_type.id == CheckType.Id.GROUP_ARRIVED:
                    qs = qs.filter(group=self.instance.get_group())

                if qs.exists():
                    raise ValidationError(
                        "This check already exists. "
                        "Please edit the existing check instead."
                    )

            # Escalation flag
            if (
                status == DevCheckV2.CheckStatus.FAILED
                and not check_type.id == CheckType.Id.GROUP_ARRIVED
            ):
                self.should_raise_escalation = True
                if check_type.id in [
                    CheckType.Id.ACCOMM_EXISTS,
                    CheckType.Id.ACCOMM_SUITABLE,
                ]:
                    self.escalate_accommodation = self.cleaned_data.get(
                        "accommodations", None
                    )
                elif check_type.id == CheckType.Id.SPONSOR_DBS:
                    self.escalate_sponsor = self.cleaned_data.get("sponsors", None)

        return cleaned

    def clean_accommodation_exists_failure(self):
        return normalize_empty_to_none(
            self.cleaned_data.get("accommodation_exists_failure")
        )

    def clean_accommodation_suitable_failure(self):
        return normalize_empty_to_none(
            self.cleaned_data.get("accommodation_suitable_failure")
        )

    def clean_sponsor_dbs_passed(self):
        return normalize_empty_to_none(self.cleaned_data.get("sponsor_dbs_passed"))

    def clean_sponsor_dbs_failure(self):
        return normalize_empty_to_none(self.cleaned_data.get("sponsor_dbs_failure"))

    def clean_notes(self):
        return normalize_empty_to_none(self.cleaned_data.get("notes"))

    def _create_or_update_sg_check(self, data):
        now = timezone.now()
        user = self.user if self.user else None
        user_id = str(user.id) if user else None

        if self.dev_check_v2_id:
            sg_check = DevCheckV2.objects.get(id=self.dev_check_v2_id)
        else:
            sg_check = DevCheckV2(
                id=str(uuid.uuid4()),
                check_type=data.get("check_type"),
                check_status=data.get("status"),
                create_at=now,
                create_by=user_id,
            )

        sg_check.last_updated_at = now
        sg_check.last_updated_by = user

        sg_check.check_type = data.get("check_type")
        sg_check.check_status = data.get("status")
        sg_check.note = data.get("notes")

        self._set_check_subtype(sg_check, data)
        self._set_related_fields(sg_check, data)

        self._set_person_field(sg_check, data)
        sg_check.save()

        # Send Sentry metric for updated safeguarding check
        # Don't include check subtypes or failure reasons for now
        # All attributes are string types as user_id may be None
        sentry_sdk.metrics.count(
            "safeguarding_check",
            1,
            attributes={
                "check_type": str(sg_check.check_type),
                "check_status": sg_check.check_status,
                "user_id": user_id,
            },
        )

        sg_check.create_interactions_for_check_update(
            source_ar=self.instance, author=self.user, updated_at=now
        )

        return sg_check

    def _set_check_subtype(self, sg_check, data):
        if sg_check.check_type.id == CheckType.Id.SPONSOR_DBS:
            if sg_check.check_status == DevCheckV2.CheckStatus.PASSED:
                sg_check.check_subtype = data.get("sponsor_dbs_passed")
            elif sg_check.check_status == DevCheckV2.CheckStatus.FAILED:
                sg_check.check_subtype = data.get("sponsor_dbs_failure")
            else:
                sg_check.check_subtype = None
        elif sg_check.check_status == DevCheckV2.CheckStatus.FAILED:
            if sg_check.check_type.id == CheckType.Id.ACCOMM_EXISTS:
                sg_check.check_subtype = data.get("accommodation_exists_failure")
            elif sg_check.check_type.id == CheckType.Id.ACCOMM_SUITABLE:
                sg_check.check_subtype = data.get("accommodation_suitable_failure")
            else:
                sg_check.check_subtype = None
        else:
            sg_check.check_subtype = None

    def _set_related_fields(self, sg_check, data):
        if sg_check.check_type.id in [
            CheckType.Id.ACCOMM_EXISTS,
            CheckType.Id.ACCOMM_SUITABLE,
        ]:
            sg_check.accommodation.set([data.get("accommodations")])
            sg_check.AR.set([self.instance])

        if sg_check.check_type.id == CheckType.Id.SPONSOR_DBS:
            sg_check.sponsor.set([data.get("sponsors")])

        if sg_check.check_type.id == CheckType.Id.GROUP_ARRIVED:
            sg_check.group.set([self.instance.get_group()])

        if self.instance.ltla_code_id is not None:
            sg_check.ltla_code.set(self.instance.ltla_code_id)

    def _set_person_field(self, sg_check, data):
        if sg_check.check_type.id == CheckType.Id.ACCOMM_EXISTS:
            accommodation = data.get("accommodations")
            if accommodation:
                ar_ids = MvAccommodationRequest.objects.filter(
                    accommodation_id__contains=[accommodation.id]
                ).values_list("id", flat=True)
                all_people = MvPerson.objects.filter(
                    accommodation_request_id__in=ar_ids
                )
                sg_check.person.set(all_people)
            else:
                sg_check.person.set([])
        elif sg_check.check_type.id == CheckType.Id.SPONSOR_DBS:
            sponsor = data.get("sponsors")
            if sponsor:
                sponsor_requests = MvAccommodationRequest.objects.filter(
                    primary_sponsor=sponsor
                )
                all_people = MvPerson.objects.filter(
                    accommodation_request__in=sponsor_requests
                )
                sg_check.person.set(all_people)
            else:
                sg_check.person.set([])
        else:
            sg_check.person.set(self.instance.get_people())

    def save(self, commit=True):
        data = self.cleaned_data
        # Use a transaction to ensure all operations succeed or fail together
        with transaction.atomic():
            sg_check = self._create_or_update_sg_check(data)
            if self.should_raise_escalation:
                self.sg_loop_and_raise(sg_check)

        return self.instance


class CloseAccommodationRequestForm(forms.Form):
    guests = MultipleChoiceField(
        choices=(),
        label="Select guests",
        widget=CheckboxSelectMultiple(),
        help_text="If the reason for each guest is different, "
        "you will need to repeat the process for other guests."
        "<br><br>This will mark the guests as inactive.",
        error_messages={"required": "You must select at least one guest."},
        required=False,
    )

    reason = ChoiceField(
        choices=MvAccommodationRequest.ClosedReason.choices,
        label="Reason for closing request",
        widget=RadioSelect(),
        help_text="Select whether the guest chose not to travel to the UK, "
        "or their next steps outside the Homes for Ukraine scheme.",
        error_messages={"required": "You must select a reason."},
    )

    comment = CharField(
        label="Comment",
        widget=forms.Textarea(),
        required=False,
        help_text="Add any relevant notes for audit or reporting (max 500 characters)",
        max_length=500,
    )

    def __init__(self, *args, **kwargs):
        guest_list = kwargs.pop("accommodation_request").get_people()
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios(
                "reason",
                legend_size=Size.LARGE,
            ),
            Field.textarea(
                "comment", label_size=Size.MEDIUM, rows=5, max_characters=500
            ),
            Div(
                Button("submit", "Update record"),
                HTML(
                    '<a href="{{ cancel_url }}"'
                    'class="govuk-link govuk-link--no-visited-state govuk-body">'
                    "Cancel"
                    "</a>"
                ),
                style="display: flex; gap: 16px; align-items: baseline",
            ),
        )
        if len(guest_list) > 1:
            self.fields["guests"].choices = [
                (guest.id, f"{guest.first_name} {guest.last_name}")
                for guest in guest_list
            ]
            self.fields["guests"].required = True
            self.helper.layout.insert(
                0,
                Layout(
                    Field.checkboxes(
                        "guests",
                        legend_size=Size.LARGE,
                    ),
                ),
            )

    def clean(self):
        cleaned_data = super().clean()
        reason = cleaned_data.get("reason")
        comment = cleaned_data.get("comment")

        if reason == MvAccommodationRequest.ClosedReason.OTHER and comment == "":
            msg = "Enter details for 'Other' reason."
            self.add_error("comment", ValidationError(msg))

        return cleaned_data

    def clean_comment(self):
        return normalize_empty_to_none(self.cleaned_data.get("comment"))


class ReopenAccommodationRequestForm(forms.Form):
    confirmation = forms.BooleanField(
        label="Yes, reopen this accommodation request",
        help_text="Please confirm you want to reopen this request.",
        error_messages={
            "required": "You must confirm that you want to reopen this request."
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML.h2("Are you sure you want to reopen this accommodation request?"),
            Field.checkboxes("confirmation"),
            Div(
                Button("submit", "Reopen accommodation request"),
                HTML(
                    '<a href="{{ cancel_url }}"'
                    'class="govuk-link govuk-link--no-visited-state govuk-body">'
                    "Cancel"
                    "</a>"
                ),
                css_class="govuk-button-group",
            ),
        )


class WithdrawSponsorAccommodationRequestForm(forms.Form):
    sponsors = forms.ModelMultipleChoiceField(
        queryset=MvVolunteer.objects.none(),
        label="Select sponsors",
        widget=forms.CheckboxSelectMultiple,
        help_text="Select the sponsors you want to withdraw.",
        error_messages={"required": "You must select at least one sponsor."},
    )

    reason = forms.CharField(
        widget=forms.Textarea(),
        label="Reason for withdrawing sponsor",
        help_text="Add a reason for withdrawing the sponsor. "
        "Include the visa application number (GWF) "
        "for every visa that the sponsor is withdrawing from. "
        "The text you enter should be short and clear.",
        error_messages={"required": "You must provide a reason."},
        max_length=500,
    )

    def __init__(self, *args, sponsors_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)

        if sponsors_queryset and len(sponsors_queryset) > 1:
            self.fields["sponsors"].queryset = sponsors_queryset
            self.fields["sponsors"].label_from_instance = (
                lambda sponsor: sponsor.get_full_name()
            )

            self.helper = FormHelper()
            self.helper.layout = Layout(
                Field.checkboxes("sponsors", legend_size=Size.LARGE),
                Field.textarea(
                    "reason", label_size=Size.LARGE, rows=5, max_characters=500
                ),
                Div(
                    Button("submit", "Withdraw sponsor"),
                    HTML(
                        '<a href="{{ cancel_url }}"'
                        'class="govuk-link govuk-link--no-visited-state govuk-body">'
                        "Cancel"
                        "</a>"
                    ),
                    css_class="govuk-button-group",
                ),
            )
        else:
            self.fields.pop("sponsors", None)

            self.helper = FormHelper()
            self.helper.layout = Layout(
                Field.textarea(
                    "reason", label_size=Size.LARGE, rows=5, max_characters=500
                ),
                Div(
                    Button("submit", "Withdraw sponsor"),
                    HTML(
                        '<a href="{{ cancel_url }}"'
                        'class="govuk-link govuk-link--no-visited-state govuk-body">'
                        "Cancel"
                        "</a>"
                    ),
                    css_class="govuk-button-group",
                ),
            )


class MoveGuestsFormIsStayingInLAStep(forms.Form):
    within_la = forms.ChoiceField(
        choices=[("yes", "Yes"), ("no", "No")],
        widget=forms.RadioSelect,
        label="Is the guest remaining within your local authority?",
        help_text=(
            "If you need to move one or more guests to an accommodation in your local "
            "authority, select 'Yes'."
        ),
        error_messages={"required": "You must select 'Yes' or 'No'."},
    )

    def __init__(self, *args, number_of_people, **kwargs):
        super().__init__(*args, **kwargs)

        if number_of_people > 1:
            self.fields[
                "within_la"
            ].label = "Are the guests remaining within your local authority?"

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios("within_la", legend_size=Size.LARGE, inline=True),
            Div(
                Button.primary("submit", "Continue"),
                HTML(
                    '<a href="{{ cancel_url }}"'
                    'class="govuk-link govuk-link--no-visited-state govuk-body">'
                    "Cancel"
                    "</a>"
                ),
                css_class="govuk-button-group",
            ),
        )


class MoveGuestsFormSelectGuestsStep(forms.Form):
    guests = forms.ModelMultipleChoiceField(
        queryset=MvPerson.objects.none(),
        label="Select guests",
        widget=forms.CheckboxSelectMultiple,
        help_text="You can only move guests to one address at a time. If you need to "
        "move guests on this record to another address you will need to make this "
        "change then start the process again.",
        error_messages={"required": "You must select 1 or more guests."},
    )

    def __init__(
        self,
        *args,
        move_type=MoveGuestsTypes.REMATCH,
        guests_queryset=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.fields["guests"].queryset = guests_queryset
        self.fields["guests"].label_from_instance = lambda guest: guest.get_full_name()

        if move_type == MoveGuestsTypes.REASSIGN:
            self.fields["guests"].help_text = (
                "You can only move guests to one local authority at a time. If "
                "you need to move guests on this record to another address or "
                "local authority you will need to finish this request, then start "
                "the process again."
            )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.checkboxes("guests", legend_size=Size.LARGE),
            Div(
                Button.primary("submit", "Continue"),
                HTML(
                    '<a href="{{ cancel_url }}"'
                    'class="govuk-link govuk-link--no-visited-state govuk-body">'
                    "Cancel"
                    "</a>"
                ),
                css_class="govuk-button-group",
            ),
        )


class MoveGuestsConfirmationStep(forms.Form):
    confirm_guests_moved = forms.BooleanField(
        widget=forms.CheckboxInput(),
        required=True,
        error_messages={
            "required": "Tick the box to confirm you want to move the guest(s).",
        },
    )

    def __init__(
        self,
        *args,
        move_type=MoveGuestsTypes.REMATCH,
        guests_to_move=None,
        accommodation=None,
        country=None,
        local_authority=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        moving_guests = guests_to_move or []

        # Set the confirmation text based on the move type and number of guests
        if move_type == MoveGuestsTypes.REMATCH:
            if len(moving_guests) > 1:
                confirmation_text = "Yes, move these guests to this accommodation"
            else:
                confirmation_text = "Yes, move this guest to this accommodation"
        else:
            confirmation_text = "Yes, send the request"

        self.fields["confirm_guests_moved"].label = confirmation_text

        # Set the button text based on the number of guests
        if move_type == MoveGuestsTypes.REMATCH:
            button_text = "Move guest" if len(moving_guests) == 1 else "Move guests"
        else:
            button_text = "Send request"

        destination = ""
        if accommodation:
            destination = accommodation.full_address
        elif local_authority:
            destination = local_authority
        elif country:
            destination = country.capitalize()

        # Set names based on the number of guests moved
        names = moving_guests[0].get_full_name()
        if len(moving_guests) > 1:
            names_list = [guests.get_full_name() for guests in moving_guests]
            names = ", ".join(names_list[:-1]) + f" and {names_list[-1]}"

        headline = f"Are you sure you want to move {names} to {destination}?"

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                HTML.h2(headline),
                Field.checkboxes("confirm_guests_moved", legend_size=Size.LARGE),
                Div(
                    Button.primary("move_guests", button_text),
                    HTML(
                        '<a href="{{ cancel_url }}"'
                        'class="govuk-link govuk-link--no-visited-state govuk-body">'
                        "Cancel"
                        "</a>"
                    ),
                    css_class="govuk-button-group",
                ),
            ),
        )


class MoveGuestsSelectAccommodationStep(forms.Form):
    accommodation = ModelChoiceField(
        queryset=MvAccommodation.objects.all(), widget=Input()
    )


class MoveGuestsFormSelectCountryStep(forms.Form):
    country = forms.ChoiceField(
        choices=[
            ("England", "England"),
            ("Scotland", "Scotland"),
            ("Northern Ireland", "Northern Ireland"),
            ("Wales", "Wales"),
        ],
        label="Select where to move the guest to",
        help_text="You will need to select a local authority at the next step.",
        widget=forms.RadioSelect(),
        error_messages={
            "required": "You must select a country.",
        },
    )

    def __init__(self, *args, number_of_people=0, **kwargs):
        super().__init__(*args, **kwargs)

        if number_of_people > 1:
            self.fields["country"].label = "Select where to move the guests to"

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios("country", legend_size=Size.LARGE),
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


class MoveGuestsFormSelectLocalAuthorityStep(forms.Form):
    local_authority = forms.ModelChoiceField(
        queryset=GroupInfo.objects.none(),
        to_field_name="ltla_name",
        empty_label="",
        label="Select local authority",
        widget=SearchableSelect(),
        error_messages={
            "required": "You must select a local authority.",
        },
    )

    def __init__(self, *args, number_of_people=0, country=None, **kwargs):
        super().__init__(*args, **kwargs)

        heading = (
            "Select where to move the guests to"
            if number_of_people > 1
            else "Select where to move the guest to"
        )

        if country is not None:
            self.fields["local_authority"].queryset = GroupInfo.objects.filter(
                group_type=GroupType.LOCAL_AUTHORITY,
                is_utla=False,
                da_name=country,
            ).order_by("group__name")

        self.fields[
            "local_authority"
        ].label_from_instance = render_name_label_from_group_info
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML.h2(heading),
            Field.text("local_authority", label_size=Size.MEDIUM),
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


class MoveGuestsFormReasonStep(forms.Form):
    reason = forms.CharField(
        label="Reason for moving guest",
        help_text="You must add a reason. "
        "The text you enter should be short and clear.",
        widget=forms.Textarea(),
        max_length=500,
        error_messages={
            "required": "You must enter a reason.",
        },
    )

    def __init__(self, *args, number_of_people=0, **kwargs):
        super().__init__(*args, **kwargs)

        if number_of_people > 1:
            self.fields["reason"].label = "Reason for moving guests"

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.textarea("reason", label_size=Size.LARGE, rows=5, max_characters=500),
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
