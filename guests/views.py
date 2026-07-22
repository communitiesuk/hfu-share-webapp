import os
from datetime import datetime, timedelta
from typing import Optional

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Fieldset, Layout
from crispy_forms_gds.layout.constants import Size
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.forms.widgets import CheckboxInput, CheckboxSelectMultiple
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.html import escape, format_html
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
    SingleTableView,
    tables,
)

from accounts.enums import GroupType
from deduplication.models import GuestDuplicateGroup
from ontology.models import (
    MvAccommodationRequest,
    MvInteraction,
    MvPerson,
    ReassignmentRequest,
    VisaApplication,
)
from visa_applications.templatetags.visa_application_extras import (
    visa_status_to_tag_colour,
)
from webapp.constants import (
    GUEST_SEARCH_FIELDS,
    visa_status_list,
)
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
    SummaryListLink,
    SummaryListView,
    TwoColumnSummaryListView,
)
from webapp.widgets import CheckboxSelectMultipleWithTags, DatePicker, StackedRangeInput

from .forms import GuestEditAdminForm, GuestEditForm, GuestEditUKVIForm


class GuestsTable(tables.Table):
    full_name = Column(verbose_name="Name")
    gender = Column(verbose_name="Sex")
    date_of_birth = CustomDateColumn(verbose_name="Date of birth")
    passport_id = Column(verbose_name="Passport number")
    visa_status = Column(verbose_name="Visa status")
    arrival_date = Column(verbose_name="First arrival date")
    latest_arrival_date = Column(verbose_name="Latest arrival date")
    visa_application_date_maximum = Column(verbose_name="Latest visa application date")
    application_number = Column(verbose_name="Unique application number (UAN)")

    def render_full_name(self, record: MvPerson, value):
        dup_text = "Duplicate" if not record.is_principal else ""
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{url}">{value}</a>'
            '<div class="govuk-hint govuk-!-font-size-16 govuk-!-margin-top-1'
            ' govuk-!-margin-bottom-0">{dup_text}</div>',
            url=reverse("guests:detail-overview", args=[record.id]),
            value=value,
            dup_text=dup_text,
        )

    def render_passport_id(self, value):
        return value[0] if value else ""

    def render_application_number(self, value):
        return value[0] if value else ""

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
            "passport_id",
            "visa_status",
            "arrival_date",
            "latest_arrival_date",
            "visa_application_date_maximum",
            "application_number",
        )


class GuestsFilter(FilterSet, FilterPanelMixin):
    sex = MultipleChoiceFilter(
        choices=[
            ("Male", "Male"),
            ("Female", "Female"),
        ],
        null_label="No data",
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

    latest_arrival_date = CustomDateFromToRangeFilter(
        label="Latest arrival date",
        field_name="latest_arrival_date",
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

    visa_status = MultipleChoiceFilter(
        choices=[(value.name, value.name) for value in visa_status_list],
        label="Visa status",
        widget=CheckboxSelectMultipleWithTags(
            label_to_tag_colour=visa_status_to_tag_colour
        ),
    )

    include_duplicates = BooleanFilter(
        label="Duplicate guests",
        widget=CheckboxInput(attrs={"value": "Include duplicate records"}),
        method="include_duplicates_filter",
    )

    search = CharFilter(
        label="Search",
        method="search_filter",
        help_text="Search the data in the table",
    )

    def include_duplicates_filter(self, queryset, _, value):
        if not value:
            return queryset.filter(is_principal=True)
        return queryset

    def filter_sex(self, queryset, name, value):
        null_value = self.filters["sex"].null_value
        query = Q(**{f"{name}__in": list(value)}) if value else Q()
        if null_value in value:
            query |= Q(**{f"{name}": "Unspecified"})
            query |= Q(**{f"{name}__isnull": True})
        return queryset.filter(query).distinct()

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, GUEST_SEARCH_FIELDS)

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
                "latest_arrival_date",
                context={
                    "legend_size": "govuk-fieldset__legend--m",
                },
            ),
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
            Fieldset(
                "include_duplicates",
                legend="Duplicate guests",
                legend_size=Size.MEDIUM,
                css_class="govuk-!-margin-top-5",
            ),
        )
        form.fields["include_duplicates"].label = "Include duplicate records"
        return form

    class Meta:
        model = MvPerson
        fields = [
            "search",
            "sex",
            "date_of_birth",
            "visa_status",
            "arrival_date",
            "latest_arrival_date",
            "visa_application_date_maximum",
        ]


class GuestsListView(PermissionsMixin, SingleTableMixin, FilterView):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    model = MvPerson
    table_class = GuestsTable
    filterset_class = GuestsFilter
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    paginator_class = LazyPaginator
    template_name = "guests/guests_list_page.html"

    def get_queryset(self):
        fields_needed = [
            "accommodation_request_id",
            "first_name",
            "last_name",
            "is_principal",
            "gender",
            "date_of_birth",
            "email",
            "passport_id",
            "visa_status",
            "latest_arrival_date",
            "visa_application_date_maximum",
            "application_number",
        ]

        qs = super().get_queryset()
        qs = self.filterset_class(
            self.request.GET,
            queryset=qs,
        ).qs

        return qs.only(*fields_needed).order_by("full_name")


class GuestDetailOverviewView(
    PIISafeRecordNameMixin, PermissionsMixin, IsDuplicateMixin, SummaryListView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.HOME_OFFICE,
        GroupType.MHCLG,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "guests/detail_view/detail_view_overview.html"
    model = MvPerson

    email = Column(verbose_name="Email address")

    def show_upe_visa_status(self):
        user = self.request.user
        return user.is_home_office() or user.is_dev()

    def get_fields(self):
        fields = [
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "email",
            "phone",
            "passport_id",
            "disability_flag",
            "upe_visa_status",
            "visa_status",
            "arrival_date",
            "latest_arrival_date",
            "visa_application_date_maximum",
            "application_number",
            "gwf",
        ]
        if not self.show_upe_visa_status():
            fields = [f for f in fields if f != "upe_visa_status"]
        return fields

    def render_upe_visa_status(self, value, record):
        if value:
            label = getattr(record.UPEVisaStatus(value), "label", None)
            return label if label else value
        return None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.user_can_edit(
            group_types=[
                GroupType.DEV,
                GroupType.LOCAL_AUTHORITY,
                GroupType.DEVOLVED_ADMINISTRATION,
                GroupType.HOME_OFFICE,
            ]
        ):
            ctx["edit_url"] = reverse(
                "guests:detail-edit", kwargs={"pk": self.object.pk}
            )

        ctx["show_history_tab"] = self.user_action_allowed(
            group_types=GuestDetailHistoryView.group_type
        )

        ctx["show_actions_tab"] = self.user_action_allowed(
            group_types=GuestDetailActionsView.group_type
        )

        return ctx


class GuestDetailActionsView(
    PIISafeRecordNameMixin,
    MultiLABannerMixin,
    PermissionsMixin,
    IsDuplicateMixin,
    ActionsListView,
):
    group_type = [GroupType.DEV]
    template_name = "guests/detail_view/detail_view_actions.html"
    model = MvPerson

    def __init__(self, **kwargs):
        self.deduplicated_guests_names = ""
        super().__init__(*kwargs)

    def get_actions(self) -> list[Action]:
        pending_reassignment = (
            ReassignmentRequest.objects.filter(
                guests=self.object,
                outcome=ReassignmentRequest.Outcome.PENDING,
            )
            .order_by("-created_at")
            .first()
        )

        dup_group = (
            GuestDuplicateGroup.objects.filter(principal_record_id=self.object.pk)
            .only("guests", "created_at")
            .first()
        )

        actions: list[Action] = []

        if dup_group:
            deduplicated_guests = dup_group.guests.all()

            deduplicated_guests_names = [
                format_html(
                    '<a class="govuk-link" href="{url}">{value}</a>',
                    url=reverse("guests:detail-overview", args=[guest.id]),
                    value=guest.get_full_name(),
                )
                for guest in deduplicated_guests
            ]

            deduplicated_guests_names = sorted(deduplicated_guests_names)
            if len(deduplicated_guests_names) == 2:
                deduplicated_guests_formatted = (
                    f"{deduplicated_guests_names[0]} and {deduplicated_guests_names[1]}"
                )
            else:
                deduplicated_guests_formatted = f"{
                    ', '.join(deduplicated_guests_names[:-1])
                    and deduplicated_guests_names[-1]
                }"

            further_dup_group: Optional[GuestDuplicateGroup] = (
                GuestDuplicateGroup.objects.filter(guests__pk=self.object.pk)
                .only("principal_record", "created_at")
                .first()
            )

            if self.object.is_principal:
                if pending_reassignment:
                    actions.append(
                        LinkAction(
                            label="Undo deduplication",
                            text=format_html(
                                "You sent a request to move this guest to {}. "
                                "You cannot undo this deduplication while there is a "
                                '<a class="govuk-link" href="{}">{}</a>.',
                                escape(pending_reassignment.destination_ltla_name),
                                reverse(
                                    "reassignment-requests:detail-received",
                                    kwargs={"pk": pending_reassignment.id},
                                ),
                                "pending request to move this guest",
                            ),
                        )
                    )
                elif dup_group.has_blocking_multi_la_accommodation_request(
                    self.object.pk
                ):
                    actions.append(
                        LinkAction(
                            label="Undo deduplication",
                            text="This guest is linked to multiple local authorities "
                            "(LAs) so deduplication cannot be undone.",
                        )
                    )
                elif dup_group.can_undo_deduplication(self.object.pk):
                    actions.append(
                        LinkAction(
                            label="Undo deduplication",
                            url_text="Start",
                            text=f"Delete this record and restore separate records for "
                            f"{deduplicated_guests_formatted}.",
                            url=reverse(
                                "deduplication:guests:undo-deduplication"
                                "-records-manual-step",
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
                                    'guests:detail-actions',
                                    args=[further_dup_group.principal_record.pk],
                                ),
                                further_dup_group.principal_record.get_full_name(),
                            )
                        }"
                        "A full deduplication history is in the history tab.",
                    )
                )
        return actions

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["show_history_tab"] = self.user_action_allowed(
            group_types=GuestDetailHistoryView.group_type
        )

        ctx["show_actions_tab"] = self.user_action_allowed(
            group_types=GuestDetailActionsView.group_type
        )

        return ctx


class GuestDetailLinkedRecordsView(
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
    template_name = "guests/detail_view/detail_view_linked_records.html"
    model = MvPerson

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        linked_records = []
        user = self.request.user
        guest = self.object

        visa_applications = guest.get_visa_applications_restrict_for_user(user)
        if visa_applications.exists():
            view_all_visa_applications_link = SummaryListLink(
                view_name="guests:detail-linked-records-visa-applications",
                object_id=guest.pk,
                title="View the list of all visa applications for this guest",
            )

            linked_records.append(
                (
                    "Visa application",
                    list(visa_applications) + [view_all_visa_applications_link],
                )
            )

        accommodation_request: MvAccommodationRequest = (
            guest.accommodation_request_restrict_for_user(user)
        )
        if accommodation_request:
            linked_records.append(("Accommodation request", accommodation_request))

            sponsors = accommodation_request.get_sponsors_restrict_for_user(user)
            if sponsors.exists():
                linked_records.append(("Sponsors", sponsors))

            active_host = accommodation_request.get_host_restrict_for_user(user)
            if active_host:
                linked_records.append(("Host", active_host))

            accommodations = accommodation_request.get_accommodations_restrict_for_user(
                user
            )
            if accommodations.exists():
                linked_records.append(("Accommodation", accommodations))

        ctx["fields"] = linked_records
        ctx["show_history_tab"] = self.user_action_allowed(
            group_types=GuestDetailHistoryView.group_type
        )
        ctx["show_actions_tab"] = self.user_action_allowed(
            group_types=GuestDetailActionsView.group_type
        )
        return ctx


class GuestDetailPropertiesView(
    PIISafeRecordNameMixin,
    PermissionsMixin,
    IsDuplicateMixin,
    TwoColumnSummaryListView,
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "guests/detail_view/detail_view_properties.html"
    model = MvPerson

    email = Column(verbose_name="Email address")
    upe_visa_status = Column(verbose_name="Ukraine Extension Scheme (UPE) visa status")

    def render_upe_visa_status(self, value, record):
        if value:
            label = getattr(record.UPEVisaStatus(value), "label", None)
            return label if label else value
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_history_tab"] = self.user_action_allowed(
            group_types=GuestDetailHistoryView.group_type
        )
        context["show_actions_tab"] = self.user_action_allowed(
            group_types=GuestDetailActionsView.group_type
        )
        return context

    class Meta:
        exclude_fields = [
            "personmasterrecord",
            "archived_at",
            "is_archived",
        ]


class GuestDetailHistoryView(
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
        # GroupType.LOCAL_AUTHORITY_EARLY_ADOPTERS
        # GroupType.LOCAL_AUTHORITY,
        # GroupType.DEVOLVED_ADMINISTRATION,
    ]
    template_name = "guests/detail_view/detail_view_history.html"
    model = MvPerson
    interaction_restrictions = {
        GroupType.LOCAL_AUTHORITY_EARLY_ADOPTERS: {
            "allowed_contacts": [
                MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
                MvInteraction.InteractionContact.RECORD_DEDUPLICATION_UNDONE,
            ],
            "show_actor_names": False,
        },
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
        GroupType.LOCAL_AUTHORITY_EARLY_ADOPTERS: {"hide_audit_logs": True},
        GroupType.LOCAL_AUTHORITY: {"hide_audit_logs": True},
        GroupType.DEVOLVED_ADMINISTRATION: {"hide_audit_logs": True},
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_history_tab"] = self.user_action_allowed(
            group_types=self.group_type,
        )
        context["show_actions_tab"] = self.user_action_allowed(
            group_types=GuestDetailActionsView.group_type
        )
        context["history_description"] = (
            "This history shows the dates a change was made to the guest record "
            "on the system."
        )
        return context


class GuestEditView(
    PIISafeRecordNameMixin, PermissionsMixin, SuccessMessageMixin, UpdateView
):
    model = MvPerson
    group_type = [
        GroupType.DEV,
        GroupType.HOME_OFFICE,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.SERVICE_SUPPORT,
    ]
    success_message = "Your changes have been saved"
    template_name = "guests/edit_view/edit_view_form_content.html"

    def get_form_class(self):
        if self.request.user.is_home_office():
            return GuestEditUKVIForm
        if self.request.user.is_dev():
            return GuestEditAdminForm
        return GuestEditForm

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def _get_object_details_view(self):
        return reverse_lazy("guests:detail-overview", kwargs={"pk": self.object.pk})

    def get_success_url(self):
        return self._get_object_details_view()

    def get_cancel_url(self):
        return self._get_object_details_view()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.get_cancel_url()
        return context

    def form_valid(self, form):
        form.instance.title = form.instance.first_name + " " + form.instance.last_name
        person = form.save()
        person.update_primary_contact_on_linked_objects()

        return redirect(self.get_success_url())


class RedactedVisaApplicationsTable(tables.Table):
    application_event_datetime = CustomDateTimeColumn(verbose_name="Application date")
    visa_decision_date = CustomDateColumn(verbose_name="Decision date")
    Q44g_full_name = Column(verbose_name="Guest name")
    ltla_name = Column(verbose_name="Local authority")
    Q97c_sponsor_name = Column(verbose_name="Sponsor name")
    gwf = Column(verbose_name="Global Web Form number (GWF)")
    application_unique_application_number = Column(
        verbose_name="Unique Application Number (UAN)"
    )

    def render_visa_status(self, value):
        return render_to_string(
            "webapp/components/visa_status_tag/visa_status_tag.html",
            {"visa_status": value},
        )

    def render_gwf(self, record, value):
        if not record.user_can_view:
            return "Not available"

        return value

    def render_Q97c_sponsor_name(self, record, value):
        if not record.user_can_view:
            return "Not available"
        return value

    def render_application_unique_application_number(self, record, value):
        if not record.user_can_view:
            return "Not available"
        return value

    def render_Q44g_full_name(self, record, value):
        if record.user_can_view:
            return format_html(
                (
                    '<a class="govuk-body-s govuk-link"'
                    'style="white-space: normal" href="{}">'
                    "{}"
                    "</a>"
                ),
                reverse(
                    "visa-applications:detail-overview",
                    args=[record.visa_application_id],
                ),
                value,
            )

        return value

    class Meta:
        model = VisaApplication
        template_name = "webapp/components/tables/table.html"
        fields = (
            "Q44g_full_name",
            "visa_status",
            "application_event_datetime",
            "visa_decision_date",
            "Q97c_sponsor_name",
            "ltla_name",
            "gwf",
            "application_unique_application_number",
        )
        order_by = ("-application_event_datetime",)


class GuestVisaApplicationsListView(PermissionsMixin, SingleTableView):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    model = VisaApplication
    table_class = RedactedVisaApplicationsTable
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    paginator_class = LazyPaginator
    template_name = (
        "guests/detail_view/detail_view_linked_records_visa_application_list.html"
    )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["object"] = get_object_or_404(MvPerson, pk=self.kwargs["pk"])
        return ctx

    def get_queryset(self):
        return get_object_or_404(
            MvPerson.objects.get_for_user(self.request.user), pk=self.kwargs["pk"]
        ).get_visa_applications(user=self.request.user)
