import os

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Layout
from crispy_forms_gds.layout.constants import Size
from django.db.models import Case, F, IntegerField, OuterRef, Q, Subquery, Value, When
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django_filters import (
    CharFilter,
    FilterSet,
    MultipleChoiceFilter,
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
from ontology.models import MvAccommodationRequest, ReassignmentRequest
from webapp.constants import ACCOMMODATION_REQUEST_SEARCH_FIELDS
from webapp.mixins import (
    FilterPanelMixin,
    PermissionsMixin,
)
from webapp.search import perform_search
from webapp.templatetags.reassignment_request_extras import (
    reassignment_request_outcome_label_to_tag_colour,
)
from webapp.utils import CustomDateColumn
from webapp.widgets import (
    CheckboxSelectMultipleWithTags,
)


class UnassignedAccommodationRequestsTable(tables.Table):
    title = Column(verbose_name="Name")
    latest_application_date = CustomDateColumn(verbose_name="Application date")
    address = Column(
        verbose_name="Address",
        empty_values=(),
        orderable=False,
    )
    postcode = Column(
        verbose_name="Postcode",
        empty_values=(),
        orderable=False,
    )
    reassignment_la = Column(
        verbose_name="Reassignment LA", accessor="latest_reassignment_la"
    )
    reassignment_status = Column(
        verbose_name="Reassignment status",
        accessor="latest_reassignment_status",
        empty_values=(),
    )
    # hide = TemplateColumn(
    #     template_code="""
    #         <a href="#">
    #            Hide
    #         </a>
    #     """,
    #     verbose_name="",
    #     orderable=False,
    # )

    def format_array_as_string(self, value):
        output = ""
        if value:
            for v in value:
                if v is not None:
                    output += f"{v}; "
                else:
                    output += "; "
            output = output.rstrip("; ")
        return output

    def render_title(self, record: MvAccommodationRequest, value):
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{}">{}</a>',
            reverse(
                "accommodation-requests:detail-overview",
                args=[record.id],
            ),
            value,
        )

    def render_address(self, record):
        accommodations = [
            accommodation.full_address for accommodation in record.get_accommodations()
        ]
        return self.format_array_as_string(accommodations)

    def render_postcode(self, record):
        postcodes = [
            accommodation.postcode for accommodation in record.get_accommodations()
        ]
        return self.format_array_as_string(postcodes)

    def render_reassignment_status(self, record):
        value = record.latest_reassignment_status or "Unassigned"
        return render_to_string(
            "webapp/components/reassignment_status_tag/reassignment_status_tag.html",
            {"reassignment_status": value},
        )

    class Meta:
        model = MvAccommodationRequest
        template_name = "webapp/components/tables/table.html"
        fields = (
            "title",
            "latest_application_date",
            "address",
            "postcode",
            "reassignment_la",
            "reassignment_status",
        )


class UnassignedAccommodationRequestsFilter(FilterSet, FilterPanelMixin):
    search = CharFilter(
        label="Search",
        method="search_filter",
        help_text="Search the data in the table",
    )

    status = MultipleChoiceFilter(
        choices=(
            ("Accepted", "Accepted"),
            ("Rejected", "Rejected"),
            ("Pending", "Pending"),
        ),
        null_label="Unassigned",
        label="Reassignment Status",
        field_name="latest_reassignment_status",
        widget=CheckboxSelectMultipleWithTags(
            label_to_tag_colour=reassignment_request_outcome_label_to_tag_colour
        ),
    )

    # TODO: Update with filter when hidden feature is implemented
    # hidden_records = BooleanFilter(
    #     label="Hidden records",
    #     widget=CheckboxInput(attrs={"value": "Show hidden records"}),
    #     method="include_hidden_filter",
    # )

    # def include_hidden_filter(self, queryset, _, value):
    #     return queryset

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, ACCOMMODATION_REQUEST_SEARCH_FIELDS)

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
            Field("status", context={"label_size": "govuk-fieldset__legend--m"}),
            # Fieldset(
            #     "hidden_records",
            #     legend="Hidden records",
            #     legend_size=Size.MEDIUM,
            #     css_class="govuk-!-margin-top-5",
            # ),
        )
        # form.fields["hidden_records"].label = "Show hidden records"
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
        fields_needed = [
            "title",
            "latest_application_date",
        ]
        latest_reassignment = ReassignmentRequest.objects.filter(
            accommodation_request_id=OuterRef("pk")
        ).order_by("-created_at")

        qs = (
            (
                MvAccommodationRequest.objects.filter(
                    (Q(ltla_name__len=0) | Q(ltla_name__isnull=True))
                    & (Q(utla_name__len=0) | Q(utla_name__isnull=True))
                ).annotate(
                    latest_reassignment_la=Subquery(
                        latest_reassignment.values("destination_ltla_name")[:1]
                    ),
                    latest_reassignment_status=Subquery(
                        latest_reassignment.values("outcome")[:1]
                    ),
                    status_order=Case(
                        When(latest_reassignment_status="Rejected", then=Value(0)),
                        When(latest_reassignment_status="Pending", then=Value(1)),
                        When(latest_reassignment_status="Accepted", then=Value(2)),
                        When(
                            latest_reassignment_status="Needs Accommodation Request",
                            then=Value(3),
                        ),
                        default=Value(99),
                        output_field=IntegerField(),
                    ),
                )
            )
            .order_by(
                "status_order", F("latest_application_date").desc(nulls_last=True)
            )
            .only(*fields_needed)
        )

        return qs
