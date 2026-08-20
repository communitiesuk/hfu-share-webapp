import os
from enum import StrEnum
from typing import Literal

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Fieldset, Layout
from crispy_forms_gds.layout.constants import Size
from django.contrib import messages
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import F, OuterRef, Q, Subquery
from django.forms import CheckboxInput
from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
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
)
from webapp.constants import (
    ACCOMMODATION_REQUEST_SEARCH_FIELDS,
    UNASSIGNED_ACCOMMODATION_REQUESTS_ALLOWED_GROUP_TYPES,
)
from webapp.mixins import (
    FilterPanelMixin,
    PermissionsMixin,
    PIISafeRecordNameMixin,
)
from webapp.search import perform_search
from webapp.utils import CustomDateColumn

from .forms import (
    AssignLocalAuthorityFormSelectLocalAuthorityStep,
    AssignLocalAuthorityFormSelectRegionStep,
)


def is_hidden(record: MvAccommodationRequest) -> bool:
    return hasattr(record, "hidden_unassigned_record")


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
        verbose_name="Actions",
        accessor="id",
        orderable=False,
        attrs={"th": {"visually_hidden_header": True}},
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
            )
            + "?from=unassigned-accommodation-requests",
            value,
        )

    def hide_link(self, record):
        return format_html(
            '<a class="govuk-body-s govuk-link govuk-link--no-visited-state" '
            'href="{}">Hide<span class="govuk-visually-hidden"> {}</span></a>',
            reverse(
                "unassigned-accommodation-requests:hide",
                args=[record.id],
            ),
            record.title,
        )

    def unhide_form(self, record):
        return format_html(
            '<form method="post" action={action_url} style="display: inline;">'
            '<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">'
            '<button type="submit" class="govuk-link govuk-link--no-visited-state">'
            "Unhide"
            '<span class="govuk-visually-hidden"> {record_name}</span>'
            "</button>"
            "</form>",
            action_url=reverse(
                "unassigned-accommodation-requests:unhide",
                args=[record.id],
            ),
            csrf_token=get_token(self.request),
            record_name=record.title,
        )

    def render_hide(self, record: MvAccommodationRequest):
        return self.unhide_form(record) if is_hidden(record) else self.hide_link(record)

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
        method=lambda qs, name, value: qs,
    )

    @property
    def qs(self):
        qs = super().qs

        if self.form.is_valid():
            show_hidden = self.form.cleaned_data.get("hidden_records")
        else:
            show_hidden = False

        if not show_hidden:
            qs = qs.not_hidden()

        return qs

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
    group_type = UNASSIGNED_ACCOMMODATION_REQUESTS_ALLOWED_GROUP_TYPES
    model = MvAccommodationRequest
    table_class = UnassignedAccommodationRequestsTable
    filterset_class = UnassignedAccommodationRequestsFilter
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    paginator_class = LazyPaginator
    template_name = "unassigned_accommodation_requests/unassigned_accommodation_requests_list_page.html"  # noqa: E501

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

        return (
            MvAccommodationRequest.objects.unassigned()
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


class HideUnhideUnassignedAccommodationRequestViewBase(
    PermissionsMixin, SingleObjectMixin, View
):
    group_type = UNASSIGNED_ACCOMMODATION_REQUESTS_ALLOWED_GROUP_TYPES
    model = MvAccommodationRequest
    success_state: Literal["hidden", "unhidden"]

    def get_success_url(self):
        return reverse(
            "unassigned-accommodation-requests:unassigned-accommodation-requests"
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        try:
            with transaction.atomic():
                self.db_action(request)
        except HiddenUnassignedAccommodationRequest.DoesNotExist:
            messages.error(request, "The record is already visible.")
        except DatabaseError:
            messages.error(request, f"The record has not been {self.success_state}.")
        else:
            messages.success(
                request,
                f"The accommodation request has been {self.success_state}.",
            )

        return redirect(self.get_success_url())

    def db_action(self, request: HttpRequest) -> None:
        raise NotImplementedError("Subclasses must implement db_action")


class HideUnassignedAccommodationRequestView(
    HideUnhideUnassignedAccommodationRequestViewBase, TemplateResponseMixin
):
    template_name = "unassigned_accommodation_requests/hide_confirm_page.html"
    success_state = "hidden"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_to_response(
            {"object": self.object, "cancel_url": self.get_success_url()}
        )

    def db_action(self, request):
        HiddenUnassignedAccommodationRequest.objects.create(
            accommodation_request=self.object,
            hidden_by=request.user,
        )


class UnhideUnassignedAccommodationRequestView(
    HideUnhideUnassignedAccommodationRequestViewBase
):
    success_state = "unhidden"

    def db_action(self, _request):
        HiddenUnassignedAccommodationRequest.objects.get(
            accommodation_request=self.object,
        ).delete()


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
    group_type = UNASSIGNED_ACCOMMODATION_REQUESTS_ALLOWED_GROUP_TYPES
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
        local_authority = self.get_all_cleaned_data()["local_authority"]

        try:
            self.object.assign_local_authority(local_authority, self.request.user)

            guest_names = self.object.get_guest_names()
            guest_names_prefix = f"{guest_names} " if guest_names else ""
            messages.success(
                self.request,
                f"You have assigned {guest_names_prefix}to "
                f"{local_authority.ltla_name}.",
            )
        except (IntegrityError, DatabaseError):
            messages.error(
                self.request,
                "The record has not been assigned. We do not know why this "
                "happened. You can try again now or later.",
            )

        return redirect(
            f"{self.get_cancel_url()}?from=unassigned-accommodation-requests"
        )
