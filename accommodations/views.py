import os
from typing import Optional

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Fieldset, Layout
from crispy_forms_gds.layout.constants import Size
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.forms import CheckboxInput
from django.http import HttpResponse, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html
from django.views import View
from django.views.generic import DetailView, UpdateView
from django_filters import (
    BooleanFilter,
    CharFilter,
    FilterSet,
)
from django_filters.views import FilterView
from django_tables2 import Column, LazyPaginator, SingleTableMixin, tables

from accommodations.forms import AccommodationEditForm
from accounts.enums import GroupType
from deduplication.models import AccommodationDuplicateGroup
from ontology.models import (
    MvAccommodation,
    MvInteraction,
    MvPerson,
    MvUkPostcode,
)
from webapp.constants import (
    ACCOMMODATION_SEARCH_FIELDS,
    FIX_DUPLICATE_RECORDS_ALLOWED_GROUP_TYPES,
)
from webapp.mixins import (
    AuditLogTimelineEventsMixin,
    FilterPanelMixin,
    InteractionTimelineEventsMixin,
    IsDuplicateMixin,
    PermissionsMixin,
    PIISafeRecordNameMixin,
)
from webapp.search import perform_search
from webapp.utils import LazyChoiceFilter
from webapp.views import (
    Action,
    ActionsListView,
    LinkAction,
    SummaryListView,
    TwoColumnSummaryListView,
)
from webapp.widgets import SearchableSelect


class AccommodationTable(tables.Table):
    full_address = Column(verbose_name="Address")
    postcode = Column(verbose_name="Postcode")
    ltla_name = Column(verbose_name="Lower tier LA")
    utla_name = Column(verbose_name="Upper tier LA")

    def render_full_address(self, record: MvAccommodation, value):
        dup_text = "Duplicate" if not record.is_principal else ""
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{url}">{value}</a>'
            '<div class="govuk-hint govuk-!-font-size-16 govuk-!-margin-top-1'
            ' govuk-!-margin-bottom-0">{dup_text}</div>',
            url=reverse("accommodations:detail-overview", args=[record.id]),
            value=value,
            dup_text=dup_text,
        )

    def render_postcode(self, value: MvUkPostcode):
        if value.postcode_formatted:
            return value.postcode_formatted
        if value.postcode:
            return value.postcode
        return ""

    class Meta:
        model = MvAccommodation
        template_name = "webapp/components/tables/table.html"
        fields = (
            "full_address",
            "postcode",
            "ltla_name",
            "utla_name",
        )


class AccommodationFilter(FilterSet, FilterPanelMixin):
    search = CharFilter(
        label="Search",
        method="search_filter",
        help_text="Search the data in the table",
    )

    ltla_name = LazyChoiceFilter(
        choices=lambda: [
            (ltla, ltla) for ltla in MvAccommodation.objects.get_queryset().ltla_names()
        ],
        label="Lower tier local authority (LTLA)",
        empty_label="",
        lookup_expr="icontains",
        widget=SearchableSelect(),
    )

    utla_name = LazyChoiceFilter(
        choices=lambda: [
            (utla, utla) for utla in MvAccommodation.objects.get_queryset().utla_names()
        ],
        label="Upper tier local authority (UTLA)",
        empty_label="",
        lookup_expr="icontains",
        widget=SearchableSelect(),
    )

    include_duplicates = BooleanFilter(
        label="Duplicate accommodations",
        widget=CheckboxInput(attrs={"value": "Include duplicate records"}),
        method="include_duplicates_filter",
    )

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, ACCOMMODATION_SEARCH_FIELDS)

    def include_duplicates_filter(self, queryset, _, value):
        if not value:
            return queryset.filter(is_principal=True)
        return queryset

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
            Field.text("ltla_name", small=True, label_size=Size.MEDIUM),
            Field.text("utla_name", small=True, label_size=Size.MEDIUM),
            Fieldset(
                "include_duplicates",
                legend="Duplicate accommodations",
                legend_size=Size.MEDIUM,
                css_class="govuk-!-margin-top-5",
            ),
        )
        form.fields["include_duplicates"].label = "Include duplicate records"
        return form

    class Meta:
        model = MvAccommodation
        fields = [
            "search",
        ]


class AccommodationsListView(PermissionsMixin, SingleTableMixin, FilterView):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    model = MvAccommodation
    table_class = AccommodationTable
    filterset_class = AccommodationFilter
    paginate_by = os.environ.get("PAGINATION_PAGE_SIZE")
    paginator_class = LazyPaginator
    template_name = "accommodations/accommodations_list_page.html"

    def get_queryset(self):
        fields_needed = [
            "id",
            "full_address",
            "postcode_id",
            "utla_name",
            "ltla_name",
        ]

        qs = super().get_queryset()
        qs = self.filterset_class(
            self.request.GET,
            queryset=qs,
        ).qs

        return qs.only(*fields_needed).order_by("full_address")


class AccommodationDetailOverviewView(
    PIISafeRecordNameMixin, PermissionsMixin, IsDuplicateMixin, SummaryListView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "accommodations/detail_view/detail_view_overview.html"
    model = MvAccommodation

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.object.is_editable and self.user_can_edit(
            group_types=[
                GroupType.DEV,
                GroupType.LOCAL_AUTHORITY,
                GroupType.DEVOLVED_ADMINISTRATION,
            ]
        ):
            ctx["edit_url"] = reverse(
                "accommodations:edit", kwargs={"pk": self.object.pk}
            )

        postcode = self.object.get_postcode()

        ctx["fields"] = [
            ("Address", self.object.full_address),
            (
                "Postcode",
                postcode.display_postcode() if postcode else None,
            ),
            ("Current capacity", self.object.current_capacity),
            ("Availability start date", self.object.availability_start_date),
            ("Availability end date", self.object.availability_end_date),
            ("Wheelchair accessible", self.object.wheelchair_accessible),
            ("Lower tier LA", self.object.ltla_name),
            ("Upper tier LA", self.object.utla_name),
        ]

        ctx["show_actions_tab"] = self.user_action_allowed(
            group_types=AccommodationDetailActionsView.group_type
        )
        ctx["show_history_tab"] = self.user_action_allowed(
            group_types=AccommodationDetailHistoryView.group_type
        )

        return ctx


class AccommodationDetailLinkedRecordsView(
    PIISafeRecordNameMixin, PermissionsMixin, IsDuplicateMixin, DetailView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "accommodations/detail_view/detail_view_linked_records.html"
    model = MvAccommodation

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        linked_records = []
        user = self.request.user
        accommodation = self.object

        accommodation_requests = (
            accommodation.get_accommodation_requests_restrict_for_user(user)
        )
        if accommodation_requests.exists():
            linked_records.append(("Accommodation requests", accommodation_requests))

            guests = MvPerson.objects.none()
            for ar in accommodation_requests.all():
                guests |= ar.get_people_restrict_for_user(user)

            if guests.exists():
                linked_records.append(("Guests", guests))

        hosts = accommodation.get_hosts_restrict_for_user(user)
        if hosts.exists():
            linked_records.append(("Host", hosts))

        visa_applications = accommodation.get_visa_applications_restrict_for_user(user)
        if visa_applications.exists():
            linked_records.append(("Visa applications", visa_applications))

        ctx["fields"] = linked_records

        ctx["show_actions_tab"] = self.user_action_allowed(
            group_types=AccommodationDetailActionsView.group_type
        )
        ctx["show_history_tab"] = self.user_action_allowed(
            group_types=AccommodationDetailHistoryView.group_type
        )
        return ctx


class AccommodationDetailPropertiesView(
    PIISafeRecordNameMixin, PermissionsMixin, IsDuplicateMixin, TwoColumnSummaryListView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "accommodations/detail_view/detail_view_properties.html"
    model = MvAccommodation

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["show_actions_tab"] = self.user_action_allowed(
            group_types=AccommodationDetailActionsView.group_type
        )
        ctx["show_history_tab"] = self.user_action_allowed(
            group_types=AccommodationDetailHistoryView.group_type
        )
        return ctx

    class Meta:
        exclude_fields = [
            "archived_at",
            "is_archived",
        ]


class AccommodationDetailActionsView(
    PIISafeRecordNameMixin, PermissionsMixin, IsDuplicateMixin, ActionsListView
):
    group_type = list(FIX_DUPLICATE_RECORDS_ALLOWED_GROUP_TYPES)
    template_name = "accommodations/detail_view/detail_view_actions.html"
    model = MvAccommodation

    def __init__(self, **kwargs):
        self.merged_accommodation_names = ""
        super().__init__(*kwargs)

    def get_actions(self) -> list[Action]:
        dup_group = AccommodationDuplicateGroup.objects.filter(
            principal_record_id=self.object.pk
        ).first()

        actions: list[Action] = []

        if dup_group:
            merged_accommodations = dup_group.accommodations.all()

            merged_accommodations_names = [
                format_html(
                    '<a class="govuk-link" href="{url}">{value}</a>',
                    url=reverse(
                        "accommodations:detail-overview", args=[accommodation.id]
                    ),
                    value=accommodation.full_address,
                )
                for accommodation in merged_accommodations
            ]

            merged_accommodations_names = sorted(merged_accommodations_names)
            if len(merged_accommodations_names) == 2:
                merged_accommodations_formatted = (
                    f"{merged_accommodations_names[0]} and "
                    f"{merged_accommodations_names[1]}"
                )
            else:
                merged_accommodations_formatted = f"{
                    ', '.join(merged_accommodations_names[:-1])
                    and merged_accommodations_names[-1]
                }"

            further_dup_group: Optional[AccommodationDuplicateGroup] = (
                AccommodationDuplicateGroup.objects.filter(
                    accommodations__pk=self.object.pk
                )
                .only("principal_record", "created_at")
                .first()
            )

            if self.object.is_principal:
                actions.append(
                    LinkAction(
                        label="Undo deduplication",
                        url_text="Start",
                        text=f"Delete this record and restore separate records for "
                        f"{merged_accommodations_formatted}.",
                        url=reverse(
                            "deduplication:accommodations:undo-deduplication-records-manual-step",
                            kwargs={
                                "step": "view-duplicate-records",
                                "id": self.object.id,
                            },
                        ),
                    )
                )
            elif further_dup_group:
                actions.append(
                    LinkAction(
                        label="Undo deduplication",
                        text="This deduplication cannot yet be undone due to a "
                        "further deduplication. To restore this record, first undo the "
                        "deduplication from the "
                        f"{
                            format_html(
                                '<a href={}>actions tab for {}.</a><br></br>',
                                reverse(
                                    'accommodations:detail-actions',
                                    args=[further_dup_group.principal_record.pk],
                                ),
                                further_dup_group.principal_record.full_address,
                            )
                        }"
                        "A full deduplication history is in the history tab.",
                    )
                )
        return actions

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["show_actions_tab"] = self.user_action_allowed(
            group_types=AccommodationDetailActionsView.group_type
        )
        ctx["show_history_tab"] = self.user_action_allowed(
            group_types=AccommodationDetailHistoryView.group_type
        )
        return ctx


class AccommodationDetailHistoryView(
    PIISafeRecordNameMixin,
    PermissionsMixin,
    IsDuplicateMixin,
    InteractionTimelineEventsMixin,
    AuditLogTimelineEventsMixin,
    DetailView,
):
    group_type = [
        GroupType.DEV,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
    ]
    interaction_restrictions = {
        GroupType.LOCAL_AUTHORITY: {
            "allowed_contacts": [
                MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
                MvInteraction.InteractionContact.RECORD_DEDUPLICATION_UNDONE,
            ],
            "show_actor_names": False,
        },
        GroupType.DEVOLVED_ADMINISTRATION: {
            "allowed_contacts": [
                MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
                MvInteraction.InteractionContact.RECORD_DEDUPLICATION_UNDONE,
            ],
            "show_actor_names": False,
        },
    }
    audit_log_restrictions = {
        GroupType.LOCAL_AUTHORITY: {"hide_audit_logs": True},
        GroupType.DEVOLVED_ADMINISTRATION: {"hide_audit_logs": True},
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_history_tab"] = self.user_action_allowed(
            group_types=self.group_type
        )
        context["show_actions_tab"] = self.user_action_allowed(
            group_types=AccommodationDetailActionsView.group_type
        )
        context["history_description"] = (
            "This history shows the dates a change was made to the accommodation "
            "record on the system."
        )
        return context

    template_name = "accommodations/detail_view/detail_view_history.html"
    model = MvAccommodation


class AccommodationEditView(
    PIISafeRecordNameMixin, PermissionsMixin, SuccessMessageMixin, UpdateView
):
    model = MvAccommodation
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    form_class = AccommodationEditForm
    success_message = "Your changes have been saved"
    template_name = "accommodations/edit_view/edit_view_question.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.is_editable:
            return HttpResponse(status=404)
        return super().dispatch(request, *args, **kwargs)

    def _get_object_details_view(self):
        return reverse_lazy(
            "accommodations:detail-overview", kwargs={"pk": self.object.pk}
        )

    def get_success_url(self):
        return self._get_object_details_view()

    def get_cancel_url(self):
        return self._get_object_details_view()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["accommodation"] = self.object

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.get_cancel_url()
        return context

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None


class PostcodeSearchView(PermissionsMixin, View):
    model = MvAccommodation
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]

    def get(self, request):
        query = request.GET.get("q", "").strip()

        if query and len(query) >= 2:
            postcodes = (
                MvUkPostcode.objects.get_for_user(request.user)
                .filter(
                    Q(postcode_formatted__icontains=query)
                    | Q(postcode__icontains=query)
                )
                .only("postcode_formatted")
                .order_by("postcode_formatted")[:25]
            )

            return JsonResponse(
                {"results": [postcode.postcode_formatted for postcode in postcodes]}
            )

        return JsonResponse({"results": []})
