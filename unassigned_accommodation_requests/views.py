import os
from enum import StrEnum

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Fieldset, Layout
from crispy_forms_gds.layout.constants import Size
from django.contrib import messages
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import Exists, F, OuterRef, Q, Subquery
from django.forms import CheckboxInput
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.detail import SingleObjectMixin
from django_filters import (
    BooleanFilter,
    CharFilter,
    FilterSet,
    UnknownFieldBehavior,
)
from django_filters.views import FilterView
from django_tables2 import (
    Column,
    LazyPaginator,
    SingleTableMixin,
    tables,
)
from formtools.wizard.views import NamedUrlSessionWizardView

from ontology.models import (
    HiddenUnassignedAccommodationRequest,
    MvAccommodation,
    MvAccommodationRequest,
    MvVolunteer,
)
from webapp.constants import ACCOMMODATION_REQUEST_SEARCH_FIELDS
from webapp.mixins import (
    FilterPanelMixin,
    PermissionsMixin,
    PIISafeRecordNameMixin,
)
from webapp.search import perform_search
from webapp.utils import CustomDateColumn

from .constants import UNASSIGNED_ACCOMMODATION_REQUESTS_GROUP_TYPES
from .forms import (
    AssignLocalAuthorityFormSelectLocalAuthorityStep,
    AssignLocalAuthorityFormSelectRegionStep,
)


def is_hidden(record: MvAccommodationRequest) -> bool:
    """Stub until the hidden records table exists."""
    return False


class UnassignedAccommodationRequestsTable(tables.Table):
    title = Column(verbose_name="Name")
    latest_application_date = CustomDateColumn(verbose_name="Date of application")
    address = Column(
        verbose_name="Address",
        empty_values=(),
        order_by=("address_sort_value", "title"),
    )
    postcode = Column(
        verbose_name="Postcode",
        empty_values=(),
        order_by=("postcode_sort_value", "title"),
    )
    hide = Column(
        verbose_name=mark_safe('<span class="govuk-visually-hidden">Actions</span>'),
        accessor="id",
        orderable=False,
    )

    def render_address(self, record: MvAccommodationRequest):
        return [
            accommodation.full_address or "" for accommodation in record.accommodations
        ]

    def render_postcode(self, record: MvAccommodationRequest):
        return [
            str(accommodation.postcode) if accommodation.postcode else ""
            for accommodation in record.accommodations
        ]

    def render_title(self, record: MvAccommodationRequest, value):
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{}">{}</a>',
            reverse(
                "accommodation-requests:detail-overview",
                args=[record.id],
            ),
            value,
        )

    def render_hide(self, record: MvAccommodationRequest):
        label = "Unhide" if is_hidden(record) else "Hide"
        return format_html(
            '<a class="govuk-body-s govuk-link govuk-link--no-visited-state" '
            'href="{}">{}</a>',
            reverse(
                "unassigned-accommodation-requests:hide",
                args=[record.id],
            ),
            label,
        )

    class Meta:
        model = MvAccommodationRequest
        template_name = "webapp/components/tables/table.html"
        fields = (
            "title",
            "latest_application_date",
            "address",
            "postcode",
            "hide",
        )


class UnassignedAccommodationRequestsFilter(FilterSet, FilterPanelMixin):
    search = CharFilter(
        label="Search",
        method="search_filter",
        help_text="Search the data in the table",
    )

    hidden_records = BooleanFilter(
        label="Hidden records",
        widget=CheckboxInput(attrs={"value": "Show hidden records"}),
        method="include_hidden_filter",
    )

    def include_hidden_filter(self, queryset, _, value):
        """Stub until the hidden records table exists."""
        return queryset

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, ACCOMMODATION_REQUEST_SEARCH_FIELDS)

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
            Fieldset(
                "hidden_records",
                legend="Hidden records",
                legend_size=Size.MEDIUM,
                css_class="govuk-!-margin-top-5",
            ),
        )
        form.fields["hidden_records"].label = "Show hidden records"
        return form

    class Meta:
        model = MvAccommodationRequest
        fields = ("search",)
        unknown_field_behavior = UnknownFieldBehavior.IGNORE


class UnassignedAccommodationRequestsListView(
    PermissionsMixin, SingleTableMixin, FilterView
):
    group_type = UNASSIGNED_ACCOMMODATION_REQUESTS_GROUP_TYPES
    model = MvAccommodationRequest
    table_class = UnassignedAccommodationRequestsTable
    filterset_class = UnassignedAccommodationRequestsFilter
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    paginator_class = LazyPaginator
    template_name = "unassigned_accommodation_requests/unassigned_accommodation_requests_list_page.html"  # noqa: E501
    super_sponsors_to_filter = [
        "Scottish Government",
        "Scotland Government",
        "Welsh Government",
        "Wales Government",
    ]

    def get_queryset(self):
        accommodations = MvAccommodation.objects.filter(
            Q(id__any=OuterRef("accommodation_id"))
            | Q(
                id__in=[
                    OuterRef("bridging_accommodation_id"),
                    OuterRef("temporary_accommodation_id"),
                    OuterRef("primary_accommodation_id"),
                ]
            )
        ).order_by("id")

        sponsors = MvVolunteer.objects.filter(
            Q(id__any=OuterRef("sponsor_id")) | Q(id=OuterRef("primary_sponsor_id"))
        )

        name_filter = Q()
        for name in self.super_sponsors_to_filter:
            name_filter |= Q(full_name__icontains=name)

        super_sponsors = sponsors.filter(name_filter)

        return (
            MvAccommodationRequest.objects.filter(
                (Q(ltla_name__len=0) | Q(ltla_name__isnull=True))
                & (Q(utla_name__len=0) | Q(utla_name__isnull=True))
            )
            .exclude(Exists(super_sponsors))
            .exclude(hidden_unassigned_record__isnull=False)
            .annotate(
                address_sort_value=Subquery(accommodations.values("full_address")[:1]),
                postcode_sort_value=Subquery(
                    accommodations.values("postcode__postcode_formatted")[:1]
                ),
            )
            .order_by(F("latest_application_date").desc(nulls_last=True), "title")
            .only(
                "title",
                "latest_application_date",
                "accommodation_id",
                "bridging_accommodation_id",
                "temporary_accommodation_id",
                "primary_accommodation_id",
            )
        )


class HideUnassignedAccommodationRequestView(
    PermissionsMixin, SingleObjectMixin, TemplateResponseMixin, View
):
    group_type = UNASSIGNED_ACCOMMODATION_REQUESTS_GROUP_TYPES
    model = MvAccommodationRequest
    template_name = "unassigned_accommodation_requests/hide_confirm_page.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def get_success_url(self):
        return reverse(
            "unassigned-accommodation-requests:unassigned-accommodation-requests"
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_to_response(
            {"object": self.object, "cancel_url": self.get_success_url()}
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            with transaction.atomic():
                HiddenUnassignedAccommodationRequest.objects.create(
                    accommodation_request=self.object,
                    hidden_by=request.user,
                )
        except (IntegrityError, DatabaseError):
            messages.error(request, "The record has not been hidden.")
        else:
            messages.success(request, "The accommodation request has been hidden.")
        return redirect(self.get_success_url())


class AssignLocalAuthorityFormSteps(StrEnum):
    REGION = "region"
    LOCAL_AUTHORITY = "local-authority"


ASSIGN_LOCAL_AUTHORITY_FORMS = [
    (
        AssignLocalAuthorityFormSteps.REGION,
        AssignLocalAuthorityFormSelectRegionStep,
    ),
    (
        AssignLocalAuthorityFormSteps.LOCAL_AUTHORITY,
        AssignLocalAuthorityFormSelectLocalAuthorityStep,
    ),
]


class AssignLocalAuthorityFormWizard(
    PIISafeRecordNameMixin,
    PermissionsMixin,
    SingleObjectMixin,
    NamedUrlSessionWizardView,
):
    model = MvAccommodationRequest
    group_type = UNASSIGNED_ACCOMMODATION_REQUESTS_GROUP_TYPES
    template_name = (
        "unassigned_accommodation_requests/"
        "assign_local_authority/"
        "assign_local_authority_page.html"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        if self.object.ltla_name:
            return HttpResponse(status=409)

        if "reset" in self.request.GET:
            self.storage.reset()

        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        if self.object.ltla_name:
            return HttpResponse(status=409)

        return super().post(*args, **kwargs)

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)

        if step == AssignLocalAuthorityFormSteps.LOCAL_AUTHORITY:
            region_data = (
                self.get_cleaned_data_for_step(AssignLocalAuthorityFormSteps.REGION)
                or {}
            )
            kwargs["region"] = region_data.get("region")

        return kwargs

    def get_step_url(self, step):
        return reverse(self.url_name, kwargs={"step": step, "pk": self.object.pk})

    def get_prefix(self, request, *args, **kwargs):
        return f"assign_local_authority_form_wizard_{self.object.pk}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.get_cancel_url()
        return context

    def get_cancel_url(self):
        return reverse(
            "accommodation-requests:detail-overview", kwargs={"pk": self.object.pk}
        )

    def done(self, form_list, **kwargs):
        self.object.assign_local_authority(
            self.get_all_cleaned_data()["local_authority"]
        )

        return redirect(self.get_cancel_url())
