import os
from datetime import datetime, timedelta
from typing import Optional

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Fieldset, Layout
from crispy_forms_gds.layout.constants import Size
from django.contrib.messages.views import SuccessMessageMixin
from django.forms import CheckboxInput
from django.forms.widgets import CheckboxSelectMultiple
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html
from django.views.generic import DetailView, UpdateView
from django_filters import (
    BooleanFilter,
    CharFilter,
    FilterSet,
    MultipleChoiceFilter,
)
from django_filters.views import FilterView
from django_tables2 import (
    Column,
    LazyPaginator,
    SingleTableMixin,
    tables,
)

from accounts.enums import GroupType
from deduplication.models import SponsorDuplicateGroup
from ontology.models import MvInteraction, MvVolunteer
from webapp.constants import SPONSORS_SEARCH_FIELDS
from webapp.mixins import (
    AuditLogTimelineEventsMixin,
    FilterPanelMixin,
    InteractionTimelineEventsMixin,
    IsDuplicateMixin,
    MultiLABannerMixin,
    PermissionsMixin,
    PIISafeRecordNameMixin,
)
from webapp.search import perform_search
from webapp.utils import (
    CustomDateColumn,
    CustomDateFromToRangeFilter,
    CustomDateTimeColumn,
)
from webapp.views import (
    Action,
    ActionsListView,
    LinkAction,
    SummaryListView,
    TwoColumnSummaryListView,
)
from webapp.widgets import DatePicker, StackedRangeInput

from .forms import SponsorEditForm

EXCESSIVE_SPONSOR_THRESHOLD = 1000


class SponsorsTable(tables.Table):
    full_name = Column(verbose_name="Name")
    sex = Column(verbose_name="Sex")
    date_of_birth = CustomDateColumn(verbose_name="Date of birth")
    email = Column(verbose_name="Email address")
    phone_number = Column(verbose_name="Phone number")
    is_eoi = Column(verbose_name="EOI host")
    created_date = CustomDateTimeColumn(verbose_name="Date added")

    def render_full_name(self, record: MvVolunteer, value):
        dup_text = "Duplicate" if not record.is_principal else ""
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{url}">{value}</a>'
            '<div class="govuk-hint govuk-!-font-size-16 govuk-!-margin-top-1'
            ' govuk-!-margin-bottom-0">{dup_text}</div>',
            url=reverse("sponsors:detail-overview", args=[record.id]),
            value=value,
            dup_text=dup_text,
        )

    def render_phone_number(self, value):
        return value[0] if value else None

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


class SponsorsFilter(FilterSet, FilterPanelMixin):
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

    include_duplicates = BooleanFilter(
        label="Duplicate sponsors and hosts",
        widget=CheckboxInput(attrs={"value": "Include duplicate records"}),
        method="include_duplicates_filter",
    )

    def show_eoi_hosts(self, queryset, _, value):
        if not value:
            return queryset

        return queryset.filter(is_eoi=value)

    def include_duplicates_filter(self, queryset, _, value):
        if not value:
            return queryset.filter(is_principal=True)
        return queryset

    search = CharFilter(
        label="Search",
        method="search_filter",
        help_text="Search the data in the table",
    )

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, SPONSORS_SEARCH_FIELDS)

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
            Fieldset(
                "include_duplicates",
                legend="Duplicate sponsors and hosts",
                legend_size=Size.MEDIUM,
                css_class="govuk-!-margin-top-5",
            ),
        )
        form.fields["include_duplicates"].label = "Include duplicate records"
        return form

    class Meta:
        model = MvVolunteer
        fields = [
            "search",
            "sex",
            "date_of_birth",
            "include_duplicates",
        ]


class SponsorsListView(PermissionsMixin, SingleTableMixin, FilterView):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    model = MvVolunteer
    table_class = SponsorsTable
    filterset_class = SponsorsFilter
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    paginator_class = LazyPaginator
    template_name = "sponsors/sponsors_list_page.html"

    def get_queryset(self):
        fields_needed = [
            "full_name",
            "sex",
            "date_of_birth",
            "email",
            "phone_number",
        ]

        qs = super().get_queryset()
        qs = self.filterset_class(
            self.request.GET,
            queryset=qs,
        ).qs

        return qs.only(*fields_needed).order_by("full_name")


class SponsorDetailOverviewView(
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
    template_name = "sponsors/detail_view/detail_view_overview.html"
    model = MvVolunteer

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
                "sponsors:detail-edit", kwargs={"pk": self.object.pk}
            )

        ctx["show_history_tab"] = self.user_action_allowed(
            group_types=SponsorDetailHistoryView.group_type
        )

        ctx["show_actions_tab"] = self.user_action_allowed(
            group_types=SponsorDetailActionsView.group_type
        )

        ctx["fields"] = [
            ("First name", self.object.first_name),
            ("Last name", self.object.last_name),
            ("Date of birth", self.object.date_of_birth),
            ("Sex", self.object.sex),
            ("Email", self.object.email),
            ("Phone number", self.object.phone_number),
            ("Relationship status", self.object.family_situation),
            ("DBS check status", self.object.determine_dbs_check_status().label),
            ("Passport number", self.object.passport_details),
            ("Host", self.object.is_eoi),
            ("Sponsor", self.object.is_sponsor),
        ]
        return ctx


class SponsorDetailActionsView(
    PIISafeRecordNameMixin,
    MultiLABannerMixin,
    PermissionsMixin,
    IsDuplicateMixin,
    ActionsListView,
):
    group_type = [GroupType.DEV]
    template_name = "sponsors/detail_view/detail_view_actions.html"
    model = MvVolunteer

    def __init__(self, **kwargs):
        self.merged_sponsors_names = ""
        super().__init__(*kwargs)

    def get_actions(self) -> list[Action]:
        dup_group = SponsorDuplicateGroup.objects.filter(
            principal_record_id=self.object.pk
        ).first()

        actions: list[Action] = []

        if dup_group:
            merged_sponsors = dup_group.sponsors.all()

            merged_sponsors_names = [
                format_html(
                    '<a class="govuk-link" href="{url}">{value}</a>',
                    url=reverse("sponsors:detail-overview", args=[sponsor.id]),
                    value=sponsor.full_name,
                )
                for sponsor in merged_sponsors
            ]

            merged_sponsors_names = sorted(merged_sponsors_names)
            if len(merged_sponsors_names) == 2:
                merged_sponsors_formatted = (
                    f"{merged_sponsors_names[0]} and {merged_sponsors_names[1]}"
                )
            else:
                merged_sponsors_formatted = f"{
                    ', '.join(merged_sponsors_names[:-1]) and merged_sponsors_names[-1]
                }"

            further_dup_group: Optional[SponsorDuplicateGroup] = (
                SponsorDuplicateGroup.objects.filter(sponsors__pk=self.object.pk)
                .only("principal_record", "created_at")
                .first()
            )

            can_undo_deduplication = dup_group.can_undo_deduplication(self.object)

            if not can_undo_deduplication:
                actions.append(
                    LinkAction(
                        label="Undo deduplication",
                        text="This sponsor is linked to multiple local authorities "
                        "(LAs) so deduplication cannot be undone.",
                    )
                )
            elif self.object.is_principal:
                actions.append(
                    LinkAction(
                        label="Undo deduplication",
                        url_text="Start",
                        text=f"Delete this record and restore separate records for "
                        f"{merged_sponsors_formatted}.",
                        url=reverse(
                            "deduplication:sponsors:undo-deduplication-records-manual-step",
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
                                    'sponsors:detail-actions',
                                    args=[further_dup_group.principal_record.pk],
                                ),
                                further_dup_group.principal_record.full_name,
                            )
                        }"
                        "A full deduplication history is in the history tab.",
                    )
                )
        return actions

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["show_history_tab"] = self.user_action_allowed(
            group_types=SponsorDetailHistoryView.group_type
        )

        ctx["show_actions_tab"] = self.user_action_allowed(
            group_types=SponsorDetailActionsView.group_type
        )

        return ctx


class SponsorDetailLinkedRecordsView(
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
    template_name = "sponsors/detail_view/detail_view_linked_records.html"
    model = MvVolunteer

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        linked_records = []
        user = self.request.user
        sponsor = self.object

        accommodation_requests = sponsor.get_accommodation_requests_restrict_for_user(
            user
        )

        is_excessive_sponsor = (
            accommodation_requests.count() > EXCESSIVE_SPONSOR_THRESHOLD
        )
        if is_excessive_sponsor:
            linked_records.append(
                ("Accommodation requests", ["There are too many records to display."])
            )
        else:
            if accommodation_requests.exists():
                linked_records.append(
                    ("Accommodation requests", accommodation_requests)
                )

            accommodations = sponsor.get_accommodations_restrict_for_user(user)
            if accommodations.exists():
                linked_records.append(("Accommodation", accommodations))

            visa_applications = (
                sponsor.application_unique_application_number_restrict_for_user(user)
            )
            if visa_applications.exists():
                linked_records.append(("Visa applications", visa_applications))

            guests = sponsor.get_guests_restrict_for_user(user)
            if guests.exists():
                linked_records.append(("Guests", guests))

        ctx["fields"] = linked_records
        ctx["show_history_tab"] = self.user_action_allowed(
            group_types=SponsorDetailHistoryView.group_type
        )
        ctx["show_actions_tab"] = self.user_action_allowed(
            group_types=SponsorDetailActionsView.group_type
        )

        return ctx


class SponsorDetailPropertiesView(
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
    template_name = "sponsors/detail_view/detail_view_properties.html"
    model = MvVolunteer

    email = Column(verbose_name="Email address")
    passport_details = Column(verbose_name="Passport number")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_history_tab"] = self.user_action_allowed(
            group_types=SponsorDetailHistoryView.group_type
        )
        context["show_actions_tab"] = self.user_action_allowed(
            group_types=SponsorDetailActionsView.group_type
        )

        return context

    class Meta:
        exclude_fields = [
            "viewer_group_names",
        ]


class SponsorDetailHistoryView(
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
            group_types=SponsorDetailActionsView.group_type
        )
        context["history_description"] = (
            "This history shows the dates a change was made to the sponsor and host "
            "record on the system."
        )
        return context

    template_name = "sponsors/detail_view/detail_view_history.html"
    model = MvVolunteer


class SponsorEditView(
    PIISafeRecordNameMixin, PermissionsMixin, SuccessMessageMixin, UpdateView
):
    model = MvVolunteer
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    form_class = SponsorEditForm
    success_message = "Your changes have been saved"
    template_name = "sponsors/edit_view/edit_view_form_content.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.is_editable:
            return HttpResponse(status=404)
        return super().dispatch(request, *args, **kwargs)

    def _get_object_details_view(self):
        return reverse_lazy("sponsors:detail-overview", kwargs={"pk": self.object.pk})

    def get_success_url(self):
        return self._get_object_details_view()

    def get_cancel_url(self):
        return self._get_object_details_view()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.get_cancel_url()
        return context

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None
