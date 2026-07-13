import logging
import os
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any, List

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Fieldset, Layout, Size
from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Q
from django.forms import CheckboxInput, CheckboxSelectMultiple
from django.http import Http404, HttpRequest
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.views.generic import FormView, TemplateView
from django_filters import BooleanFilter, CharFilter, FilterSet, MultipleChoiceFilter
from django_filters.views import FilterView
from django_tables2 import (
    Column,
    LazyPaginator,
    MultiTableMixin,
    SingleTableMixin,
    SingleTableView,
)
from django_tables2 import (
    tables as dj_tables,
)
from formtools.wizard.views import NamedUrlSessionWizardView

from accounts.enums import GroupType
from case_management.settings import sentry_sdk
from deduplication.constants import DEDUP_SPONSORS_SEARCH_FIELDS
from deduplication.forms import (
    CheckAndCompleteStepForm,
    ReviewSelectedRecordsStepForm,
    SelectAccommodationRequestStepForm,
    SelectAndReviewRecordStepForm,
    SelectCorrectDetailsStepForm,
    SelectRecordTypeForm,
    UndoDeduplicateRecordsStepForm,
    UndoDeduplicationRecordsStepForm,
    ViewSelectedRecordsStepForm,
)
from deduplication.models import (
    AccommodationDuplicateGroup,
    GuestDuplicateGroup,
    SponsorDuplicateGroup,
)
from ontology.models import (
    MvAccommodation,
    MvAccommodationRequest,
    MvPerson,
    MvUkPostcode,
    MvVolunteer,
    ReassignmentRequest,
)
from visa_applications.templatetags.visa_application_extras import (
    visa_status_to_tag_colour,
)
from webapp.constants import (
    ACCOMMODATION_SEARCH_FIELDS,
    FIX_DUPLICATE_RECORDS_ALLOWED_GROUP_TYPES,
    GUEST_SEARCH_FIELDS,
    visa_status_list,
)
from webapp.mixins import FilterPanelMixin, PermissionsMixin
from webapp.search import perform_search
from webapp.utils import (
    CustomDateColumn,
    CustomDateFromToRangeFilter,
    CustomDateTimeColumn,
)
from webapp.widgets import CheckboxSelectMultipleWithTags, DatePicker, StackedRangeInput

logger = logging.getLogger(__name__)


def get_non_principal_records(records):
    return [record for record in records if not record.is_principal]


def non_principal_records_error_message(record_names: List[str]) -> str:
    outcome = "No new principal record was created."
    if len(record_names) == 1:
        return f"The {record_names[0]} record has already been deduplicated. {outcome}"

    joined_names = ", ".join(record_names)
    return (
        f"The following records have already been deduplicated: {joined_names}. "
        f"{outcome}"
    )


class SelectAndReviewRecordsStep(StrEnum):
    SELECT_RECORD = "select-record"
    VIEW_SELECTED_RECORDS = "view-selected-records"
    REVIEW_SELECTED_RECORDS = "review-selected-records"
    SELECT_ACCOMMODATION_REQUEST = "select-accommodation-request"
    SELECT_CORRECT_DETAILS = "select-correct-details"
    CHECK_AND_COMPLETE = "check-and-complete"


SELECT_AND_REVIEW_RECORDS_FORMS = [
    (SelectAndReviewRecordsStep.SELECT_RECORD, SelectAndReviewRecordStepForm),
    (SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS, ViewSelectedRecordsStepForm),
    (SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS, ReviewSelectedRecordsStepForm),
    (
        SelectAndReviewRecordsStep.SELECT_ACCOMMODATION_REQUEST,
        SelectAccommodationRequestStepForm,
    ),
    (SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS, SelectCorrectDetailsStepForm),
    (SelectAndReviewRecordsStep.CHECK_AND_COMPLETE, CheckAndCompleteStepForm),
]

SELECT_AND_REVIEW_FORM_TEMPLATES = {
    SelectAndReviewRecordsStep.SELECT_RECORD: "select_records_list_step.html",  # noqa: E501
    SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS: "view_selected_records_list_step.html",  # noqa: E501
    SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS: "review_selected_records_list_step.html",  # noqa: E501
    SelectAndReviewRecordsStep.SELECT_ACCOMMODATION_REQUEST: "select_accommodation_request_step.html",  # noqa: E501
    SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS: "select_correct_details_step.html",  # noqa: E501
    SelectAndReviewRecordsStep.CHECK_AND_COMPLETE: "check_and_complete_records_step.html",  # noqa: E501
}


class UndoDeduplicationRecordsStep(StrEnum):
    VIEW_DUPLICATE_RECORDS = "view-duplicate-records"
    UNDO_DEDUPLICATE_RECORDS = "undo-deduplicate-records"
    DEDUPLICATED_RECORDS_RESTORED = "deduplicated-records-restored"


UNDO_DEDUPLICATION_RECORDS_FORMS = [
    (
        UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
        UndoDeduplicationRecordsStepForm,
    ),
    (
        UndoDeduplicationRecordsStep.UNDO_DEDUPLICATE_RECORDS,
        UndoDeduplicateRecordsStepForm,
    ),
    (
        UndoDeduplicationRecordsStep.DEDUPLICATED_RECORDS_RESTORED,
        UndoDeduplicateRecordsStepForm,
    ),
]

UNDO_DEDUPLICATION_FORM_TEMPLATES = {
    UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS: "view_duplicate_records_list_step.html",  # noqa: E501
    UndoDeduplicationRecordsStep.UNDO_DEDUPLICATE_RECORDS: "undo_deduplicate_records_step.html",  # noqa: E501
    UndoDeduplicationRecordsStep.DEDUPLICATED_RECORDS_RESTORED: "deduplicated_records_restored_step.html",  # noqa: E501
}


## DEDUPLICATION
# Select object type
class SelectRecordTypeView(PermissionsMixin, FormView):
    template_name = "select_duplicate_record_type.html"
    form_class = SelectRecordTypeForm

    def get_group_type(self):
        if settings.FIX_DUPLICATE_RECORDS_ENABLED:
            return list(FIX_DUPLICATE_RECORDS_ALLOWED_GROUP_TYPES)
        return [GroupType.DEV]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # TEMP: Only show the 'Guests' option to users in the DEV group
        show_guests_option = False
        if self.request.user.groups.filter(name="dev").exists():
            show_guests_option = True
        kwargs["show_guests_option"] = show_guests_option
        return kwargs

    def form_valid(self, form):
        value = form.cleaned_data["object_choice"]
        if value == "Accommodation":
            redirect_url = (
                reverse("deduplication:accommodations:select-and-review-records-manual")
                + "?reset=true"
            )
        elif value == "Guests":
            redirect_url = (
                reverse("deduplication:guests:select-and-review-records-manual")
                + "?reset=true"
            )
        else:
            redirect_url = (
                reverse("deduplication:sponsors:select-and-review-records-manual")
                + "?reset=true"
            )

        return redirect(redirect_url)


# Select records for deduplication
def _get_selected_ltla_list(selected_record_ids: List[str], object_type) -> List[str]:
    selected_ltla_list: List[str] = []

    for record_id in selected_record_ids:
        if object_type == "guest":
            _extend_selected_ltla_list_for_guests(record_id, selected_ltla_list)
        elif object_type == "sponsor":
            _extend_selected_ltla_list_for_sponsors(record_id, selected_ltla_list)
        elif object_type == "accommodation":
            _extend_selected_ltla_list_for_accommodations(record_id, selected_ltla_list)

    return selected_ltla_list


def _extend_selected_ltla_list_for_guests(guest_id: str, selected_ltla_list: List[str]):
    guest = MvPerson.objects.get(pk=guest_id)
    accommodation_request = guest.get_accommodation_request()
    if accommodation_request.ltla_name:
        selected_ltla_list.extend(accommodation_request.ltla_name)


def _extend_selected_ltla_list_for_sponsors(
    sponsor_id: str, selected_ltla_list: List[str]
):
    sponsor = MvVolunteer.objects.get(pk=sponsor_id)
    accommodations = sponsor.accommodations.all()
    selected_ltla_list.extend([ac.ltla_name for ac in accommodations if ac.ltla_name])


def _extend_selected_ltla_list_for_accommodations(
    accommodation_id: str, selected_ltla_list: List[str]
):
    accommodation = MvAccommodation.objects.get(pk=accommodation_id)
    if accommodation.ltla_name:
        selected_ltla_list.append(accommodation.ltla_name)


# Sponsors
class ManualSponsorDeduplicationFilter(FilterSet, FilterPanelMixin):
    sex = MultipleChoiceFilter(
        choices=[
            ("Male", "Male"),
            ("Female", "Female"),
        ],
        null_label="No data",
        label="Sex",
        field_name="sex",
        widget=CheckboxSelectMultiple(),
        distinct=True,
    )

    date_of_birth = CustomDateFromToRangeFilter(
        label="Date of birth",
        field_name="date_of_birth",
        widget=StackedRangeInput(
            sub_widget=DatePicker,
            attrs={
                "from_hint": f"For example "
                f"{(datetime.today() - timedelta(days=10000)).strftime('%d/%m/%Y')}",
                "to_hint": f"For example "
                f"{(datetime.today() - timedelta(days=20)).strftime('%d/%m/%Y')}",
                "from_label": "Date from",
                "to_label": "Date to",
            },
        ),
        distinct=True,
        error_messages={
            "invalid_range": "'Date from' must be before 'Date to'.",
        },
    )

    search = CharFilter(
        label="Search",
        method="search_filter",
        help_text="Search the data in the table",
    )

    is_eoi = BooleanFilter(
        label="Show only EOI hosts",
        widget=CheckboxInput(attrs={"value": "Yes"}),
        method="show_eoi_hosts",
    )

    created_date = CustomDateFromToRangeFilter(
        label="Date added",
        field_name="created_date",
        widget=StackedRangeInput(
            sub_widget=DatePicker,
            attrs={
                "from_hint": f"For example "
                f"{(datetime.today() - timedelta(days=1000)).strftime('%d/%m/%Y')}",
                "to_hint": f"For example "
                f"{(datetime.today() - timedelta(days=20)).strftime('%d/%m/%Y')}",
                "from_label": "Date from",
                "to_label": "Date to",
            },
        ),
        distinct=True,
        error_messages={
            "invalid_range": "'Date from' must be before 'Date to'.",
        },
    )

    def show_eoi_hosts(self, queryset, _, value):
        if not value:
            return queryset

        return queryset.filter(is_eoi=value)

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, DEDUP_SPONSORS_SEARCH_FIELDS)

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
            Field.checkboxes("sex", small=True, legend_size=Size.MEDIUM),
            Field(
                "date_of_birth",
                context={
                    "legend_size": "govuk-fieldset__legend--m",
                },
            ),
            Fieldset(
                "is_eoi",
                legend="EOI host",
                legend_size=Size.MEDIUM,
                css_class="govuk-!-margin-bottom-5",
            ),
            Field(
                "created_date",
                context={
                    "legend_size": "govuk-fieldset__legend--m",
                },
            ),
        )
        return form

    class Meta:
        model = MvVolunteer
        fields = [
            "search",
            "sex",
            "date_of_birth",
            "is_eoi",
            "created_date",
        ]


class ManualSponsorDeduplicationTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    full_name = Column(verbose_name="Name", order_by=("first_name", "last_name"))
    sex = Column(verbose_name="Sex")
    date_of_birth = CustomDateColumn(verbose_name="Date of birth")
    email = Column(verbose_name="Email address")
    phone_number = Column(verbose_name="Phone number")
    is_eoi = Column(verbose_name="EOI host")
    created_date = CustomDateTimeColumn(verbose_name="Date added")
    select = Column(accessor="pk", verbose_name="", orderable=False)

    def render_full_name(self, record: MvVolunteer, value):
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{url}">{value}</a>',
            url=reverse("sponsors:detail-overview", args=[record.id]),
            value=value,
        )

    def render_is_eoi(self, value):
        return "True" if value is True else "False"

    def render_select(self, value):
        hidden_sponsor_inputs = mark_safe(
            "".join(
                [
                    format_html(
                        '<input type="hidden" name="select-record-sponsor_record" '
                        'id="id_select-record-sponsor_record" value="{value}"/>',
                        value=pk,
                    )
                    for pk in self.context["selected_ids"]
                ]
            )
        )
        return format_html(
            '<form method="post">'
            "{management_form}"
            "{hidden_sponsor_inputs}"
            '<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}"/>'
            '<input type="hidden" name="select-record-sponsor_record"'
            'id="id_select-record-sponsor_record" value="{value}"/>'
            '<button type="submit" name="submit" class="govuk-link">Select</button>'
            "</form>",
            management_form=self.context["wizard"]["management_form"],
            value=value,
            csrf_token=get_token(self.request),
            hidden_sponsor_inputs=hidden_sponsor_inputs,
        )

    class Meta:
        model = MvVolunteer
        template_name = "webapp/components/tables/table.html"
        fields = (
            "full_name",
            "sex",
            "date_of_birth",
            "email",
            "phone_number",
            "is_eoi",
            "created_date",
            "select",
        )


class SelectAndReviewRecordsSponsorListStepView(
    PermissionsMixin, SingleTableMixin, FilterView
):
    model = MvVolunteer
    table_class = ManualSponsorDeduplicationTable
    filterset_class = ManualSponsorDeduplicationFilter
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    paginator_class = LazyPaginator
    template_name = "select_records_list_step.html"

    def __init__(self, **kwargs):
        self.filterset = None
        self.object_list = None
        self.selected_sponsor_ids = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = [
            "id",
            "first_name",
            "last_name",
            "sex",
            "date_of_birth",
            "email",
            "phone_number",
            "is_eoi",
            "created_date",
            "is_principal",
        ]

        queryset = (
            super()
            .get_queryset()
            .only(*fields_needed)
            .annotate(ltla_count=Count("accommodations__ltla_name", distinct=True))
            .filter(
                ~Q(pk__in=self.selected_sponsor_ids),
                ltla_count__lte=1,
                is_principal=True,
                sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
            )
        )

        if self.selected_sponsor_ids:
            queryset = queryset.filter(
                accommodations__ltla_name__in=_get_selected_ltla_list(
                    self.selected_sponsor_ids, "sponsor"
                )
            )

        return queryset

    def get_context_data(self, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)

        if (
            not self.filterset.is_bound
            or self.filterset.is_valid()
            or not self.get_strict()
        ):
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()

        return super().get_context_data(
            filter=self.filterset, object_list=self.object_list
        )


# Guests
class ManualGuestDeduplicationFilter(FilterSet, FilterPanelMixin):
    search = CharFilter(
        label="Search",
        method="search_filter",
        help_text="Search the data in the table",
    )

    sex = MultipleChoiceFilter(
        choices=[
            ("Male", "Male"),
            ("Female", "Female"),
        ],
        null_label="No Data",
        label="Sex",
        field_name="gender",
        widget=CheckboxSelectMultiple(),
        distinct=True,
        method="filter_sex",
    )

    date_of_birth = CustomDateFromToRangeFilter(
        label="Date of birth",
        field_name="date_of_birth",
        widget=StackedRangeInput(
            sub_widget=DatePicker,
            attrs={
                "from_hint": f"For example "
                f"{(datetime.today() - timedelta(days=10000)).strftime('%d/%m/%Y')}",
                "to_hint": f"For example "
                f"{(datetime.today() - timedelta(days=20)).strftime('%d/%m/%Y')}",
                "from_label": "Date from",
                "to_label": "Date to",
            },
        ),
        distinct=True,
        error_messages={
            "invalid_range": "'Date from' must be before 'Date to'.",
        },
    )

    visa_status = MultipleChoiceFilter(
        choices=[(value.name, value.name) for value in visa_status_list],
        label="Visa status",
        widget=CheckboxSelectMultipleWithTags(
            label_to_tag_colour=visa_status_to_tag_colour
        ),
    )

    first_arrival_date = CustomDateFromToRangeFilter(
        label="First arrival date",
        field_name="arrival_date",
        widget=StackedRangeInput(
            sub_widget=DatePicker,
            attrs={
                "from_hint": f"For example "
                f"{(datetime.today() - timedelta(days=10000)).strftime('%d/%m/%Y')}",
                "to_hint": f"For example "
                f"{(datetime.today() - timedelta(days=20)).strftime('%d/%m/%Y')}",
                "from_label": "Date from",
                "to_label": "Date to",
            },
        ),
        distinct=True,
        error_messages={
            "invalid_range": "'Date from' must be before 'Date to'.",
        },
    )

    visa_application_date_maximum = CustomDateFromToRangeFilter(
        label="Latest visa application date",
        field_name="visa_application_date_maximum",
        widget=StackedRangeInput(
            sub_widget=DatePicker,
            attrs={
                "from_hint": f"For example "
                f"{(datetime.today() - timedelta(days=10000)).strftime('%d/%m/%Y')}",
                "to_hint": f"For example "
                f"{(datetime.today() - timedelta(days=20)).strftime('%d/%m/%Y')}",
                "from_label": "Date from",
                "to_label": "Date to",
            },
        ),
        distinct=True,
        error_messages={
            "invalid_range": "'Date from' must be before 'Date to'.",
        },
    )

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, GUEST_SEARCH_FIELDS)

    def filter_sex(self, queryset, name, value):
        null_value = self.filters["sex"].null_value
        query = Q(**{f"{name}__in": list(value)}) if value else Q()
        if null_value in value:
            query |= Q(**{f"{name}": "Unspecified"})
            query |= Q(**{f"{name}__isnull": True})
        return queryset.filter(query).distinct()

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
            Field.checkboxes("sex", small=True, legend_size=Size.MEDIUM),
            Field(
                "date_of_birth",
                context={
                    "legend_size": "govuk-fieldset__legend--m",
                },
            ),
            Field("visa_status", context={"label_size": "govuk-fieldset__legend--m"}),
            Field(
                "first_arrival_date",
                context={
                    "legend_size": "govuk-fieldset__legend--m",
                },
            ),
            Field(
                "visa_application_date_maximum",
                context={
                    "legend_size": "govuk-fieldset__legend--m",
                },
            ),
        )
        return form

    class Meta:
        model = MvPerson
        fields = [
            "search",
            "sex",
            "date_of_birth",
            "visa_status",
            "first_arrival_date",
            "visa_application_date_maximum",
        ]


class ManualGuestDeduplicationTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    get_full_name = Column(verbose_name="Name", order_by=("first_name", "last_name"))
    gender = Column(verbose_name="Sex")
    date_of_birth = CustomDateColumn(verbose_name="Date of birth")
    passport_id = Column(verbose_name="Passport number")
    visa_status = Column(verbose_name="Visa status")
    arrival_date = CustomDateColumn(verbose_name="First arrival date")
    visa_application_date_maximum = CustomDateColumn(
        verbose_name="Latest visa application date"
    )
    application_number = Column(verbose_name="Unique Application Number (UAN)")
    select = Column(accessor="pk", verbose_name="", orderable=False)

    def render_get_full_name(self, record: MvPerson, value):
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{url}">{value}</a>',
            url=reverse("guests:detail-overview", args=[record.id]),
            value=value,
        )

    def render_select(self, value):
        hidden_guest_inputs = mark_safe(
            "".join(
                [
                    format_html(
                        '<input type="hidden" name="select-record-guest_record" '
                        'id="id_select-record-guest_record" value="{value}"/>',
                        value=pk,
                    )
                    for pk in self.context["selected_ids"]
                ]
            )
        )
        return format_html(
            '<form method="post">'
            "{management_form}"
            "{hidden_guest_inputs}"
            '<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}"/>'
            '<input type="hidden" name="select-record-guest_record"'
            'id="id_select-record-guest_record" value="{value}"/>'
            '<button type="submit" name="submit" class="govuk-link">Select</button>'
            "</form>",
            management_form=self.context["wizard"]["management_form"],
            value=value,
            csrf_token=get_token(self.request),
            hidden_guest_inputs=hidden_guest_inputs,
        )

    def render_visa_status(self, value):
        return render_to_string(
            "webapp/components/visa_status_tag/visa_status_tag.html",
            {"visa_status": value},
        )

    class Meta:
        model = MvPerson
        template_name = "webapp/components/tables/table.html"
        fields = (
            "get_full_name",
            "gender",
            "date_of_birth",
            "passport_id",
            "visa_status",
            "arrival_date",
            "visa_application_date_maximum",
            "application_number",
            "select",
        )


class SelectAndReviewRecordsGuestListStepView(
    PermissionsMixin, SingleTableMixin, FilterView
):
    model = MvPerson
    table_class = ManualGuestDeduplicationTable
    filterset_class = ManualGuestDeduplicationFilter
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    paginator_class = LazyPaginator
    template_name = "select_records_list_step.html"

    def __init__(self, **kwargs):
        self.filterset = None
        self.object_list = None
        self.selected_guest_ids = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = [
            "id",
            "first_name",
            "gender",
            "date_of_birth",
            "passport_id",
            "visa_status",
            "arrival_date",
            "visa_application_date_maximum",
            "application_number",
            "is_principal",
        ]

        queryset = (
            super()
            .get_queryset()
            .only(*fields_needed)
            .filter(
                ~Q(pk__in=self.selected_guest_ids),
                is_principal=True,
            )
            .filter(
                Q(accommodation_request__isnull=True)
                | Q(accommodation_request__ltla_name__isnull=True)
                | Q(accommodation_request__ltla_name__len__lte=1)
            )
            .exclude(
                Q(reassignmentrequest__outcome=ReassignmentRequest.Outcome.PENDING)
            )
        )

        if self.selected_guest_ids:
            queryset = queryset.filter(
                accommodation_request__ltla_name__overlap=_get_selected_ltla_list(
                    self.selected_guest_ids, "guest"
                )
            )

        return queryset

    def get_context_data(self, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)

        if (
            not self.filterset.is_bound
            or self.filterset.is_valid()
            or not self.get_strict()
        ):
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()

        return super().get_context_data(
            filter=self.filterset, object_list=self.object_list
        )


# Accommodations
class ManualAccommodationDeduplicationFilter(FilterSet, FilterPanelMixin):
    search = CharFilter(
        label="Search",
        method="search_filter",
        help_text="Search the data in the table",
    )

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, ACCOMMODATION_SEARCH_FIELDS)

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
        )
        return form

    class Meta:
        model = MvAccommodation
        fields = [
            "search",
        ]


class ManualAccommodationDeduplicationTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    full_address = Column(verbose_name="Address")
    postcode = Column(verbose_name="Postcode")
    ltla_name = Column(verbose_name="Lower tier LA")
    utla_name = Column(verbose_name="Upper tier LA")
    select = Column(accessor="pk", verbose_name="", orderable=False)

    def render_full_address(self, record: MvAccommodation, value):
        return format_html(
            '<a class="govuk-body-s govuk-link--no-visited-state" href="{}">{}</a>',
            reverse("accommodations:detail-overview", args=[record.id]),
            value,
        )

    def render_postcode(self, value: MvUkPostcode):
        if value.postcode_formatted:
            return value.postcode_formatted
        if value.postcode:
            return value.postcode
        return ""

    def render_select(self, value):
        hidden_accommodation_inputs = mark_safe(
            "".join(
                [
                    format_html(
                        '<input type="hidden" '
                        'name="select-record-accommodation_record" '
                        'id="id_select-record-accommodation_record" value="{value}"/>',
                        value=pk,
                    )
                    for pk in self.context["selected_ids"]
                ]
            )
        )
        return format_html(
            '<form method="post">'
            "{management_form}"
            "{hidden_accommodation_inputs}"
            '<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}"/>'
            '<input type="hidden" name="select-record-accommodation_record"'
            'id="id_select-record-accommodation_record" value="{value}"/>'
            '<button type="submit" name="submit" class="govuk-link">Select</button>'
            "</form>",
            management_form=self.context["wizard"]["management_form"],
            value=value,
            csrf_token=get_token(self.request),
            hidden_accommodation_inputs=hidden_accommodation_inputs,
        )

    class Meta:
        model = MvAccommodation
        template_name = "webapp/components/tables/table.html"
        fields = ("full_address", "postcode", "ltla_name", "utla_name", "select")


class SelectAndReviewRecordsAccommodationListStepView(
    PermissionsMixin, SingleTableMixin, FilterView
):
    model = MvAccommodation
    table_class = ManualAccommodationDeduplicationTable
    filterset_class = ManualAccommodationDeduplicationFilter
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    paginator_class = LazyPaginator
    template_name = "select_records_list_step.html"

    def __init__(self, **kwargs):
        self.filterset = None
        self.object_list = None
        self.selected_accommodation_ids = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = ["full_address", "postcode", "ltla_name", "utla_name", "is_eoi"]

        queryset = (
            super()
            .get_queryset()
            .only(*fields_needed)
            .filter(
                ~Q(pk__in=self.selected_accommodation_ids),
                is_principal=True,
            )
            .order_by("full_address")
        )

        if self.selected_accommodation_ids:
            queryset = queryset.filter(
                ltla_name__in=_get_selected_ltla_list(
                    self.selected_accommodation_ids, "accommodation"
                )
            )

        return queryset

    def get_context_data(self, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)

        if (
            not self.filterset.is_bound
            or self.filterset.is_valid()
            or not self.get_strict()
        ):
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()

        return super().get_context_data(
            filter=self.filterset, object_list=self.object_list
        )


# View selected records for deduplication
# Sponsors
class ManualViewSelectedSponsorsTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    full_name = Column(verbose_name="Name", order_by=("first_name", "last_name"))
    sex = Column(verbose_name="Sex")
    date_of_birth = CustomDateColumn(verbose_name="Date of birth")
    email = Column(verbose_name="Email address")
    phone_number = Column(verbose_name="Phone number")
    is_eoi = Column(verbose_name="EOI host")
    created_date = CustomDateTimeColumn(verbose_name="Date added")
    remove = Column(accessor="pk", verbose_name="", orderable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if len(self.data) <= 1:
            for column in self.columns:
                column.column.orderable = False

    def render_full_name(self, record: MvVolunteer, value):
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{url}">{value}</a>',
            url=reverse("sponsors:detail-overview", args=[record.id]),
            value=value,
        )

    def render_is_eoi(self, value):
        return "True" if value is True else "False"

    def render_remove(self, value):
        return format_html(
            '<form method="post">'
            "{management_form}"
            '<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}"/>'
            '<input type="hidden" '
            'name="review-selected-records-sponsor_record_to_remove"'
            'id="id_review-selected-records-sponsor_record_to_remove" value="{value}"/>'
            '<button type="submit" name="submit" class="govuk-link">Remove</button>'
            "</form>",
            management_form=self.context["wizard"]["management_form"],
            value=value,
            csrf_token=get_token(self.request),
        )

    class Meta:
        model = MvVolunteer
        template_name = "webapp/components/tables/table.html"
        fields = (
            "full_name",
            "sex",
            "date_of_birth",
            "email",
            "phone_number",
            "is_eoi",
            "created_date",
            "remove",
        )


class SelectAndReviewRecordsSponsorViewSelectionStepView(
    PermissionsMixin, SingleTableView
):
    model = MvVolunteer
    table_class = ManualViewSelectedSponsorsTable
    template_name = "view_selected_records_list_step.html"

    def __init__(self, **kwargs):
        self.selected_sponsor_ids = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = [
            "id",
            "first_name",
            "last_name",
            "sex",
            "date_of_birth",
            "email",
            "phone_number",
            "is_eoi",
            "created_date",
        ]

        data = (
            super()
            .get_queryset()
            .only(*fields_needed)
            .filter(pk__in=self.selected_sponsor_ids)
        )
        return data

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()

        return super().get_context_data(object_list=self.object_list)


# Guests
class ManualViewSelectedGuestsTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    get_full_name = Column(verbose_name="Name", order_by=("first_name", "last_name"))
    gender = Column(verbose_name="Sex")
    date_of_birth = CustomDateColumn(verbose_name="Date of birth")
    passport_id = Column(verbose_name="Passport number")
    visa_status = Column(verbose_name="Visa status")
    arrival_date = CustomDateColumn(verbose_name="First arrival date")
    visa_application_date_maximum = CustomDateColumn(
        verbose_name="Latest visa application date"
    )
    application_number = Column(verbose_name="Unique Application Number (UAN)")
    remove = Column(accessor="pk", verbose_name="", orderable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if len(self.data) <= 1:
            for column in self.columns:
                column.column.orderable = False

    def render_get_full_name(self, record: MvPerson, value):
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{url}">{value}</a>',
            url=reverse("guests:detail-overview", args=[record.id]),
            value=value,
        )

    def render_remove(self, value):
        return format_html(
            '<form method="post">'
            "{management_form}"
            '<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}"/>'
            '<input type="hidden" name="review-selected-records-guest_record_to_remove"'
            'id="id_review-selected-records-guest_record_to_remove" value="{value}"/>'
            '<button type="submit" name="submit" class="govuk-link">Remove</button>'
            "</form>",
            management_form=self.context["wizard"]["management_form"],
            value=value,
            csrf_token=get_token(self.request),
        )

    def render_visa_status(self, value):
        return render_to_string(
            "webapp/components/visa_status_tag/visa_status_tag.html",
            {"visa_status": value},
        )

    class Meta:
        model = MvPerson
        template_name = "webapp/components/tables/table.html"
        fields = (
            "get_full_name",
            "gender",
            "date_of_birth",
            "passport_id",
            "visa_status",
            "arrival_date",
            "visa_application_date_maximum",
            "application_number",
            "remove",
        )


class SelectAndReviewRecordsGuestViewSelectionStepView(
    PermissionsMixin, SingleTableView
):
    model = MvPerson
    table_class = ManualViewSelectedGuestsTable
    template_name = "view_selected_records_list_step.html"

    def __init__(self, **kwargs):
        self.selected_guest_ids = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = [
            "id",
            "gender",
            "date_of_birth",
            "passport_id",
            "visa_status",
            "arrival_date",
            "visa_application_date_maximum",
            "application_number",
        ]

        data = (
            super()
            .get_queryset()
            .only(*fields_needed)
            .filter(pk__in=self.selected_guest_ids)
        )
        return data

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()

        return super().get_context_data(object_list=self.object_list)


# Accommodations
class ManualViewSelectedAccommodationsTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    full_address = Column(verbose_name="Address")
    postcode = Column(verbose_name="Postcode")
    ltla_name = Column(verbose_name="Lower tier LA")
    utla_name = Column(verbose_name="Upper tier LA")
    remove = Column(accessor="pk", verbose_name="", orderable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if len(self.data) <= 1:
            for column in self.columns:
                column.column.orderable = False

    def render_full_address(self, record: MvAccommodation, value):
        return format_html(
            '<a class="govuk-body-s govuk-link--no-visited-state" href="{}">{}</a>',
            reverse("accommodations:detail-overview", args=[record.id]),
            value,
        )

    def render_postcode(self, value: MvUkPostcode):
        if value.postcode_formatted:
            return value.postcode_formatted
        if value.postcode:
            return value.postcode
        return ""

    def render_remove(self, value):
        return format_html(
            '<form method="post">'
            "{management_form}"
            '<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}"/>'
            '<input type="hidden" '
            'name="review-selected-records-accommodation_record_to_remove"'
            'id="id_review-selected-records-accommodation_record_to_remove" '
            'value="{value}"/>'
            '<button type="submit" name="submit" class="govuk-link">Remove</button>'
            "</form>",
            management_form=self.context["wizard"]["management_form"],
            value=value,
            csrf_token=get_token(self.request),
        )

    class Meta:
        model = MvAccommodation
        template_name = "webapp/components/tables/table.html"
        fields = ("full_address", "postcode", "ltla_name", "utla_name", "remove")


class SelectAndReviewRecordsAccommodationViewSelectionStepView(
    PermissionsMixin, SingleTableView
):
    model = MvAccommodation
    table_class = ManualViewSelectedAccommodationsTable
    template_name = "view_selected_records_list_step.html"

    def __init__(self, **kwargs):
        self.selected_accommodation_ids = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = ["full_address", "postcode", "ltla_name", "utla_name", "is_eoi"]

        data = (
            super()
            .get_queryset()
            .only(*fields_needed)
            .filter(pk__in=self.selected_accommodation_ids)
        )
        return data

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()

        return super().get_context_data(object_list=self.object_list)


# Review selected records for deduplication
# Sponsors
class ManualReviewSelectedSponsorsTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    full_name = Column(
        verbose_name="Name", order_by=("first_name", "last_name"), orderable=False
    )
    sex = Column(verbose_name="Sex", orderable=False)
    date_of_birth = CustomDateColumn(verbose_name="Date of birth", orderable=False)
    email = Column(verbose_name="Email address", orderable=False)
    phone_number = Column(verbose_name="Phone number", orderable=False)
    is_eoi = Column(verbose_name="EOI host", orderable=False)
    created_date = CustomDateTimeColumn(verbose_name="Date added", orderable=False)

    def render_full_name(self, record: MvVolunteer, value):
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{url}">{value}</a>',
            url=reverse("sponsors:detail-overview", args=[record.id]),
            value=value,
        )

    def render_is_eoi(self, value):
        return "True" if value is True else "False"

    class Meta:
        model = MvVolunteer
        template_name = "webapp/components/tables/table.html"
        fields = (
            "full_name",
            "sex",
            "date_of_birth",
            "email",
            "phone_number",
            "is_eoi",
            "created_date",
        )


class SelectAndReviewRecordsSponsorReviewSelectionStepView(
    PermissionsMixin, SingleTableView
):
    model = MvVolunteer
    table_class = ManualReviewSelectedSponsorsTable
    template_name = "review_selected_records_list_step.html"

    def __init__(self, **kwargs):
        self.selected_sponsor_ids = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = [
            "id",
            "first_name",
            "last_name",
            "sex",
            "date_of_birth",
            "email",
            "phone_number",
            "is_eoi",
            "created_date",
        ]

        data = (
            super()
            .get_queryset()
            .only(*fields_needed)
            .filter(pk__in=self.selected_sponsor_ids)
        )
        return data

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()

        return super().get_context_data(object_list=self.object_list)


# Guests
class ManualReviewSelectedGuestsTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    get_full_name = Column(
        verbose_name="Name", order_by=("first_name", "last_name"), orderable=False
    )
    gender = Column(verbose_name="Sex", orderable=False)
    date_of_birth = CustomDateColumn(verbose_name="Date of birth", orderable=False)
    passport_id = Column(verbose_name="Passport number", orderable=False)
    visa_status = Column(verbose_name="Visa status", orderable=False)
    arrival_date = CustomDateColumn(verbose_name="First arrival date", orderable=False)
    visa_application_date_maximum = CustomDateColumn(
        verbose_name="Latest visa application date", orderable=False
    )
    application_number = Column(
        verbose_name="Unique Application Number (UAN)", orderable=False
    )

    def render_get_full_name(self, record: MvPerson, value):
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{url}">{value}</a>',
            url=reverse("guests:detail-overview", args=[record.id]),
            value=value,
        )

    def render_visa_status(self, value):
        return render_to_string(
            "webapp/components/visa_status_tag/visa_status_tag.html",
            {"visa_status": value},
        )

    class Meta:
        model = MvPerson
        template_name = "webapp/components/tables/table.html"
        fields = (
            "get_full_name",
            "gender",
            "date_of_birth",
            "passport_id",
            "visa_status",
            "arrival_date",
            "visa_application_date_maximum",
            "application_number",
        )


class SelectAndReviewRecordsGuestReviewSelectionStepView(
    PermissionsMixin, SingleTableView
):
    model = MvPerson
    table_class = ManualReviewSelectedGuestsTable
    template_name = "review_selected_records_list_step.html"

    def __init__(self, **kwargs):
        self.selected_guest_ids = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = [
            "id",
            "first_name",
            "gender",
            "date_of_birth",
            "passport_id",
            "visa_status",
            "arrival_date",
            "visa_application_date_maximum",
            "application_number",
        ]
        return (
            super()
            .get_queryset()
            .only(*fields_needed)
            .filter(pk__in=self.selected_guest_ids)
        )

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()
        return super().get_context_data(object_list=self.object_list)


# Accommodations
class ManualReviewSelectedAccommodationsTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    full_address = Column(verbose_name="Address", orderable=False)
    postcode = Column(verbose_name="Postcode", orderable=False)
    ltla_name = Column(verbose_name="Lower tier LA", orderable=False)
    utla_name = Column(verbose_name="Upper tier LA", orderable=False)

    def render_postcode(self, value: MvUkPostcode):
        if value.postcode_formatted:
            return value.postcode_formatted
        if value.postcode:
            return value.postcode
        return ""

    class Meta:
        model = MvAccommodation
        template_name = "webapp/components/tables/table.html"
        fields = ("full_address", "postcode", "ltla_name", "utla_name")


class SelectAndReviewRecordsAccommodationReviewSelectionStepView(
    PermissionsMixin, SingleTableView
):
    model = MvAccommodation
    table_class = ManualReviewSelectedAccommodationsTable
    template_name = "review_selected_records_list_step.html"

    def __init__(self, **kwargs):
        self.selected_accommodation_ids = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = ["full_address", "postcode", "ltla_name", "utla_name"]

        return (
            super()
            .get_queryset()
            .only(*fields_needed)
            .filter(pk__in=self.selected_accommodation_ids)
        )

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()
        return super().get_context_data(object_list=self.object_list)


# Select accommodation request
# Guests only
class ManualSelectAccommodationRequestTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    title = Column(verbose_name="Name", orderable=False)
    checks_status = Column(verbose_name="Status", orderable=False)
    latest_application_date = CustomDateColumn(
        verbose_name="Date of application", orderable=False
    )
    number_of_people = Column(verbose_name="Number of people", orderable=False)
    ltla_name = Column(verbose_name="Lower tier LA", orderable=False)
    utla_name = Column(verbose_name="Upper tier LA", orderable=False)

    def render_title(self, record: MvAccommodationRequest, value):
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{}">{}</a>',
            reverse(
                "accommodation-requests:detail-overview",
                args=[record.id],
            ),
            value,
        )

    def render_checks_status(self, value):
        return render_to_string(
            "webapp/components/checks_status_tag/accommodation_checks_status_tag.html",
            {"accommodation_checks_status": value},
        )

    class Meta:
        model = MvAccommodationRequest
        template_name = "webapp/components/tables/table.html"
        fields = (
            "title",
            "checks_status",
            "latest_application_date",
            "number_of_people",
            "ltla_name",
            "utla_name",
        )


class SelectAndReviewRecordsGuestSelectAccommodationRequestStepView(
    PermissionsMixin, SingleTableView
):
    model = MvAccommodationRequest
    table_class = ManualSelectAccommodationRequestTable
    template_name = "select_accommodation_request_step.html"

    def __init__(self, **kwargs):
        self.selected_guest_ids = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = [
            "title",
            "checks_status",
            "latest_application_date",
            "number_of_people",
            "ltla_name",
            "utla_name",
        ]

        guests = MvPerson.objects.filter(id__in=self.selected_guest_ids).only(
            "accommodation_request"
        )
        ar_ids = [g.accommodation_request.pk for g in guests]

        return super().get_queryset().only(*fields_needed).filter(pk__in=ar_ids)

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()
        return super().get_context_data(object_list=self.object_list)


# Select correct details for deduplication
# Sponsors
class ManualSelectCorrectDetailsSponsorsTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    full_name = Column(
        verbose_name="Name", order_by=("first_name", "last_name"), orderable=False
    )
    sex = Column(verbose_name="Sex", orderable=False)
    date_of_birth = CustomDateColumn(verbose_name="Date of birth", orderable=False)
    email = Column(verbose_name="Email address", orderable=False)
    phone_number = Column(verbose_name="Phone number", orderable=False)
    residential_postcodes = Column(verbose_name="Residential postcode", orderable=False)

    class Meta:
        model = MvVolunteer
        template_name = "webapp/components/tables/table.html"
        fields = (
            "full_name",
            "sex",
            "date_of_birth",
            "email",
            "phone_number",
            "residential_postcodes",
        )


class SelectAndReviewRecordsSponsorSelectCorrectDetailsStepView(
    PermissionsMixin, SingleTableView
):
    model = MvVolunteer
    table_class = ManualSelectCorrectDetailsSponsorsTable
    template_name = "select_correct_details_step.html"

    def __init__(self, **kwargs):
        self.selected_sponsor_ids = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = [
            "id",
            "first_name",
            "last_name",
            "sex",
            "date_of_birth",
            "email",
            "phone_number",
            "residential_postcodes",
            "flag_unsuitable",
        ]

        data = (
            super()
            .get_queryset()
            .only(*fields_needed)
            .filter(pk__in=self.selected_sponsor_ids)
        )
        return data

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()

        return super().get_context_data(object_list=self.object_list)


# Guests
class ManualSelectCorrectDetailsGuestsTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    get_full_name = Column(verbose_name="Name", orderable=False)
    gender = Column(verbose_name="Sex", orderable=False)
    date_of_birth = CustomDateColumn(verbose_name="Date of birth", orderable=False)
    email = Column(verbose_name="Email address", orderable=False)
    phone = Column(verbose_name="Phone number", orderable=False)
    passport_id = Column(verbose_name="Passport number", orderable=False)
    visa_status = Column(verbose_name="Visa status", orderable=False)
    application_number = Column(
        verbose_name="Unique Application Number (UAN)", orderable=False
    )
    accommodation_request = Column(
        verbose_name="Accommodation request", orderable=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render_get_full_name(self, record: MvPerson, value):
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{url}">{value}</a>',
            url=reverse("guests:detail-overview", args=[record.id]),
            value=value,
        )

    def render_visa_status(self, value):
        return render_to_string(
            "webapp/components/visa_status_tag/visa_status_tag.html",
            {"visa_status": value},
        )

    class Meta:
        model = MvPerson
        template_name = "webapp/components/tables/table.html"
        fields = (
            "get_full_name",
            "gender",
            "date_of_birth",
            "email",
            "phone",
            "passport_id",
            "visa_status",
            "application_number",
            "accommodation_request",
        )


class SelectAndReviewRecordsGuestSelectCorrectDetailsStepView(
    PermissionsMixin, SingleTableView
):
    model = MvPerson
    table_class = ManualSelectCorrectDetailsGuestsTable
    template_name = "select_correct_details_step.html"

    def __init__(self, **kwargs):
        self.selected_guest_ids = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = [
            "id",
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "email",
            "phone",
            "passport_id",
            "visa_status",
            "application_number",
            "accommodation_request",
        ]

        data = (
            super()
            .get_queryset()
            .only(*fields_needed)
            .filter(pk__in=self.selected_guest_ids)
        )
        return data

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()

        return super().get_context_data(object_list=self.object_list)


# Accommodations
class ManualSelectCorrectDetailsAccommodationTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    full_address = Column(verbose_name="Address", orderable=False)
    postcode = Column(verbose_name="Postcode", orderable=False)
    ltla_name = Column(verbose_name="Lower tier LA", orderable=False)
    utla_name = Column(verbose_name="Upper tier LA", orderable=False)

    def render_postcode(self, value: MvUkPostcode):
        if value.postcode_formatted:
            return value.postcode_formatted
        if value.postcode:
            return value.postcode
        return ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = MvAccommodation
        template_name = "webapp/components/tables/table.html"
        fields = (
            "full_address",
            "postcode",
            "ltla_name",
            "utla_name",
        )


class SelectAndReviewRecordsAccommodationSelectCorrectDetailsStepView(
    PermissionsMixin, SingleTableView
):
    model = MvAccommodation
    table_class = ManualSelectCorrectDetailsAccommodationTable
    template_name = "select_correct_details_step.html"

    def __init__(self, **kwargs):
        self.selected_accommodation_ids = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = [
            "id",
            "full_address",
            "postcode",
            "ltla_name",
            "utla_name",
        ]
        return (
            super()
            .get_queryset()
            .select_related("postcode")
            .only(*fields_needed)
            .filter(pk__in=self.selected_accommodation_ids)
        )

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()
        return super().get_context_data(object_list=self.object_list)


# Check details and complete deduplication
# Sponsors
class SelectAndReviewRecordsSponsorCheckAndCompleteStepView(
    PermissionsMixin, MultiTableMixin, TemplateView
):
    def __init__(self, **kwargs):
        self.selected_sponsor_ids = []
        self.principal_sponsor = {}
        super().__init__(**kwargs)

    template_name = "check_and_complete_records_step.html"

    tables: List[dj_tables.Table] = []

    def get_tables(self):
        return [
            ManualSelectCorrectDetailsSponsorsTable(
                MvVolunteer.objects.filter(pk__in=self.selected_sponsor_ids)
            ),
            ManualSelectCorrectDetailsSponsorsTable([self.principal_sponsor]),
        ]


# Guests
class ManualCheckAndCompleteGuestsTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    full_name = Column(verbose_name="Name", orderable=False)
    gender = Column(verbose_name="Sex", orderable=False)
    date_of_birth = CustomDateColumn(verbose_name="Date of birth", orderable=False)
    email = Column(verbose_name="Email address", orderable=False)
    phone = Column(verbose_name="Phone number", orderable=False)
    passport_id = Column(verbose_name="Passport number", orderable=False)
    visa_status = Column(verbose_name="Visa status", orderable=False)
    application_number = Column(
        verbose_name="Unique Application Number (UAN)", orderable=False
    )
    accommodation_request = Column(
        verbose_name="Accommodation request", orderable=False
    )

    def render_visa_status(self, value):
        return render_to_string(
            "webapp/components/visa_status_tag/visa_status_tag.html",
            {"visa_status": value},
        )

    class Meta:
        model = MvPerson
        template_name = "webapp/components/tables/table.html"
        fields = (
            "full_name",
            "gender",
            "date_of_birth",
            "email",
            "phone",
            "passport_id",
            "visa_status",
            "application_number",
            "accommodation_request",
        )


class SelectAndReviewRecordsGuestCheckAndCompleteStepView(
    PermissionsMixin, MultiTableMixin, TemplateView
):
    def __init__(self, **kwargs):
        self.selected_guest_ids = []
        self.principal_guest = {}
        super().__init__(**kwargs)

    template_name = "check_and_complete_records_step.html"

    tables: List[dj_tables.Table] = []

    def get_tables(self):
        return [
            ManualSelectCorrectDetailsGuestsTable(
                MvPerson.objects.filter(pk__in=self.selected_guest_ids)
            ),
            ManualCheckAndCompleteGuestsTable([self.principal_guest]),
        ]


# Accommodations
class SelectAndReviewRecordsAccommodationCheckAndCompleteStepView(
    PermissionsMixin, MultiTableMixin, TemplateView
):
    def __init__(self, **kwargs):
        self.selected_accommodation_ids = []
        self.principal_accommodation = {}
        super().__init__(**kwargs)

    template_name = "check_and_complete_records_step.html"

    tables: List[dj_tables.Table] = []

    def get_tables(self):
        return [
            ManualSelectCorrectDetailsAccommodationTable(
                MvAccommodation.objects.filter(pk__in=self.selected_accommodation_ids)
            ),
            ManualSelectCorrectDetailsAccommodationTable(
                [self.principal_accommodation]
            ),
        ]


## UNDO DEDUPLICATION
# Sponsors
class ManualViewDeduplicatedSponsorsTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    full_name = Column(verbose_name="Name", orderable=False)
    sex = Column(verbose_name="Sex", orderable=False)
    date_of_birth = CustomDateColumn(verbose_name="Date of birth", orderable=False)
    email = Column(verbose_name="Email address", orderable=False)
    phone_number = Column(verbose_name="Phone number", orderable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render_full_name(self, record: MvVolunteer, value):
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{url}">{value}</a>'
            '<div class="govuk-hint govuk-!-font-size-16 govuk-!-margin-top-1'
            ' govuk-!-margin-bottom-0">Duplicate</div>',
            url=reverse("sponsors:detail-overview", args=[record.id]),
            value=value,
        )

    class Meta:
        model = MvVolunteer
        template_name = "webapp/components/tables/table.html"
        fields = (
            "full_name",
            "sex",
            "date_of_birth",
            "email",
            "phone_number",
        )


class UndoDeduplicationSponsorRecordsViewSelectionStepView(
    PermissionsMixin, SingleTableView
):
    model = MvVolunteer
    table_class = ManualViewDeduplicatedSponsorsTable
    template_name = "view_duplicate_records_list_step.html"

    def __init__(self, **kwargs):
        self.deduplicated_sponsors = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = [
            "id",
            "first_name",
            "last_name",
            "sex",
            "date_of_birth",
            "email",
            "phone_number",
        ]

        data = (
            super()
            .get_queryset()
            .only(*fields_needed)
            .filter(pk__in=self.deduplicated_sponsors)
        )
        return data

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()

        return super().get_context_data(object_list=self.object_list)


class UndoDeduplicationSponsorRecordsUndoDeduplicationStepView(
    PermissionsMixin, SingleTableView
):
    model = MvVolunteer
    table_class = ManualViewDeduplicatedSponsorsTable
    template_name = "undo_deduplicate_records_step.html"

    def __init__(self, **kwargs):
        self.deduplicated_sponsors = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = [
            "id",
            "first_name",
            "last_name",
            "sex",
            "date_of_birth",
            "email",
            "phone_number",
        ]

        data = (
            super()
            .get_queryset()
            .only(*fields_needed)
            .filter(pk__in=self.deduplicated_sponsors)
        )
        return data

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()

        return super().get_context_data(object_list=self.object_list)


class UndoDeduplicationSponsorRecordsRecordsRestoredStepView(
    PermissionsMixin, SingleTableView
):
    model = MvVolunteer
    template_name = "deduplicated_records_restored_step.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# Guests
class ManualViewDeduplicatedGuestsTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    get_full_name = Column(
        verbose_name="Name", order_by=("first_name", "last_name"), orderable=False
    )
    gender = Column(verbose_name="Sex", orderable=False)
    date_of_birth = CustomDateColumn(verbose_name="Date of birth", orderable=False)
    passport_id = Column(verbose_name="Passport number", orderable=False)
    visa_status = Column(verbose_name="Visa status", orderable=False)
    arrival_date = CustomDateColumn(verbose_name="First arrival date", orderable=False)
    visa_application_date_maximum = CustomDateColumn(
        verbose_name="Latest visa application date", orderable=False
    )
    application_number = Column(
        verbose_name="Unique Application Number (UAN)", orderable=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render_get_full_name(self, record: MvPerson, value):
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{url}">{value}</a>'
            '<div class="govuk-hint govuk-!-font-size-16 govuk-!-margin-top-1'
            ' govuk-!-margin-bottom-0">Duplicate</div>',
            url=reverse("guests:detail-overview", args=[record.id]),
            value=value,
        )

    def render_visa_status(self, value):
        return render_to_string(
            "webapp/components/visa_status_tag/visa_status_tag.html",
            {"visa_status": value},
        )

    class Meta:
        model = MvPerson
        template_name = "webapp/components/tables/table.html"
        fields = (
            "get_full_name",
            "gender",
            "date_of_birth",
            "passport_id",
            "visa_status",
            "arrival_date",
            "visa_application_date_maximum",
            "application_number",
        )


class UndoDeduplicationGuestRecordsViewSelectionStepView(
    PermissionsMixin, SingleTableView
):
    model = MvPerson
    table_class = ManualViewDeduplicatedGuestsTable
    template_name = "view_duplicate_records_list_step.html"

    def __init__(self, **kwargs):
        self.deduplicated_guests = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = [
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "email",
            "phone",
            "passport_id",
            "visa_status",
            "application_number",
        ]

        data = (
            super()
            .get_queryset()
            .only(*fields_needed)
            .filter(pk__in=self.deduplicated_guests)
        )
        return data

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()

        return super().get_context_data(object_list=self.object_list)


class UndoDeduplicationGuestRecordsUndoDeduplicationStepView(
    PermissionsMixin, SingleTableView
):
    model = MvPerson
    table_class = ManualViewDeduplicatedGuestsTable
    template_name = "undo_deduplicate_records_step.html"

    def __init__(self, **kwargs):
        self.deduplicated_guests = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = [
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "email",
            "phone",
            "passport_id",
            "visa_status",
            "application_number",
        ]

        data = (
            super()
            .get_queryset()
            .only(*fields_needed)
            .filter(pk__in=self.deduplicated_guests)
        )
        return data

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()

        return super().get_context_data(object_list=self.object_list)


class UndoDeduplicationGuestRecordsRecordsRestoredStepView(
    PermissionsMixin, SingleTableView
):
    model = MvPerson
    template_name = "deduplicated_records_restored_step.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# Accommodations
class ManualViewDeduplicatedAccommodationTable(dj_tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    full_address = Column(verbose_name="Address", orderable=False)
    postcode = Column(verbose_name="Postcode", orderable=False)
    ltla_name = Column(verbose_name="Lower tier LA", orderable=False)
    utla_name = Column(verbose_name="Upper tier LA", orderable=False)

    def render_full_address(self, record: MvAccommodation, value):
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{url}">{value}</a>'
            '<div class="govuk-hint govuk-!-font-size-16 govuk-!-margin-top-1'
            ' govuk-!-margin-bottom-0">Duplicate</div>',
            url=reverse("accommodations:detail-overview", args=[record.id]),
            value=value,
        )

    def render_postcode(self, value: MvUkPostcode):
        if value.postcode_formatted:
            return value.postcode_formatted
        if value.postcode:
            return value.postcode
        return ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = MvAccommodation
        template_name = "webapp/components/tables/table.html"
        fields = (
            "full_address",
            "postcode",
            "ltla_name",
            "utla_name",
        )


class UndoDeduplicationAccommodationRecordsViewSelectionStepView(
    PermissionsMixin, SingleTableView
):
    model = MvAccommodation
    table_class = ManualViewDeduplicatedAccommodationTable
    template_name = "view_duplicate_records_list_step.html"

    def __init__(self, **kwargs):
        self.deduplicated_accommodations = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = [
            "id",
            "full_address",
            "postcode",
            "ltla_name",
            "utla_name",
        ]
        return (
            super()
            .get_queryset()
            .select_related("postcode")
            .only(*fields_needed)
            .filter(pk__in=self.deduplicated_accommodations)
        )

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()

        return super().get_context_data(object_list=self.object_list)


class UndoDeduplicationAccommodationRecordsUndoDeduplicationStepView(
    PermissionsMixin, SingleTableView
):
    model = MvAccommodation
    table_class = ManualViewDeduplicatedAccommodationTable
    template_name = "undo_deduplicate_records_step.html"

    def __init__(self, **kwargs):
        self.deduplicated_accommodations = []
        super().__init__(**kwargs)

    def get_queryset(self):
        fields_needed = [
            "id",
            "full_address",
            "postcode",
            "ltla_name",
            "utla_name",
        ]
        return (
            super()
            .get_queryset()
            .select_related("postcode")
            .only(*fields_needed)
            .filter(pk__in=self.deduplicated_accommodations)
        )

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()

        return super().get_context_data(object_list=self.object_list)


class UndoDeduplicationAccommodationRecordsRecordsRestoredStepView(
    PermissionsMixin, SingleTableView
):
    model = MvAccommodation
    template_name = "deduplicated_records_restored_step.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# Form Wizards
class SelectAndViewRecordsFormWizard(
    PermissionsMixin,
    FormView,
    NamedUrlSessionWizardView,
):
    condition_dict = {
        SelectAndReviewRecordsStep.SELECT_ACCOMMODATION_REQUEST: (
            lambda self: self.include_select_ar_step()
        )
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def include_select_ar_step(self):
        is_guest = isinstance(self, SelectAndReviewGuestRecordsFormWizard)
        if not is_guest:
            return False

        is_different_ars = False
        data = (
            self.get_cleaned_data_for_step(SelectAndReviewRecordsStep.SELECT_RECORD)
            or {}
        )
        guest_records = data.get("guest_record")
        if guest_records and len(guest_records) > 1:
            if (
                guest_records[0].accommodation_request.pk
                != guest_records[1].accommodation_request.pk
            ):
                is_different_ars = True
        return is_different_ars

    def get_step_url(self, step):
        return reverse(self.url_name, kwargs={"step": step})

    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_prefix(self, request, *args, **kwargs):
        return "SelectAndReviewRecordsFormWizard"

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        return context

    def get(self, request, *args, **kwargs):
        if "reset" in request.GET:
            self.storage.reset()
        return super().get(request, *args, **kwargs)

    def get_select_records_step_view(self):
        raise NotImplementedError(
            "Implement this to provide the select record list step view"
        )

    def get_view_selected_records_step_view(self):
        raise NotImplementedError(
            "Implement this to provide the view records list step view"
        )

    def get_review_selected_records_step_view(self):
        raise NotImplementedError(
            "Implement this to provide the review records list step view"
        )

    def get_select_correct_details_step_view(self):
        raise NotImplementedError(
            "Implement this to provide the review records list step view"
        )

    def get_check_and_complete_step_view(self):
        raise NotImplementedError(
            "Implement this to provide the review records list step view"
        )

    def get_record_display_names(self, records):
        raise NotImplementedError(
            "Implement this to provide display names for the selected records"
        )

    def redirect_with_non_principal_records_error(self, non_principal_records):
        messages.error(
            self.request,
            non_principal_records_error_message(
                self.get_record_display_names(non_principal_records)
            ),
        )
        return redirect(self.get_step_url(SelectAndReviewRecordsStep.SELECT_RECORD))


class UndoDeduplicationRecordsFormWizard(
    PermissionsMixin,
    FormView,
    NamedUrlSessionWizardView,
):
    id: int

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_step_url(self, step):
        kwargs = self.get_url_kwargs()
        kwargs["step"] = step
        return reverse(self.url_name, kwargs=kwargs)

    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.id = kwargs["id"]

    def get_url_kwargs(self):
        return {
            "id": self.id,
        }

    def get_prefix(self, request, *args, **kwargs):
        return "UndoDeduplicationRecordsFormWizard"

    def get_cancel_url(self):
        raise NotImplementedError("Subclasses must implement get_cancel_url")

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        kwargs["record_id"] = self.kwargs["id"]
        kwargs["cancel_url"] = self.get_cancel_url()
        return kwargs

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def get_view_deduplicated_records_step_view(self):
        raise NotImplementedError(
            "Implement this to provide the select record list step view"
        )

    def get_undo_deduplicated_records_step_view(self):
        raise NotImplementedError(
            "Implement this to provide the select record list step view"
        )

    def get_unlocked_deduplicated_records_step_view(self):
        raise NotImplementedError(
            "Implement this to provide the select record list step view"
        )


# Sponsors
class SelectAndReviewSponsorRecordsFormWizard(SelectAndViewRecordsFormWizard):
    model = MvVolunteer

    def get_group_type(self):
        if settings.FIX_DUPLICATE_RECORDS_ENABLED:
            return list(FIX_DUPLICATE_RECORDS_ALLOWED_GROUP_TYPES)
        return [GroupType.DEV]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.deduplicate_sponsors_step_view = (
            SelectAndReviewRecordsSponsorListStepView()
        )
        self.view_selected_sponsors_step_view = (
            SelectAndReviewRecordsSponsorViewSelectionStepView()
        )
        self.review_selected_sponsors_step_view = (
            SelectAndReviewRecordsSponsorReviewSelectionStepView()
        )

        self.select_correct_details_step_view = (
            SelectAndReviewRecordsSponsorSelectCorrectDetailsStepView()
        )

        self.check_and_complete_step_view = (
            SelectAndReviewRecordsSponsorCheckAndCompleteStepView()
        )

    def get_select_records_step_view(self):
        return self.deduplicate_sponsors_step_view

    def get_view_selected_records_step_view(self):
        return self.view_selected_sponsors_step_view

    def get_review_selected_records_step_view(self):
        return self.review_selected_sponsors_step_view

    def get_select_correct_details_step_view(self):
        return self.select_correct_details_step_view

    def get_check_and_complete_step_view(self):
        return self.check_and_complete_step_view

    def get_template_names(self):
        return SELECT_AND_REVIEW_FORM_TEMPLATES[self.steps.current]

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step and step == SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS:
            step_data = self.storage.get_step_data(
                SelectAndReviewRecordsStep.SELECT_RECORD
            )
            kwargs["queryset"] = MvVolunteer.objects.filter(
                pk__in=step_data.getlist("select-record-sponsor_record")
            )
        return kwargs

    def get_context_data(self, form=None, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        context["cancel_url"] = self.get_cancel_url()
        context["table_template_url"] = "sponsors/sponsors_list.html"

        context["type"] = "sponsor and host"

        if data := self.get_cleaned_data_for_step(
            SelectAndReviewRecordsStep.SELECT_RECORD
        ):
            selected_sponsors = list(data.get("sponsor_record", []))
        else:
            selected_sponsors = []

        if self.steps.current == SelectAndReviewRecordsStep.SELECT_RECORD:
            selected_sponsor_ids = [sponsor.pk for sponsor in selected_sponsors]
            self.get_select_records_step_view().selected_sponsor_ids = (
                selected_sponsor_ids
            )
            self.get_select_records_step_view().request = self.request
            context |= self.get_select_records_step_view().get_context_data()
            context["selected_ids"] = selected_sponsor_ids

        if self.steps.current == SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS:
            self.get_view_selected_records_step_view().selected_sponsor_ids = [
                sponsor.pk for sponsor in selected_sponsors
            ]
            self.get_view_selected_records_step_view().request = self.request
            context |= self.get_view_selected_records_step_view().get_context_data()

        if self.steps.current == SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS:
            self.get_review_selected_records_step_view().selected_sponsor_ids = [
                sponsor.pk for sponsor in selected_sponsors
            ]
            self.get_review_selected_records_step_view().request = self.request
            context |= self.get_review_selected_records_step_view().get_context_data()

        if self.steps.current == SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS:
            self.get_select_correct_details_step_view().selected_sponsor_ids = [
                sponsor.pk for sponsor in selected_sponsors
            ]
            self.get_select_correct_details_step_view().request = self.request
            context |= self.get_select_correct_details_step_view().get_context_data()

        if self.steps.current == SelectAndReviewRecordsStep.CHECK_AND_COMPLETE:
            self.get_check_and_complete_step_view().selected_sponsor_ids = [
                sponsor.pk for sponsor in selected_sponsors
            ]
            ps = self.get_cleaned_data_for_step(
                SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS
            )
            if ps["date_of_birth"]:
                date_of_birth_str = ps["date_of_birth"].split(" (")[0]
                date_of_birth = datetime.strptime(
                    date_of_birth_str, "%d %B %Y"
                ).strftime("%-d %b %Y")
            else:
                date_of_birth = ps["date_of_birth"]
            self.get_check_and_complete_step_view().principal_sponsor = {
                "full_name": f"{ps['first_name']} {ps['last_name']}",
                "sex": ps["sex"],
                "date_of_birth": date_of_birth,
                "email": ps["email_address"],
                "phone_number": ps["phone_numbers"],
                "residential_postcodes": ps["residential_postcodes"],
                "flag_unsuitable": False,
            }
            self.get_check_and_complete_step_view().request = self.request
            context |= self.get_check_and_complete_step_view().get_context_data()

        return context

    def get_form_step_data(self, form):
        if (
            isinstance(form, ViewSelectedRecordsStepForm)
            and "review-selected-records-sponsor_record_to_remove" in form.data
        ):
            self.storage.data["step_data"][SelectAndReviewRecordsStep.SELECT_RECORD][
                "select-record-sponsor_record"
            ].remove(form.data["review-selected-records-sponsor_record_to_remove"])
            self.render_goto_step(SelectAndReviewRecordsStep.SELECT_RECORD)
        return super().get_form_step_data(form)

    def get_cancel_url(self):
        return (
            reverse("deduplication:sponsors:select-and-review-records-manual")
            + "?reset=true"
        )

    def get_record_display_names(self, records):
        return [sponsor.full_name for sponsor in records]

    def done(self, form_list, **kwargs):
        try:
            selected_sponsors = list(
                self.get_cleaned_data_for_step(
                    SelectAndReviewRecordsStep.SELECT_RECORD
                )["sponsor_record"]
            )
            non_principal_sponsors = get_non_principal_records(selected_sponsors)
            if non_principal_sponsors:
                return self.redirect_with_non_principal_records_error(
                    non_principal_sponsors
                )

            ps = self.get_cleaned_data_for_step(
                SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS
            )
            date_of_birth_str = ps["date_of_birth"].split(" (")[0]
            date_of_birth = datetime.strptime(date_of_birth_str, "%d %B %Y").date()
            principal_sponsor_details = {
                "first_name": f"{ps['first_name']}",
                "last_name": f"{ps['last_name']}",
                "sex": ps["sex"],
                "date_of_birth": date_of_birth,
                "email": ps["email_address"],
                "phone_number": ps["phone_numbers"],
                "residential_postcodes": ps["residential_postcodes"],
                "flag_unsuitable": False,
            }

            dedup_sponsor_group = SponsorDuplicateGroup.objects.create()
            dedup_sponsor_group.sponsors.set(selected_sponsors)
            dedup_sponsor_group.deduplicate(
                principal_sponsor_details, user=self.request.user
            )

            messages.success(
                self.request,
                f"{
                    format_html(
                        '<a class="govuk-body govuk-link" href="{url}">{value}</a>',
                        url=reverse(
                            'sponsors:detail-overview',
                            args=[dedup_sponsor_group.principal_record.id],
                        ),
                        value=dedup_sponsor_group.principal_record.full_name,
                    )
                }",
            )
        except Exception as e:
            logger.exception("Sponsor Deduplication Error: %s", e)
            sentry_sdk.capture_exception(e)
            messages.error(
                self.request,
                "The selected records have not been marked as duplicates. "
                "No new principal record was created.",
            )

        return redirect(
            "deduplication:sponsors:select-and-review-records-manual-step",
            "select-record",
        )


class UndoDeduplicationSponsorRecordsFormWizard(UndoDeduplicationRecordsFormWizard):
    model = MvVolunteer
    group_type = [GroupType.DEV]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.view_deduplicated_sponsors_step_view = (
            UndoDeduplicationSponsorRecordsViewSelectionStepView()
        )
        self.undo_deduplication_sponsors_step_view = (
            UndoDeduplicationSponsorRecordsUndoDeduplicationStepView()
        )
        self.deduplicated_records_restored_step_view = (
            UndoDeduplicationSponsorRecordsRecordsRestoredStepView()
        )

    def get_view_duplicate_records_step_view(self):
        return self.view_deduplicated_sponsors_step_view

    def get_undo_deduplicate_records_step_view(self):
        return self.undo_deduplication_sponsors_step_view

    def get_deduplicated_records_restored_step_view(self):
        return self.deduplicated_records_restored_step_view

    def get_template_names(self):
        return UNDO_DEDUPLICATION_FORM_TEMPLATES[self.steps.current]

    def post(self, *args, **kwargs):
        if self.steps.current == UndoDeduplicationRecordsStep.UNDO_DEDUPLICATE_RECORDS:
            return self.done(self.get_all_cleaned_data())

        return super().post(*args, **kwargs)

    def get_context_data(self, form=None, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        context["cancel_url"] = self.get_cancel_url()
        context["view_duplicate_records_url"] = reverse(
            "deduplication:sponsors:undo-deduplication-records-manual-step",
            kwargs={
                "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                "id": self.kwargs["id"],
            },
        )
        context["type_list_url"] = reverse("sponsors:sponsors")
        context["type_record_url"] = reverse(
            "sponsors:detail-overview", kwargs={"pk": self.kwargs["id"]}
        )
        context["table_template_url"] = "sponsors/sponsors_list.html"

        context["type_title_plural"] = "Sponsors and hosts"
        context["type_title"] = "Sponsor and host"
        context["type"] = "sponsor and host"

        if self.steps.current == UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS:
            sponsor_id = self.kwargs["id"]
            dedup_group = (
                SponsorDuplicateGroup.objects.filter(principal_record_id=sponsor_id)
                .only("sponsors", "principal_record")
                .prefetch_related("sponsors")
                .first()
            )
            deduplicated_sponsors = (
                dedup_group.sponsors.all()
                .only("full_name")
                .order_by("first_name", "last_name")
            )
            if len(deduplicated_sponsors) == 2:
                deduplicated_sponsors_formatted = (
                    f"{deduplicated_sponsors[0].full_name} "
                    f"and {deduplicated_sponsors[1].full_name}"
                )
            else:
                deduplicated_sponsors_formatted = f"{
                    ', '.join(deduplicated_sponsors[:-1].full_name)
                    and deduplicated_sponsors[-1].full_name
                }"

            self.get_view_duplicate_records_step_view().deduplicated_sponsors = (
                deduplicated_sponsors
            )
            self.get_view_duplicate_records_step_view().request = self.request
            context |= self.get_view_duplicate_records_step_view().get_context_data()

            self.storage.extra_data["deduplication_data"] = {
                "principal_name": dedup_group.principal_record.full_name,
                "deduplicated_sponsor_data": [
                    {
                        "url": reverse("sponsors:detail-overview", args=[sponsor.pk]),
                        "name": sponsor.full_name,
                    }
                    for sponsor in deduplicated_sponsors
                ],
                "formatted_deduplicated_sponsors": deduplicated_sponsors_formatted,
            }

            context["deduplicated_records"] = deduplicated_sponsors
            context["principal_record_name"] = dedup_group.principal_record.full_name

        if self.steps.current == UndoDeduplicationRecordsStep.UNDO_DEDUPLICATE_RECORDS:
            sponsor_id = self.kwargs["id"]
            dedup_group = (
                SponsorDuplicateGroup.objects.filter(principal_record_id=sponsor_id)
                .only("sponsors", "principal_record", "created_at")
                .prefetch_related("sponsors")
                .first()
            )
            deduplicated_sponsors = (
                dedup_group.sponsors.all()
                .only("full_name")
                .order_by("first_name", "last_name")
            )
            self.get_undo_deduplicate_records_step_view().deduplicated_sponsors = (
                deduplicated_sponsors
            )
            self.get_undo_deduplicate_records_step_view().request = self.request
            context |= self.get_undo_deduplicate_records_step_view().get_context_data()
            if len(deduplicated_sponsors) == 2:
                deduplicated_sponsors_formatted = (
                    f"{deduplicated_sponsors[0].full_name} and "
                    f"{deduplicated_sponsors[1].full_name}"
                )
            else:
                deduplicated_sponsors_formatted = f"{
                    ', '.join(deduplicated_sponsors[:-1].full_name)
                    and deduplicated_sponsors[-1].full_name
                }"
            context["deduplicated_records"] = deduplicated_sponsors_formatted
            context["principal_record_name"] = dedup_group.principal_record.full_name
            context["date"] = dedup_group.created_at

        if (
            self.steps.current
            == UndoDeduplicationRecordsStep.DEDUPLICATED_RECORDS_RESTORED
        ):
            deduplication_data = self.storage.extra_data.get("deduplication_data")

            self.get_undo_deduplicate_records_step_view().request = self.request
            context |= self.get_undo_deduplicate_records_step_view().get_context_data()

            context["principal_record_name"] = deduplication_data["principal_name"]
            context["deduplicated_record_data"] = deduplication_data[
                "deduplicated_sponsor_data"
            ]
            context["deduplicated_records_names_list_formatted"] = deduplication_data[
                "formatted_deduplicated_sponsors"
            ]

        return context

    def get_cancel_url(self):
        return (
            reverse("sponsors:detail-actions", kwargs={"pk": self.kwargs["id"]})
            + "?reset=true"
        )

    def done(self, form_list, **kwargs):
        sponsor_id = self.kwargs["id"]
        dedup_group = SponsorDuplicateGroup.objects.prefetch_related("sponsors").get(
            principal_record_id=sponsor_id
        )
        try:
            dedup_group.undo_deduplication(user=self.request.user)
        except Exception:
            messages.error(
                self.request,
                "The principal record has not been deleted and the original "
                "records were not restored.",
            )
            return redirect("sponsors:detail-actions", sponsor_id)

        return redirect(
            "deduplication:sponsors:complete-undo-deduplication-records-manual-step",
            UndoDeduplicationRecordsStep.DEDUPLICATED_RECORDS_RESTORED,
        )


# Guests
class SelectAndReviewGuestRecordsFormWizard(SelectAndViewRecordsFormWizard):
    model = MvPerson
    group_type = [GroupType.DEV]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.deduplicate_guests_step_view = SelectAndReviewRecordsGuestListStepView()
        self.view_selected_guests_step_view = (
            SelectAndReviewRecordsGuestViewSelectionStepView()
        )
        self.review_selected_guests_step_view = (
            SelectAndReviewRecordsGuestReviewSelectionStepView()
        )
        self.select_accommodation_request_step_view = (
            SelectAndReviewRecordsGuestSelectAccommodationRequestStepView()
        )
        self.select_correct_details_step_view = (
            SelectAndReviewRecordsGuestSelectCorrectDetailsStepView()
        )
        self.check_and_complete_step_view = (
            SelectAndReviewRecordsGuestCheckAndCompleteStepView()
        )

    def get_select_records_step_view(self):
        return self.deduplicate_guests_step_view

    def get_view_selected_records_step_view(self):
        return self.view_selected_guests_step_view

    def get_review_selected_records_step_view(self):
        return self.review_selected_guests_step_view

    def get_select_accommodation_request_view(self):
        return self.select_accommodation_request_step_view

    def get_select_correct_details_step_view(self):
        return self.select_correct_details_step_view

    def get_check_and_complete_step_view(self):
        return self.check_and_complete_step_view

    def get_template_names(self):
        return SELECT_AND_REVIEW_FORM_TEMPLATES[self.steps.current]

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if (
            step
            and step == SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS
            or step == SelectAndReviewRecordsStep.SELECT_ACCOMMODATION_REQUEST
        ):
            step_data = self.storage.get_step_data(
                SelectAndReviewRecordsStep.SELECT_RECORD
            )
            kwargs["queryset"] = MvPerson.objects.filter(
                pk__in=step_data.getlist("select-record-guest_record")
            )
        if step and step == SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS:
            if (
                SelectAndReviewRecordsStep.SELECT_ACCOMMODATION_REQUEST
                in self.get_form_list()
            ):
                kwargs["select_ar_data"] = self.get_cleaned_data_for_step(
                    SelectAndReviewRecordsStep.SELECT_ACCOMMODATION_REQUEST
                )
            else:
                kwargs["select_ar_data"] = {
                    "accommodation_request": self.get_cleaned_data_for_step(
                        SelectAndReviewRecordsStep.SELECT_RECORD
                    )["guest_record"][0].accommodation_request.pk
                }
        return kwargs

    def get_context_data(self, form=None, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        context["cancel_url"] = self.get_cancel_url()
        context["table_template_url"] = "guests/guests_list.html"

        context["type"] = "guest"

        if data := self.get_cleaned_data_for_step(
            SelectAndReviewRecordsStep.SELECT_RECORD
        ):
            selected_guests = list(data.get("guest_record", []))
        else:
            selected_guests = []

        if self.steps.current == SelectAndReviewRecordsStep.SELECT_RECORD:
            selected_guest_ids = [guest.pk for guest in selected_guests]
            self.get_select_records_step_view().selected_guest_ids = selected_guest_ids
            self.get_select_records_step_view().request = self.request
            context |= self.get_select_records_step_view().get_context_data()
            context["selected_ids"] = selected_guest_ids

        if self.steps.current == SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS:
            self.get_view_selected_records_step_view().selected_guest_ids = [
                guest.pk for guest in selected_guests
            ]
            self.get_view_selected_records_step_view().request = self.request
            context |= self.get_view_selected_records_step_view().get_context_data()

        if self.steps.current == SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS:
            self.get_review_selected_records_step_view().selected_guest_ids = [
                guest.pk for guest in selected_guests
            ]
            self.get_review_selected_records_step_view().request = self.request
            context |= self.get_review_selected_records_step_view().get_context_data()

        if (
            self.steps.current
            == SelectAndReviewRecordsStep.SELECT_ACCOMMODATION_REQUEST
        ):
            self.get_select_accommodation_request_view().selected_guest_ids = [
                guest.pk for guest in selected_guests
            ]
            self.get_select_accommodation_request_view().request = self.request
            context["table_template_url"] = (
                "accommodation_requests/accommodation_requests_list.html"
            )
            context |= self.get_select_accommodation_request_view().get_context_data()

        if self.steps.current == SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS:
            self.get_select_correct_details_step_view().selected_guest_ids = [
                guest.pk for guest in selected_guests
            ]
            self.get_select_correct_details_step_view().request = self.request
            context |= self.get_select_correct_details_step_view().get_context_data()

        if self.steps.current == SelectAndReviewRecordsStep.CHECK_AND_COMPLETE:
            self.get_check_and_complete_step_view().selected_guest_ids = [
                guest.pk for guest in selected_guests
            ]
            ps = self.get_cleaned_data_for_step(
                SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS
            )
            if ps["date_of_birth"]:
                date_of_birth_str = ps["date_of_birth"].split(" (")[0]
                date_of_birth = datetime.strptime(
                    date_of_birth_str, "%d %B %Y"
                ).strftime("%-d %b %Y")
            else:
                date_of_birth = ps["date_of_birth"]
            self.get_check_and_complete_step_view().principal_guest = {
                "full_name": f"{ps['first_name']} {ps['last_name']}",
                "gender": ps["sex"],
                "date_of_birth": date_of_birth,
                "email": ps["email_address"],
                "phone": ps["phone_numbers"],
                "passport_id": ps["passport_number"],
                "visa_status": ps["visa_status"],
                "application_number": ps["application_numbers"],
            }
            if (
                SelectAndReviewRecordsStep.SELECT_ACCOMMODATION_REQUEST
                in self.get_form_list()
            ):
                ar_id = self.get_cleaned_data_for_step(
                    SelectAndReviewRecordsStep.SELECT_ACCOMMODATION_REQUEST
                )["accommodation_request"]
                ar = MvAccommodationRequest.objects.get(pk=ar_id)

                self.get_check_and_complete_step_view().principal_guest[
                    "accommodation_request"
                ] = ar
            self.get_check_and_complete_step_view().request = self.request
            context |= self.get_check_and_complete_step_view().get_context_data()

        return context

    def get_form_step_data(self, form):
        if (
            isinstance(form, ViewSelectedRecordsStepForm)
            and "review-selected-records-guest_record_to_remove" in form.data
        ):
            self.storage.data["step_data"][SelectAndReviewRecordsStep.SELECT_RECORD][
                "select-record-guest_record"
            ].remove(form.data["review-selected-records-guest_record_to_remove"])
            self.render_goto_step(SelectAndReviewRecordsStep.SELECT_RECORD)
        return super().get_form_step_data(form)

    def get_cancel_url(self):
        return (
            reverse("deduplication:guests:select-and-review-records-manual")
            + "?reset=true"
        )

    def get_record_display_names(self, records):
        return [guest.get_full_name() for guest in records]

    def done(self, form_list, **kwargs):
        try:
            selected_guests = list(
                self.get_cleaned_data_for_step(
                    SelectAndReviewRecordsStep.SELECT_RECORD
                )["guest_record"]
            )
            non_principal_guests = get_non_principal_records(selected_guests)
            if non_principal_guests:
                return self.redirect_with_non_principal_records_error(
                    non_principal_guests
                )

            ps = self.get_cleaned_data_for_step(
                SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS
            )
            date_of_birth_str = ps["date_of_birth"].split(" (")[0]
            date_of_birth = datetime.strptime(date_of_birth_str, "%d %B %Y").date()
            principal_guest_details = {
                "first_name": ps["first_name"],
                "last_name": ps["last_name"],
                "gender": ps["sex"],
                "date_of_birth": date_of_birth,
                "email": ps["email_address"],
                "phone": ps["phone_numbers"],
                "passport_id": ps["passport_number"],
                "visa_status": ps["visa_status"],
                "application_number": ps["application_numbers"],
            }

            if (
                SelectAndReviewRecordsStep.SELECT_ACCOMMODATION_REQUEST
                in self.get_form_list()
            ):
                ar_id = self.get_cleaned_data_for_step(
                    SelectAndReviewRecordsStep.SELECT_ACCOMMODATION_REQUEST
                )["accommodation_request"]
                ar = MvAccommodationRequest.objects.get(pk=ar_id)

                principal_guest_details["accommodation_request"] = ar

            dedup_guest_group = GuestDuplicateGroup.objects.create()
            dedup_guest_group.guests.set(selected_guests)

            dedup_guest_group.deduplicate(
                principal_guest_details, user=self.request.user
            )

            messages.success(
                self.request,
                f"{
                    format_html(
                        '<a class="govuk-body govuk-link" href="{url}">{value}</a>',
                        url=reverse(
                            'guests:detail-overview',
                            args=[dedup_guest_group.principal_record.id],
                        ),
                        value=dedup_guest_group.principal_record.get_full_name(),
                    )
                }",
            )
        except Exception as e:
            logger.exception("Guest Deduplication Error: %s", e)
            sentry_sdk.capture_exception(e)
            messages.error(
                self.request,
                "The selected records have not been marked as duplicates. "
                "No new principal record was created.",
            )

        return redirect(
            "deduplication:guests:select-and-review-records-manual-step",
            "select-record",
        )


class UndoDeduplicationGuestRecordsFormWizard(UndoDeduplicationRecordsFormWizard):
    model = MvPerson
    group_type = [GroupType.DEV]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.view_deduplicated_guests_step_view = (
            UndoDeduplicationGuestRecordsViewSelectionStepView()
        )
        self.undo_deduplicated_guests_step_view = (
            UndoDeduplicationGuestRecordsUndoDeduplicationStepView()
        )
        self.deduplicated_records_restored_step_view = (
            UndoDeduplicationGuestRecordsRecordsRestoredStepView()
        )

    def dispatch(self, request, *args, **kwargs):
        guest_id = kwargs.get("id")
        dedup_group = GuestDuplicateGroup.objects.filter(
            principal_record_id=guest_id
        ).first()
        if dedup_group and not dedup_group.can_undo_deduplication(guest_id):
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_view_duplicate_records_step_view(self):
        return self.view_deduplicated_guests_step_view

    def get_undo_deduplicate_records_step_view(self):
        return self.undo_deduplicated_guests_step_view

    def get_deduplicated_records_restored_step_view(self):
        return self.deduplicated_records_restored_step_view

    def get_template_names(self):
        return UNDO_DEDUPLICATION_FORM_TEMPLATES[self.steps.current]

    def post(self, *args, **kwargs):
        if self.steps.current == UndoDeduplicationRecordsStep.UNDO_DEDUPLICATE_RECORDS:
            return self.done(self.get_all_cleaned_data())

        return super().post(*args, **kwargs)

    def get_context_data(self, form=None, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        context["cancel_url"] = self.get_cancel_url()
        context["view_duplicate_records_url"] = reverse(
            "deduplication:guests:undo-deduplication-records-manual-step",
            kwargs={
                "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                "id": self.kwargs["id"],
            },
        )
        context["type_list_url"] = reverse("guests:guests")
        context["type_record_url"] = reverse(
            "guests:detail-overview", kwargs={"pk": self.kwargs["id"]}
        )
        context["table_template_url"] = "guests/guests_list.html"

        context["type_title_plural"] = "Guests"
        context["type_title"] = "Guest"
        context["type"] = "guest"

        if self.steps.current == UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS:
            guest_id = self.kwargs["id"]
            dedup_group = (
                GuestDuplicateGroup.objects.filter(principal_record_id=guest_id)
                .only("principal_record", "guests")
                .prefetch_related("guests")
                .first()
            )
            deduplicated_guests = (
                dedup_group.guests.all()
                .only("pk", "first_name", "last_name")
                .order_by("first_name", "last_name")
            )
            deduplicated_guests_formatted = GuestDuplicateGroup.format_guest_names(
                dedup_group, deduplicated_guests
            )

            self.get_view_duplicate_records_step_view().deduplicated_guests = (
                deduplicated_guests
            )
            self.get_view_duplicate_records_step_view().request = self.request
            context |= self.get_view_duplicate_records_step_view().get_context_data()

            self.storage.extra_data["deduplication_data"] = {
                "principal_name": dedup_group.principal_record.get_full_name(),
                "deduplicated_guest_data": [
                    {
                        "url": reverse("guests:detail-overview", args=[guest.pk]),
                        "name": guest.full_name,
                    }
                    for guest in deduplicated_guests
                ],
                "formatted_deduplicated_guests": deduplicated_guests_formatted,
            }

            context["deduplicated_records"] = deduplicated_guests
            context["principal_record_name"] = (
                dedup_group.principal_record.get_full_name()
            )

        if self.steps.current == UndoDeduplicationRecordsStep.UNDO_DEDUPLICATE_RECORDS:
            guest_id = self.kwargs["id"]
            dedup_group = (
                GuestDuplicateGroup.objects.filter(principal_record_id=guest_id)
                .only("created_at", "principal_record", "guests")
                .prefetch_related("guests")
                .first()
            )
            deduplicated_guests = (
                dedup_group.guests.all()
                .only("first_name", "last_name")
                .order_by("first_name", "last_name")
            )
            self.get_undo_deduplicate_records_step_view().deduplicated_guests = (
                deduplicated_guests
            )
            self.get_undo_deduplicate_records_step_view().request = self.request
            context |= self.get_undo_deduplicate_records_step_view().get_context_data()
            deduplicated_guests_formatted = GuestDuplicateGroup.format_guest_names(
                dedup_group, deduplicated_guests
            )
            context["deduplicated_records"] = deduplicated_guests_formatted
            context["principal_record_name"] = (
                dedup_group.principal_record.get_full_name()
            )
            context["date"] = dedup_group.created_at

        if (
            self.steps.current
            == UndoDeduplicationRecordsStep.DEDUPLICATED_RECORDS_RESTORED
        ):
            deduplication_data = self.storage.extra_data.get("deduplication_data")

            self.get_undo_deduplicate_records_step_view().request = self.request
            context |= self.get_undo_deduplicate_records_step_view().get_context_data()

            context["principal_record_name"] = deduplication_data["principal_name"]
            context["deduplicated_record_data"] = deduplication_data[
                "deduplicated_guest_data"
            ]
            context["deduplicated_records_names_list_formatted"] = deduplication_data[
                "formatted_deduplicated_guests"
            ]

        return context

    def get_cancel_url(self):
        return (
            reverse("guests:detail-actions", kwargs={"pk": self.kwargs["id"]})
            + "?reset=true"
        )

    def done(self, form_list, **kwargs):
        guest_id = self.kwargs["id"]
        dedup_group = GuestDuplicateGroup.objects.prefetch_related("guests").get(
            principal_record_id=guest_id
        )
        if not dedup_group.can_undo_deduplication(guest_id):
            return redirect("guests:detail-actions", guest_id)
        try:
            dedup_group.undo_deduplication(user=self.request.user)
        except Exception:
            messages.error(
                self.request,
                "The principal record has not been deleted and the original "
                "records were not restored.",
            )
            return redirect("guests:detail-actions", guest_id)

        return redirect(
            "deduplication:guests:complete-undo-deduplication-records-manual-step",
            UndoDeduplicationRecordsStep.DEDUPLICATED_RECORDS_RESTORED,
        )


# Accommodations
class SelectAndReviewAccommodationRecordsFormWizard(SelectAndViewRecordsFormWizard):
    model = MvAccommodation

    def get_group_type(self):
        if settings.FIX_DUPLICATE_RECORDS_ENABLED:
            return list(FIX_DUPLICATE_RECORDS_ALLOWED_GROUP_TYPES)
        return [GroupType.DEV]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.deduplicate_accommodations_step_view = (
            SelectAndReviewRecordsAccommodationListStepView()
        )
        self.view_selected_accommodations_step_view = (
            SelectAndReviewRecordsAccommodationViewSelectionStepView()
        )
        self.review_selected_accommodations_step_view = (
            SelectAndReviewRecordsAccommodationReviewSelectionStepView()
        )

        self.select_correct_details_step_view = (
            SelectAndReviewRecordsAccommodationSelectCorrectDetailsStepView()
        )

        self.check_and_complete_step_view = (
            SelectAndReviewRecordsAccommodationCheckAndCompleteStepView()
        )

    def get_select_records_step_view(self):
        return self.deduplicate_accommodations_step_view

    def get_view_selected_records_step_view(self):
        return self.view_selected_accommodations_step_view

    def get_review_selected_records_step_view(self):
        return self.review_selected_accommodations_step_view

    def get_select_correct_details_step_view(self):
        return self.select_correct_details_step_view

    def get_check_and_complete_step_view(self):
        return self.check_and_complete_step_view

    def get_template_names(self):
        return SELECT_AND_REVIEW_FORM_TEMPLATES[self.steps.current]

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step and step == SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS:
            step_data = self.storage.get_step_data(
                SelectAndReviewRecordsStep.SELECT_RECORD
            )
            kwargs["queryset"] = MvAccommodation.objects.filter(
                pk__in=step_data.getlist("select-record-accommodation_record")
            )
        return kwargs

    def get_context_data(self, form=None, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        context["cancel_url"] = self.get_cancel_url()
        context["table_template_url"] = "accommodations/accommodations_list.html"

        context["type"] = "accommodation"

        if data := self.get_cleaned_data_for_step(
            SelectAndReviewRecordsStep.SELECT_RECORD
        ):
            selected_accommodations = list(data.get("accommodation_record", []))
        else:
            selected_accommodations = []

        if self.steps.current == SelectAndReviewRecordsStep.SELECT_RECORD:
            selected_accommodation_ids = [ac.pk for ac in selected_accommodations]
            self.get_select_records_step_view().selected_accommodation_ids = (
                selected_accommodation_ids
            )
            self.get_select_records_step_view().request = self.request
            context |= self.get_select_records_step_view().get_context_data()
            context["selected_ids"] = selected_accommodation_ids

        if self.steps.current == SelectAndReviewRecordsStep.VIEW_SELECTED_RECORDS:
            self.get_view_selected_records_step_view().selected_accommodation_ids = [
                ac.pk for ac in selected_accommodations
            ]
            self.get_view_selected_records_step_view().request = self.request
            context |= self.get_view_selected_records_step_view().get_context_data()

        if self.steps.current == SelectAndReviewRecordsStep.REVIEW_SELECTED_RECORDS:
            self.get_review_selected_records_step_view().selected_accommodation_ids = [
                ac.pk for ac in selected_accommodations
            ]
            self.get_review_selected_records_step_view().request = self.request
            context |= self.get_review_selected_records_step_view().get_context_data()

        if self.steps.current == SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS:
            self.get_select_correct_details_step_view().selected_accommodation_ids = [
                ac.pk for ac in selected_accommodations
            ]
            self.get_select_correct_details_step_view().request = self.request
            context |= self.get_select_correct_details_step_view().get_context_data()

        if self.steps.current == SelectAndReviewRecordsStep.CHECK_AND_COMPLETE:
            self.get_check_and_complete_step_view().selected_accommodation_ids = [
                ac.pk for ac in selected_accommodations
            ]
            ps = self.get_cleaned_data_for_step(
                SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS
            )

            self.get_check_and_complete_step_view().principal_accommodation = {
                "full_address": MvAccommodation.objects.only("full_address", "postcode")
                .get(id=ps["full_address"])
                .full_address,
                "postcode": MvUkPostcode.objects.get(id=ps["postcode"]),
                "ltla_name": ps["ltla_name"],
                "utla_name": ps["utla_name"],
            }
            self.get_check_and_complete_step_view().request = self.request
            context |= self.get_check_and_complete_step_view().get_context_data()

        return context

    def get_form_step_data(self, form):
        if (
            isinstance(form, ViewSelectedRecordsStepForm)
            and "review-selected-records-accommodation_record_to_remove" in form.data
        ):
            self.storage.data["step_data"][SelectAndReviewRecordsStep.SELECT_RECORD][
                "select-record-accommodation_record"
            ].remove(
                form.data["review-selected-records-accommodation_record_to_remove"]
            )
            self.render_goto_step(SelectAndReviewRecordsStep.SELECT_RECORD)
        return super().get_form_step_data(form)

    def get_cancel_url(self):
        return (
            reverse("deduplication:accommodations:select-and-review-records-manual")
            + "?reset=true"
        )

    def get_record_display_names(self, records):
        return [accommodation.full_address for accommodation in records]

    def done(self, form_list, **kwargs):
        try:
            selected_accommodations = list(
                self.get_cleaned_data_for_step(
                    SelectAndReviewRecordsStep.SELECT_RECORD
                )["accommodation_record"]
            )
            non_principal_accommodations = get_non_principal_records(
                selected_accommodations
            )
            if non_principal_accommodations:
                return self.redirect_with_non_principal_records_error(
                    non_principal_accommodations
                )

            ps = self.get_cleaned_data_for_step(
                SelectAndReviewRecordsStep.SELECT_CORRECT_DETAILS
            )
            principal_accommodation_details = {
                "full_address": MvAccommodation.objects.only("full_address", "postcode")
                .get(id=ps["full_address"])
                .full_address,
                "postcode": MvUkPostcode.objects.get(id=ps["postcode"]),
                "ltla_name": ps["ltla_name"],
                "utla_name": ps["utla_name"],
            }

            dedup_accommodation_group = AccommodationDuplicateGroup.objects.create()
            dedup_accommodation_group.accommodations.set(selected_accommodations)
            dedup_accommodation_group.deduplicate(
                principal_accommodation_details, user=self.request.user
            )

            messages.success(
                self.request,
                f"{
                    format_html(
                        '<a class="govuk-body govuk-link" href="{url}">{value}</a>',
                        url=reverse(
                            'accommodations:detail-overview',
                            args=[dedup_accommodation_group.principal_record.id],
                        ),
                        value=dedup_accommodation_group.principal_record.full_address,
                    )
                }",
            )
        except Exception as e:
            logger.exception("Accommodation Deduplication Error: %s", e)
            sentry_sdk.capture_exception(e)
            messages.error(
                self.request,
                "The selected records have not been marked as duplicates. "
                "No new principal record was created.",
            )

        return redirect(
            "deduplication:accommodations:select-and-review-records-manual-step",
            "select-record",
        )


class UndoDeduplicationAccommodationRecordsFormWizard(
    UndoDeduplicationRecordsFormWizard
):
    model = MvAccommodation
    group_type = [
        GroupType.DEV,
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.view_deduplicated_accommodations_step_view = (
            UndoDeduplicationAccommodationRecordsViewSelectionStepView()
        )
        self.undo_deduplicated_accommodations_step_view = (
            UndoDeduplicationAccommodationRecordsUndoDeduplicationStepView()
        )
        self.deduplicated_records_restored_step_view = (
            UndoDeduplicationAccommodationRecordsRecordsRestoredStepView()
        )

    def get_view_duplicate_records_step_view(self):
        return self.view_deduplicated_accommodations_step_view

    def get_undo_deduplicate_records_step_view(self):
        return self.undo_deduplicated_accommodations_step_view

    def get_deduplicated_records_restored_step_view(self):
        return self.deduplicated_records_restored_step_view

    def get_template_names(self):
        return UNDO_DEDUPLICATION_FORM_TEMPLATES[self.steps.current]

    def post(self, *args, **kwargs):
        if self.steps.current == UndoDeduplicationRecordsStep.UNDO_DEDUPLICATE_RECORDS:
            return self.done(self.get_all_cleaned_data())

        return super().post(*args, **kwargs)

    def get_context_data(self, form=None, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        context["cancel_url"] = self.get_cancel_url()
        context["view_duplicate_records_url"] = reverse(
            "deduplication:accommodations:undo-deduplication-records-manual-step",
            kwargs={
                "step": UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                "id": self.kwargs["id"],
            },
        )
        context["type_list_url"] = reverse("accommodations:accommodations")
        context["type_record_url"] = reverse(
            "accommodations:detail-overview", kwargs={"pk": self.kwargs["id"]}
        )
        context["table_template_url"] = "accommodations/accommodations_list.html"

        context["type_title_plural"] = "Accommodation"
        context["type_title"] = "Accommodation"
        context["type"] = "accommodation"

        if self.steps.current == UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS:
            accommodation_id = self.kwargs["id"]
            dedup_group = (
                AccommodationDuplicateGroup.objects.filter(
                    principal_record_id=accommodation_id
                )
                .only("accommodations", "principal_record")
                .prefetch_related("accommodations")
                .first()
            )
            deduplicated_accommodations = (
                dedup_group.accommodations.all()
                .only("full_address", "postcode")
                .order_by("full_address")
            )
            if len(deduplicated_accommodations) == 2:
                deduplicated_accommodations_formatted = (
                    f"{deduplicated_accommodations[0].full_address} and "
                    f"{deduplicated_accommodations[1].full_address}"
                )
            else:
                deduplicated_accommodations_formatted = f"{
                    ', '.join(deduplicated_accommodations[:-1].full_address)
                    and deduplicated_accommodations[-1].full_address
                }"

            self.get_view_duplicate_records_step_view().deduplicated_accommodations = (
                deduplicated_accommodations
            )
            self.get_view_duplicate_records_step_view().request = self.request
            context |= self.get_view_duplicate_records_step_view().get_context_data()

            self.storage.extra_data["deduplication_data"] = {
                "principal_name": dedup_group.principal_record.full_address,
                "deduplicated_accommodation_data": [
                    {
                        "url": reverse(
                            "accommodations:detail-overview", args=[accommodation.pk]
                        ),
                        "name": accommodation.full_address,
                    }
                    for accommodation in deduplicated_accommodations
                ],
                "formatted_deduplicated_accommodations": (
                    deduplicated_accommodations_formatted
                ),
            }

            context["deduplicated_records"] = deduplicated_accommodations
            context["principal_record_name"] = dedup_group.principal_record.full_address

        if self.steps.current == UndoDeduplicationRecordsStep.UNDO_DEDUPLICATE_RECORDS:
            accommodation_id = self.kwargs["id"]
            dedup_group = (
                AccommodationDuplicateGroup.objects.filter(
                    principal_record_id=accommodation_id
                )
                .only("accommodations", "principal_record", "created_at")
                .prefetch_related("accommodations")
                .first()
            )
            deduplicated_accommodations = (
                dedup_group.accommodations.all()
                .only("full_address", "postcode")
                .order_by("full_address")
            )
            self.get_undo_deduplicate_records_step_view().deduplicated_accommodations = deduplicated_accommodations  # noqa: E501
            self.get_undo_deduplicate_records_step_view().request = self.request
            context |= self.get_undo_deduplicate_records_step_view().get_context_data()
            if len(deduplicated_accommodations) == 2:
                deduplicated_accommodations_formatted = (
                    f"{deduplicated_accommodations[0].full_address} and "
                    f"{deduplicated_accommodations[1].full_address}"
                )
            else:
                deduplicated_accommodations_formatted = f"{
                    ', '.join(deduplicated_accommodations[:-1].full_address)
                    and deduplicated_accommodations[-1].full_address
                }"
            context["deduplicated_records"] = deduplicated_accommodations_formatted
            context["principal_record_name"] = dedup_group.principal_record.full_address
            context["date"] = dedup_group.created_at

        if (
            self.steps.current
            == UndoDeduplicationRecordsStep.DEDUPLICATED_RECORDS_RESTORED
        ):
            deduplication_data = self.storage.extra_data.get("deduplication_data")

            self.get_undo_deduplicate_records_step_view().request = self.request
            context |= self.get_undo_deduplicate_records_step_view().get_context_data()

            context["principal_record_name"] = deduplication_data["principal_name"]
            context["deduplicated_record_data"] = deduplication_data[
                "deduplicated_accommodation_data"
            ]
            context["deduplicated_records_names_list_formatted"] = deduplication_data[
                "formatted_deduplicated_accommodations"
            ]

        return context

    def get_cancel_url(self):
        return (
            reverse("accommodations:detail-actions", kwargs={"pk": self.kwargs["id"]})
            + "?reset=true"
        )

    def done(self, form_list, **kwargs):
        accommodation_id = self.kwargs["id"]
        dedup_group = AccommodationDuplicateGroup.objects.prefetch_related(
            "accommodations"
        ).get(principal_record_id=accommodation_id)
        try:
            dedup_group.undo_deduplication(user=self.request.user)
        except Exception:
            messages.error(
                self.request,
                "The principal record has not been deleted and the original "
                "records were not restored.",
            )
            return redirect("accommodations:detail-actions", accommodation_id)

        return redirect(
            "deduplication:accommodations:complete-undo-deduplication"
            "-records-manual-step",
            UndoDeduplicationRecordsStep.DEDUPLICATED_RECORDS_RESTORED,
        )
