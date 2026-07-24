import os

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Fieldset, Layout
from crispy_forms_gds.layout.constants import Size
from django.db.models import F, OuterRef, Q, Subquery
from django.forms import CheckboxInput
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
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

from accounts.enums import GroupType
from ontology.models import MvAccommodation, MvAccommodationRequest
from webapp.constants import ACCOMMODATION_REQUEST_SEARCH_FIELDS
from webapp.mixins import (
    FilterPanelMixin,
    PermissionsMixin,
)
from webapp.search import perform_search
from webapp.utils import CustomDateColumn


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
        empty_values=(),
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

    def render_hide(self, record):
        label = "Unhide" if is_hidden(record) else "Hide"
        # No href until hiding is implemented, so the link cannot be actioned
        return format_html(
            '<a class="govuk-body-s govuk-link" aria-disabled="true">{}</a>',
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
    group_type = [
        GroupType.DEV,
        GroupType.MHCLG,
        GroupType.SERVICE_SUPPORT,
    ]
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
            MvAccommodationRequest.objects.filter(
                (Q(ltla_name__len=0) | Q(ltla_name__isnull=True))
                & (Q(utla_name__len=0) | Q(utla_name__isnull=True))
            )
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
