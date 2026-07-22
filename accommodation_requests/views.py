import os
import uuid
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from botocore.exceptions import ClientError
from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Fieldset, Layout
from crispy_forms_gds.layout.constants import Size
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db import DatabaseError, transaction
from django.db.models import OuterRef, Q, Subquery
from django.forms import TextInput, widgets
from django.http import Http404, HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.html import escape, format_html
from django.views.generic import DetailView, FormView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django_filters import (
    BooleanFilter,
    CharFilter,
    FilterSet,
    MultipleChoiceFilter,
    NumberFilter,
)
from django_filters.views import FilterView
from django_tables2 import Column, LazyPaginator, SingleTableMixin, tables
from formtools.wizard.views import NamedUrlSessionWizardView

from accommodation_requests.forms import (
    AccommodationRequestUpdateSafeguardingChecksForm,
    CloseAccommodationRequestForm,
    MoveGuestsConfirmationStep,
    MoveGuestsFormIsStayingInLAStep,
    MoveGuestsFormReasonStep,
    MoveGuestsFormSelectCountryStep,
    MoveGuestsFormSelectGuestsStep,
    MoveGuestsFormSelectLocalAuthorityStep,
    MoveGuestsSelectAccommodationStep,
    ReopenAccommodationRequestForm,
    WithdrawSponsorAccommodationRequestForm,
)
from accommodation_requests.safeguarding_utils import NotificationData, loop_and_raise
from accounts.enums import GroupType
from accounts.mixins import user_has_group_with_type
from case_management import settings
from case_management.settings import FILE_DOWNLOAD_S3_BUCKET_NAME
from ontology.models import (
    Comment,
    CommentAttachment,
    CommentAttachmentMetadata,
    MvAccommodation,
    MvAccommodationRequest,
    MvInteraction,
    MvInteractionAttachmentMetadata,
    MvPerson,
    ReassignmentRequest,
    SafeguardingNotification,
)
from safeguarding.views import get_safeguarding_checks_summary_list_items
from webapp.constants import (
    ACCOMMODATION_REQUEST_SEARCH_FIELDS,
    ACCOMMODATION_SEARCH_FIELDS,
    SELECT_ACCOMMODATION_TABLE_COLUMN_ATTRS,
)
from webapp.enhanced_sentry_logging import db_values, log_event, log_persistence_check
from webapp.mixins import (
    AuditLogTimelineEventsMixin,
    FilterPanelMixin,
    InteractionWithFilesTimelineEventsMixin,
    MultiLABannerMixin,
    PermissionsMixin,
    PIISafeRecordNameMixin,
)
from webapp.s3 import get_presigned_download_url, s3_file_exists
from webapp.search import perform_search
from webapp.templatetags.checks_status_extras import (
    accommodation_checks_status_label_to_tag_colour,
)
from webapp.templatetags.timeline_extras import TimelineEventType
from webapp.utils import CustomDateColumn, CustomDateFromToRangeFilter, LazyChoiceFilter
from webapp.views import (
    Action,
    ActionsListView,
    LinkAction,
    SummaryListView,
    TagAction,
    TwoColumnSummaryListView,
)
from webapp.widgets import (
    CheckboxSelectMultipleWithTags,
    DatePicker,
    SearchableSelect,
    StackedRangeInput,
)

from .enums import MoveGuestsTypes


class RematchGuestsFormSteps(StrEnum):
    GUESTS = "guests"
    SELECT_ACCOMMODATION = "select_accommodation"
    CONFIRMATION = "confirmation"


REMATCH_GUESTS_FORMS = [
    (RematchGuestsFormSteps.GUESTS, MoveGuestsFormSelectGuestsStep),
    (RematchGuestsFormSteps.SELECT_ACCOMMODATION, MoveGuestsSelectAccommodationStep),
    (RematchGuestsFormSteps.CONFIRMATION, MoveGuestsConfirmationStep),
]


def show_select_guests_step(wizard):
    if not wizard.object.person_id:
        return False

    return len(wizard.object.person_id) > 1


MOVE_GUESTS_FORM_CONDITIONAL_DICT = {
    "guests": show_select_guests_step,
}

REMATCH_GUESTS_FORM_TEMPLATES = {
    RematchGuestsFormSteps.GUESTS: "accommodation_requests/move_guests/"
    "accommodation_requests_move_guests_page.html",
    RematchGuestsFormSteps.SELECT_ACCOMMODATION: "accommodation_requests/move_guests/"
    "accommodation_requests_move_guests_select_accommodation_step.html",
    RematchGuestsFormSteps.CONFIRMATION: "accommodation_requests/move_guests/"
    "accommodation_requests_move_guests_page.html",
}


class ReassignGuestsFormSteps(StrEnum):
    GUESTS = "guests"
    COUNTRY = "country"
    LOCAL_AUTHORITY = "local_authority"
    REASON = "reason"
    CONFIRMATION = "confirmation"


REASSIGN_GUESTS_FORMS = [
    (ReassignGuestsFormSteps.GUESTS, MoveGuestsFormSelectGuestsStep),
    (ReassignGuestsFormSteps.COUNTRY, MoveGuestsFormSelectCountryStep),
    (ReassignGuestsFormSteps.LOCAL_AUTHORITY, MoveGuestsFormSelectLocalAuthorityStep),
    (ReassignGuestsFormSteps.REASON, MoveGuestsFormReasonStep),
    (ReassignGuestsFormSteps.CONFIRMATION, MoveGuestsConfirmationStep),
]


def get_url_for_actions_tab(request: MvAccommodationRequest):
    return reverse("accommodation-requests:detail-actions", kwargs={"pk": request.id})


class AccommodationRequestsTable(tables.Table):
    title = Column(verbose_name="Name")
    checks_status = Column(verbose_name="Status")
    latest_application_date = CustomDateColumn(verbose_name="Date of application")
    number_of_people = Column(verbose_name="Number of people")
    ltla_name = Column(verbose_name="Lower tier LA")
    utla_name = Column(verbose_name="Upper tier LA")

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

    def render_ltla_name(self, value):
        return self.format_array_as_string(value)

    def render_utla_name(self, value):
        return self.format_array_as_string(value)

    class Meta:
        model = MvAccommodationRequest
        template_name = "webapp/components/tables/table.html"
        fields = (
            "title",
            "checks_status",
            "latest_application_date",  # or maybe we want created_at instead
            "number_of_people",
            "ltla_name",
            "utla_name",
        )
        order_by = "-latest_application_date"


class AccommodationRequestsFilter(FilterSet, FilterPanelMixin):
    status = MultipleChoiceFilter(
        choices=MvAccommodationRequest.ChecksStatus.choices,
        label="Status",
        field_name="checks_status",
        widget=CheckboxSelectMultipleWithTags(
            label_to_tag_colour=accommodation_checks_status_label_to_tag_colour
        ),
    )

    date_of_application = CustomDateFromToRangeFilter(
        label="Date of application",
        field_name="latest_application_date",
        widget=StackedRangeInput(
            sub_widget=DatePicker,
            attrs={
                "from_hint": f"For example "
                f"{(datetime.today() - timedelta(days=20)).strftime('%d/%m/%Y')}",
                "to_hint": f"For example "
                f"{(datetime.today() + timedelta(days=600)).strftime('%d/%m/%Y')}",
                "from_label": "Date from",
                "to_label": "Date to",
            },
        ),
        distinct=True,
        error_messages={
            "invalid_range": "'Date from' must be before 'Date to'.",
        },
    )

    number_of_people = NumberFilter(
        label="Number of people",
        field_name="number_of_people",
        widget=TextInput(attrs={"type": "number"}),
        min_value=0,
    )

    ltla_name = LazyChoiceFilter(
        choices=lambda: [
            (ltla, ltla)
            for ltla in MvAccommodationRequest.objects.get_queryset().ltla_names()
        ],
        label="Lower tier local authority (LTLA)",
        empty_label="",
        lookup_expr="icontains",
        widget=SearchableSelect(),
    )

    utla_name = LazyChoiceFilter(
        choices=lambda: [
            (utla, utla)
            for utla in MvAccommodationRequest.objects.get_queryset().utla_names()
        ],
        label="Upper tier local authority (UTLA)",
        empty_label="",
        lookup_expr="icontains",
        widget=SearchableSelect(),
    )

    search = CharFilter(
        label="Search",
        method="search_filter",
        help_text="Search the data in the table",
    )

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, ACCOMMODATION_REQUEST_SEARCH_FIELDS)

    @property
    def qs(self):
        parent_qs = super().qs

        if hasattr(self.data, "getlist"):
            status_requested = self.data.getlist("status")
        else:
            status_requested = self.data.get("status", [])

        if MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY not in status_requested:
            parent_qs = parent_qs.exclude(
                Q(person_id__len=0)
                | Q(person_id__isnull=True)
                | Q(checks_status=MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY)
            )

        return parent_qs

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
            Field(
                "date_of_application",
                context={
                    "legend_size": "govuk-fieldset__legend--m",
                },
            ),
            Field("status", context={"label_size": "govuk-fieldset__legend--m"}),
            Field.text("number_of_people", label_size=Size.MEDIUM),
            Field.text("ltla_name", small=True, label_size=Size.MEDIUM),
            Field.text("utla_name", small=True, label_size=Size.MEDIUM),
        )
        return form

    class Meta:
        model = MvAccommodationRequest
        fields = [
            "search",
            "date_of_application",
            "status",
            "number_of_people",
            "ltla_name",
            "utla_name",
        ]


class AccommodationRequestsListView(PermissionsMixin, SingleTableMixin, FilterView):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    model = MvAccommodationRequest
    table_class = AccommodationRequestsTable
    filterset_class = AccommodationRequestsFilter
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    paginator_class = LazyPaginator
    template_name = "accommodation_requests/accommodation_requests_list_page.html"

    def get_queryset(self):
        fields_needed = [
            "title",
            "checks_status",
            "latest_application_date",
            "number_of_people",
            "ltla_name",
            "utla_name",
            "person_id",
        ]
        return super().get_queryset().only(*fields_needed)


class AccommodationRequestDetailOverviewView(
    PIISafeRecordNameMixin, MultiLABannerMixin, PermissionsMixin, SummaryListView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "accommodation_requests/detail_view/detail_view_overview.html"
    model = MvAccommodationRequest

    def get_context_data(self, **kwargs):
        self.add_multi_la_message()
        context = super().get_context_data(**kwargs)
        user = self.request.user
        ar = self.object

        context["show_actions_tab"] = self.user_can_edit(
            group_types=AccommodationRequestDetailActionsView.group_type
        )
        context["show_history_tab"] = self.user_action_allowed(
            group_types=AccommodationRequestDetailHistoryView.group_type
        )

        if (
            not ar.get_sponsors_restrict_for_user(user).exists()
            and ar.has_any_active_sponsors()
        ):
            sponsors = format_html(
                (
                    '<strong class="govuk-tag {tag_colour_class}" '
                    'style="display:inline">'
                    "{tag_text}"
                    "</strong>"
                ),
                tag_colour_class="govuk-tag--red",
                tag_text="Sponsor is not in your LA",
            )
        else:
            sponsors = [
                (
                    f"{sponsor.get_full_name()} (Withdrawn)"
                    if sponsor.id in (ar.sponsor_withdrawn or [])
                    else sponsor.get_full_name()
                )
                for sponsor in ar.get_sponsors_restrict_for_user(user)
            ]

        context["fields"] = [
            (
                "Status",
                render_to_string(
                    "webapp/components/checks_status_tag/"
                    "accommodation_checks_status_tag.html",
                    {"accommodation_checks_status": ar.checks_status},
                ),
            ),
            (
                "Host",
                (host := ar.get_host_restrict_for_user(user)) and host.get_full_name(),
            ),
            (
                (
                    "Sponsors"
                    if len(ar.get_sponsors_restrict_for_user(user)) > 1
                    else "Sponsor"
                ),
                sponsors,
            ),
            (
                "Lower tier Local Authority",
                ar.get_all_ltla_names(),
            ),
            (
                "Upper tier Local Authority",
                ar.get_all_utla_names(),
            ),
            (
                "Guests",
                [
                    person.get_full_name()
                    for person in ar.get_people_restrict_for_user(user)
                ],
            ),
            (
                "Address",
                [
                    accommodation.full_address
                    for accommodation in ar.get_accommodations_restrict_for_user(user)
                ],
            ),
        ]
        return context


class AccommodationRequestDetailActionsView(
    PIISafeRecordNameMixin, MultiLABannerMixin, PermissionsMixin, ActionsListView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "accommodation_requests/detail_view/detail_view_actions.html"
    model = MvAccommodationRequest

    def get_actions(self) -> list[Action]:
        actions: list[Action] = []
        user = self.request.user

        # Soft lock AR if there are any pending reassignment requests
        if self.object.reassignment_requests.filter(
            outcome=ReassignmentRequest.Outcome.PENDING
        ).exists():
            return []

        can_move_guests = self.user_can_edit(
            group_types=[
                GroupType.DEV,
                GroupType.MHCLG,
                GroupType.LOCAL_AUTHORITY,
                GroupType.DEVOLVED_ADMINISTRATION,
            ]
        )
        can_close_ar = self.user_can_edit(
            group_types=[
                GroupType.DEV,
                GroupType.LOCAL_AUTHORITY,
                GroupType.DEVOLVED_ADMINISTRATION,
            ]
        )
        can_reopen_ar = self.user_can_edit(
            group_types=[
                GroupType.DEV,
                GroupType.LOCAL_AUTHORITY,
                GroupType.DEVOLVED_ADMINISTRATION,
            ]
        )
        can_withdraw_sponsor = self.user_can_edit(
            group_types=[
                GroupType.DEV,
                GroupType.LOCAL_AUTHORITY,
                GroupType.DEVOLVED_ADMINISTRATION,
            ]
        )

        # Move guests (rematch or reassign)
        if can_move_guests and self.object.checks_status not in [
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
            MvAccommodationRequest.ChecksStatus.CANCELLED,
            MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE,
        ]:
            guests = self.object.get_people_restrict_for_user(user)
            if not guests.exists():
                actions.append(
                    TagAction(
                        label="Move guests (rematch or reassign)",
                        tag_text="All guests moved",
                        tag_colour_class="govuk-tag--red",
                    )
                )
            else:
                actions.append(
                    LinkAction(
                        label="Move guests (rematch or reassign)",
                        url_text="Start",
                        url=reverse(
                            "accommodation-requests:move-guests",
                            kwargs={"pk": self.object.id},
                        )
                        + "?reset",
                    )
                )

        # Reopen accommodation request for guests
        if can_reopen_ar and self.object.checks_status in [
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
            MvAccommodationRequest.ChecksStatus.CANCELLED,
        ]:
            actions.append(
                LinkAction(
                    label="Reopen accommodation request for guests",
                    url_text="Start",
                    url=reverse(
                        "accommodation-requests:reopen",
                        kwargs={"pk": self.object.id},
                    ),
                )
            )
        # Close accommodation request
        elif can_close_ar and self.object.checks_status not in [
            MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY,
            MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE,
        ]:
            actions.append(
                LinkAction(
                    label="Close accommodation request",
                    url_text="Start",
                    url=reverse(
                        "accommodation-requests:close-for-guests",
                        kwargs={"pk": self.object.id},
                    ),
                )
            )

        # Withdraw sponsor
        if can_withdraw_sponsor:
            if self.object.get_active_sponsors_restrict_for_user(user).exists():
                actions.append(
                    LinkAction(
                        label="Withdraw sponsor",
                        url_text="Start",
                        url=reverse(
                            "accommodation-requests:withdraw-sponsor",
                            kwargs={"pk": self.object.id},
                        ),
                    )
                )
            elif self.object.has_any_active_sponsors():
                actions.append(
                    TagAction(
                        label="Withdraw sponsor",
                        tag_text="Sponsor is not in your LA",
                        tag_colour_class="govuk-tag--red",
                    )
                )
            else:
                actions.append(
                    TagAction(
                        label="Withdraw sponsor",
                        tag_text="All sponsors withdrawn",
                        tag_colour_class="govuk-tag--red",
                    )
                )

        return actions

    def get_context_data(self, **kwargs):
        self.add_multi_la_message()
        ctx = super().get_context_data(**kwargs)
        pending_reassignment = self.object.reassignment_requests.filter(
            outcome=ReassignmentRequest.Outcome.PENDING
        ).first()
        if pending_reassignment:
            guest_names = ", ".join(
                [escape(g.get_full_name()) for g in pending_reassignment.guests.all()]
            )
            destination = escape(pending_reassignment.destination_ltla_name)
            reassignments_link = format_html(
                '<a class="govuk-link govuk-link" href="{}">{}</a>',
                reverse(
                    "reassignment-requests:detail-received",
                    kwargs={"pk": pending_reassignment.id},
                ),
                "pending request to move guests",
            )
            reassignment_message = format_html(
                "You sent a request to move {} to {}.<br><br>"
                "You cannot take any actions on this accommodation request "
                "while there is a {}.",
                guest_names,
                destination,
                reassignments_link,
            )
            messages.info(
                self.request,
                reassignment_message,
                extra_tags="html_safe content_full_width",
            )
        ctx["show_actions_tab"] = self.user_can_edit(group_types=self.group_type)
        ctx["show_history_tab"] = self.user_action_allowed(
            group_types=AccommodationRequestDetailHistoryView.group_type
        )
        return ctx


class AccommodationRequestDetailLinkedRecordsView(
    PIISafeRecordNameMixin, MultiLABannerMixin, PermissionsMixin, DetailView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "accommodation_requests/detail_view/detail_view_linked_records.html"
    model = MvAccommodationRequest

    def get_context_data(self, **kwargs):
        self.add_multi_la_message()
        ctx = super().get_context_data(**kwargs)
        ctx["show_actions_tab"] = self.user_can_edit(
            group_types=AccommodationRequestDetailActionsView.group_type
        )
        ctx["show_history_tab"] = self.user_action_allowed(
            group_types=AccommodationRequestDetailHistoryView.group_type
        )

        linked_records = []
        user = self.request.user
        ar = self.object

        accommodations = ar.get_accommodations_restrict_for_user(user)
        if accommodations.exists():
            linked_records.append(("Accommodation", accommodations))

        guests = ar.get_people_restrict_for_user(user)
        if guests.exists():
            linked_records.append(("Guests", guests))

        sponsors = ar.get_sponsors_restrict_for_user(user)
        if sponsors.exists():
            linked_records.append(("Sponsors", sponsors))

        active_host = ar.get_host_restrict_for_user(user)
        if active_host:
            linked_records.append(("Host", active_host))

        visa_applications = ar.get_visa_applications_restrict_for_user(user)
        if visa_applications.exists():
            linked_records.append(("Visa applications", visa_applications))

        sponsorship_certification_number = (
            ar.get_sponsorship_certification_forms_restrict_for_user(user)
        )

        if sponsorship_certification_number.exists():
            linked_records.append(
                (
                    "Sponsorship certification number",
                    sponsorship_certification_number,
                )
            )

        ctx["fields"] = linked_records
        return ctx


class AccommodationRequestDetailSafeguardingChecksView(
    PIISafeRecordNameMixin, MultiLABannerMixin, PermissionsMixin, SummaryListView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = (
        "accommodation_requests/detail_view/detail_view_safeguarding_checks.html"
    )
    model = MvAccommodationRequest

    def get_context_data(self, **kwargs):
        self.add_multi_la_message()
        ctx = super().get_context_data(**kwargs)
        ctx["user_can_add_update"] = self.user_can_edit(
            group_types=[
                GroupType.DEV,
                GroupType.LOCAL_AUTHORITY,
                GroupType.DEVOLVED_ADMINISTRATION,
                GroupType.MHCLG,
            ]
        )
        ctx["show_actions_tab"] = self.user_can_edit(
            group_types=AccommodationRequestDetailActionsView.group_type
        )
        ctx["show_history_tab"] = self.user_action_allowed(
            group_types=AccommodationRequestDetailHistoryView.group_type
        )
        ctx["fields"] = get_safeguarding_checks_summary_list_items(
            self.object,
            self.request.user,
            user_can_add_update=ctx["user_can_add_update"],
        )
        return ctx


class AccommodationRequestDetailPropertiesView(
    PIISafeRecordNameMixin,
    MultiLABannerMixin,
    PermissionsMixin,
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
    template_name = "accommodation_requests/detail_view/detail_view_properties.html"
    model = MvAccommodationRequest

    def get_context_data(self, **kwargs):
        self.add_multi_la_message()
        ctx = super().get_context_data(**kwargs)
        ctx["show_actions_tab"] = self.user_can_edit(
            group_types=AccommodationRequestDetailActionsView.group_type
        )
        ctx["show_history_tab"] = self.user_action_allowed(
            group_types=AccommodationRequestDetailHistoryView.group_type
        )
        return ctx

    class Meta:
        exclude_fields = ["requires_checks_status_recalculation"]


class AccommodationRequestDetailHistoryView(
    PIISafeRecordNameMixin,
    MultiLABannerMixin,
    PermissionsMixin,
    InteractionWithFilesTimelineEventsMixin,
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
    template_name = "accommodation_requests/detail_view/detail_view_history.html"
    model = MvAccommodationRequest

    def _show_events(self):
        user = self.request.user
        if user_has_group_with_type(
            user, GroupType.LOCAL_AUTHORITY
        ) or user_has_group_with_type(user, GroupType.DEVOLVED_ADMINISTRATION):
            if not settings.LA_HISTORY_TAB_ENABLED:
                return False

            ltlas = self.object.get_all_ltla_names()
            if ltlas and len(ltlas) > 1:
                return False

        return super()._show_events()

    def _get_timeline_start(self):
        user = self.request.user
        if user_has_group_with_type(
            user, GroupType.LOCAL_AUTHORITY
        ) or user_has_group_with_type(user, GroupType.DEVOLVED_ADMINISTRATION):
            interaction = (
                MvInteraction.objects.filter(
                    linked_accommodation_request=self.object,
                    interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
                )
                .order_by("-created_at")
                .first()
            )
            if interaction:
                return interaction.created_at
        return super()._get_timeline_start()

    def get_context_data(self, **kwargs):
        self.add_multi_la_message()
        ctx = super().get_context_data(**kwargs)
        ctx["show_actions_tab"] = self.user_can_edit(
            group_types=AccommodationRequestDetailActionsView.group_type
        )
        ctx["show_history_tab"] = self.user_action_allowed(
            group_types=self.group_type,
        )
        ctx["history_description"] = (
            "This history shows the dates a change was made to the accommodation "
            "request record on the system."
        )
        return ctx


class AccommodationRequestCloseForGuests(
    PIISafeRecordNameMixin, PermissionsMixin, SingleObjectMixin, FormView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
    ]
    template_name = (
        "accommodation_requests/accommodation_requests_close_for_guests_page.html"
    )
    model = MvAccommodationRequest
    form_class = CloseAccommodationRequestForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["accommodation_request"] = self.get_object()
        return kwargs

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.checks_status in [
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
            MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY,
            MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE,
            MvAccommodationRequest.ChecksStatus.CANCELLED,
        ]:
            return HttpResponse(status=409)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return get_url_for_actions_tab(self.get_object())

    def get_cancel_url(self):
        return get_url_for_actions_tab(self.get_object())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.get_cancel_url()
        return context

    def form_valid(self, form):
        accommodation_request = self.get_object()
        selected_guests = form.cleaned_data["guests"]
        reason = form.cleaned_data["reason"]
        comment = form.cleaned_data["comment"]

        if selected_guests and accommodation_request.number_of_people != len(
            selected_guests
        ):
            accommodation_request = accommodation_request.split_guests(selected_guests)

        accommodation_request.update_checks_status(
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
            author=self.request.user,
        )

        MvInteraction.create_interaction(
            interaction_contact=MvInteraction.InteractionContact.LEAVING_PROGRAMME,
            interaction_type=reason,
            linked_accommodation_request=accommodation_request,
            interaction_notes=reason + ": " + comment if comment else reason,
            created_by=self.request.user,
            title=MvInteraction.InteractionContact.LEAVING_PROGRAMME,
        )

        all_guests = accommodation_request.get_people_restrict_for_user(
            self.request.user
        )
        guests = all_guests[0].get_full_name() if len(all_guests) > 0 else ""

        if len(all_guests) > 1:
            others = len(all_guests) - 1
            guests += f" and {others} other{'s' if others > 1 else ''}"

        primary_accommodation = accommodation_request.get_primary_accommodation()
        full_address = (
            primary_accommodation.full_address
            if (primary_accommodation and primary_accommodation.full_address)
            else None
        )

        if full_address:
            message = (
                f"{guests} moved out of {full_address}. Accommodation request closed."
            )
        else:
            message = "You closed this accommodation request."

        messages.success(self.request, message)
        return super().form_valid(form)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None


class AccommodationRequestReopenRequestView(
    PIISafeRecordNameMixin, PermissionsMixin, SingleObjectMixin, FormView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = (
        "accommodation_requests/accommodation_requests_reopen_request_page.html"
    )
    model = MvAccommodationRequest
    form_class = ReopenAccommodationRequestForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.checks_status not in [
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
            MvAccommodationRequest.ChecksStatus.CANCELLED,
        ]:
            return HttpResponse(status=409)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return get_url_for_actions_tab(self.get_object())

    def get_cancel_url(self):
        return get_url_for_actions_tab(self.get_object())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.get_cancel_url()
        return context

    def form_valid(self, form):
        accommodation_request = self.get_object()

        if (
            accommodation_request.checks_status
            == MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME
        ):
            MvInteraction.create_interaction(
                interaction_contact=(
                    MvInteraction.InteractionContact.RETURNED_TO_PROGRAMME
                ),
                interaction_type=(
                    MvInteraction.InteractionContact.RETURNED_TO_PROGRAMME
                ),
                linked_accommodation_request=accommodation_request,
                created_by=self.request.user,
                title=MvInteraction.InteractionContact.RETURNED_TO_PROGRAMME,
            )

        accommodation_request.reset_and_redetermine_status(
            author=self.request.user.username
        )

        messages.success(
            self.request,
            "Accommodation request reopened.",
        )
        return super().form_valid(form)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None


class AccommodationRequestUpdateSafeguardingChecksView(
    PIISafeRecordNameMixin,
    PermissionsMixin,
    SuccessMessageMixin,
    UpdateView,
    SummaryListView,
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = (
        "accommodation_requests/"
        "add_update_safeguarding_checks/"
        "add_update_safeguarding_checks_page.html"
    )
    model = MvAccommodationRequest
    form_class = AccommodationRequestUpdateSafeguardingChecksForm
    success_message = "Your changes have been saved"

    def _get_object_details_view(self):
        return reverse_lazy(
            "accommodation-requests:detail-safeguarding-checks",
            kwargs={"pk": self.object.pk},
        )

    def get_success_url(self):
        if "submit_and_stay" in self.request.POST:
            return self.request.path
        return self._get_object_details_view()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["dev_check_v2_id"] = self.request.GET.get("dev_check_v2_id")
        kwargs["user"] = self.request.user
        return kwargs

    def get_cancel_url(self):
        return self._get_object_details_view()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fields"] = get_safeguarding_checks_summary_list_items(
            self.object, self.request.user
        )
        context["cancel_url"] = self.get_cancel_url()
        return context


class AccommodationRequestWithdrawSponsorView(
    PIISafeRecordNameMixin, PermissionsMixin, SingleObjectMixin, FormView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
    ]
    template_name = (
        "accommodation_requests/accommodation_requests_withdraw_sponsor_page.html"
    )
    model = MvAccommodationRequest
    form_class = WithdrawSponsorAccommodationRequestForm

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if not self.object.get_active_sponsors_restrict_for_user(
            self.request.user
        ).exists():
            return HttpResponse(status=409)

        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return get_url_for_actions_tab(self.get_object())

    def get_cancel_url(self):
        return get_url_for_actions_tab(self.get_object())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.get_cancel_url()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["sponsors_queryset"] = (
            self.get_object()
            .get_active_sponsors_restrict_for_user(self.request.user)
            .order_by("full_name")
        )
        return kwargs

    def form_valid(self, form):
        accommodation_request = self.get_object()
        reason = form.cleaned_data["reason"]
        sponsors = (
            form.cleaned_data["sponsors"]
            if "sponsors" in form.cleaned_data
            else accommodation_request.get_active_sponsors_restrict_for_user(
                self.request.user
            )
        )

        for sponsor in sponsors:
            accommodation_request.mark_sponsor_withdrawn(
                sponsor, author=self.request.user
            )
            notification_data = NotificationData(
                alert_type=SafeguardingNotification.AlertType.SPONSOR_WITHDRAWN,
                check=None,
                sponsor=sponsor,
                accommodation=None,
                description=reason,
                title="Withdrawn sponsor",
            )
            loop_and_raise(accommodation_request, notification_data)

        MvInteraction.create_interaction(
            interaction_contact=MvInteraction.InteractionContact.WITHDRAWN_SPONSOR,
            interaction_type=MvInteraction.InteractionContact.WITHDRAWN_SPONSOR,
            linked_accommodation_request=accommodation_request,
            interaction_notes=(
                f"Withdrawn sponsors: "
                f"{list(sponsors.values_list('full_name', flat=True))} "
                f"Reason: {reason}"
            ),
            created_by=self.request.user,
            title=MvInteraction.InteractionContact.WITHDRAWN_SPONSOR,
        )

        messages.success(
            self.request,
            "Sponsor withdrawn.",
        )
        return super().form_valid(form)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None


class RematchGuestsFormWizard(
    PIISafeRecordNameMixin,
    PermissionsMixin,
    SingleObjectMixin,
    NamedUrlSessionWizardView,
):
    model = MvAccommodationRequest
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.select_accommodation_step_view = RematchSelectAccommodationFormStepView()
        self.object = None

    def get_step_url(self, step):
        return reverse(self.url_name, kwargs={"step": step, "pk": self.object.pk})

    def dispatch(self, *args, **kwargs):
        self.object: MvAccommodationRequest = self.get_object()

        if self.object.ltla_name:
            self.select_accommodation_step_view.ltla = self.object.ltla_name

        return super().dispatch(*args, **kwargs)

    def get_prefix(self, request, *args, **kwargs):
        return f"rematch_guests_form_wizard_{self.get_object().pk}"

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == RematchGuestsFormSteps.GUESTS:
            kwargs["move_type"] = MoveGuestsTypes.REMATCH
            kwargs["guests_queryset"] = self.object.get_people_restrict_for_user(
                self.request.user
            )

        if step == RematchGuestsFormSteps.CONFIRMATION:
            kwargs["move_type"] = MoveGuestsTypes.REMATCH
            has_guests_step = "guests" in self.get_form_list().keys()
            if not has_guests_step:
                # Means AR has only one guest and skipped the guests step
                kwargs["guests_to_move"] = self.object.get_people_restrict_for_user(
                    self.request.user
                )
            else:
                guests_to_move_data = self.get_cleaned_data_for_step("guests") or {}
                kwargs["guests_to_move"] = guests_to_move_data.get(
                    "guests"
                ) or self.object.get_people_restrict_for_user(self.request.user)

            accommodation_data = (
                self.get_cleaned_data_for_step("select_accommodation") or {}
            )
            kwargs["accommodation"] = accommodation_data.get("accommodation")

        return kwargs

    def get(self, *args, **kwargs):
        if not self.object.get_people_restrict_for_user(self.request.user).exists():
            return HttpResponse(status=409)

        if self.object.checks_status in [
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
            MvAccommodationRequest.ChecksStatus.CANCELLED,
            MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY,
            MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE,
        ]:
            return HttpResponse(status=409)

        return super().get(*args, **kwargs)

    def get_template_names(self):
        return REMATCH_GUESTS_FORM_TEMPLATES[self.steps.current]

    def get_context_data(self, form=None, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        context["object"] = self.get_object()
        context["cancel_url"] = self.get_cancel_url()

        if self.steps.current == RematchGuestsFormSteps.SELECT_ACCOMMODATION:
            self.select_accommodation_step_view.request = self.request
            context |= self.select_accommodation_step_view.get_context_data()
        return context

    def get_cancel_url(self):
        return get_url_for_actions_tab(self.get_object())

    def done(self, form_list, **kwargs):
        data = self.get_all_cleaned_data()
        ar = self.object

        guests_to_move = data.get("guests") or ar.get_people_restrict_for_user(
            self.request.user
        )
        accommodation = data.get("accommodation")

        guest_ids = [str(guest.id) for guest in guests_to_move]

        log_event(
            "rematch_guests: started",
            ar_pk=ar.pk,
            guest_pks=guest_ids,
            accommodation_pk=accommodation.pk,
            user_pk=self.request.user.pk,
        )

        try:
            with transaction.atomic():
                if ar.number_of_people != len(guests_to_move):
                    pre_split_ar = ar
                    pre_split_person_id = list(pre_split_ar.person_id or [])
                    ar = ar.split_guests(guest_ids)
                    log_event(
                        "rematch_guests: guests split to new AR",
                        original_ar_pk=pre_split_ar.pk,
                        new_ar_pk=ar.pk,
                        guest_pks=guest_ids,
                    )
                    persisted_pre_split = db_values(
                        pre_split_ar, "person_id", "edited_in_app"
                    )
                    log_persistence_check(
                        "rematch_guests: original AR guests after split",
                        original_ar_pk=pre_split_ar.pk,
                        before={"person_id": pre_split_person_id},
                        changes={
                            "person_id": (
                                pre_split_ar.person_id,
                                persisted_pre_split.get("person_id"),
                            ),
                            "edited_in_app": (
                                pre_split_ar.edited_in_app,
                                persisted_pre_split.get("edited_in_app"),
                            ),
                        },
                    )
                    persisted_new_split = db_values(ar, "person_id", "edited_in_app")
                    log_persistence_check(
                        "rematch_guests: new AR guests after split",
                        new_ar_pk=ar.pk,
                        changes={
                            "person_id": (
                                ar.person_id,
                                persisted_new_split.get("person_id"),
                            ),
                            "edited_in_app": (
                                ar.edited_in_app,
                                persisted_new_split.get("edited_in_app"),
                            ),
                        },
                    )

                # Update AR accommodations
                ar.update_accommodation(accommodation, author=self.request.user)
                persisted_accommodation = db_values(
                    ar,
                    "accommodation_id",
                    "primary_accommodation_id",
                    "postcode",
                    "edited_in_app",
                )
                log_persistence_check(
                    "rematch_guests: accommodation updated",
                    ar_pk=ar.pk,
                    accommodation_pk=accommodation.pk,
                    changes={
                        "accommodation_id": (
                            ar.accommodation_id,
                            persisted_accommodation.get("accommodation_id"),
                        ),
                        "primary_accommodation_id": (
                            ar.primary_accommodation_id,
                            persisted_accommodation.get("primary_accommodation_id"),
                        ),
                        "postcode": (
                            ar.postcode,
                            persisted_accommodation.get("postcode"),
                        ),
                        "edited_in_app": (
                            ar.edited_in_app,
                            persisted_accommodation.get("edited_in_app"),
                        ),
                    },
                )

                guest_ar_links = list(
                    MvPerson.objects.filter(id__in=guest_ids).values(
                        "id", "accommodation_request_id"
                    )
                )
                log_event(
                    "rematch_guests: guest AR links",
                    ar_pk=ar.pk,
                    guest_ar_links=guest_ar_links,
                )

                # Remove old host
                if ar.get_active_host() or ar.get_active_eoi_host():
                    ar.unlink_host(author=self.request.user)
                    persisted_host = db_values(ar, "active_host_id", "edited_in_app")
                    log_persistence_check(
                        "rematch_guests: host unlinked",
                        ar_pk=ar.pk,
                        changes={
                            "active_host_id": (
                                ar.active_host_id,
                                persisted_host.get("active_host_id"),
                            ),
                            "edited_in_app": (
                                ar.edited_in_app,
                                persisted_host.get("edited_in_app"),
                            ),
                        },
                    )

                # Add new AR host
                ar.update_host(accommodation, author=self.request.user)
                persisted_new_host = db_values(ar, "active_host_id", "edited_in_app")
                log_persistence_check(
                    "rematch_guests: host updated",
                    ar_pk=ar.pk,
                    accommodation_pk=accommodation.pk,
                    changes={
                        "active_host_id": (
                            ar.active_host_id,
                            persisted_new_host.get("active_host_id"),
                        ),
                        "edited_in_app": (
                            ar.edited_in_app,
                            persisted_new_host.get("edited_in_app"),
                        ),
                    },
                )

                # Create interaction for rematch
                rematch_interaction = MvInteraction.create_interaction(
                    interaction_contact=MvInteraction.InteractionContact.REMATCH_RECORDED,
                    interaction_type=MvInteraction.InteractionContact.REMATCH_RECORDED,
                    linked_accommodation_request=ar,
                    created_by=self.request.user,
                    title=MvInteraction.InteractionContact.REMATCH_RECORDED,
                )
                log_event(
                    "rematch_guests: interaction created",
                    ar_pk=ar.pk,
                    interaction_pk=rematch_interaction.pk,
                    interaction_type=rematch_interaction.interaction_type,
                )

                new_checks_status = ar.determine_checks_status_from_linked_objects()
                ar.update_checks_status(
                    new_checks_status,
                    author=self.request.user,
                )
                persisted_status = db_values(ar, "checks_status", "edited_in_app")
                log_persistence_check(
                    "rematch_guests: checks status updated",
                    ar_pk=ar.pk,
                    changes={
                        "checks_status": (
                            ar.checks_status,
                            persisted_status.get("checks_status"),
                        ),
                        "edited_in_app": (
                            ar.edited_in_app,
                            persisted_status.get("edited_in_app"),
                        ),
                    },
                )
        except DatabaseError:
            if len(guests_to_move) == 1:
                not_moved_partial = "The guest was not moved."
            else:
                not_moved_partial = "The guests were not moved."
            messages.error(
                self.request,
                f"{not_moved_partial} If the problem continues raise a support ticket.",
            )
            return redirect(self.get_cancel_url())

        if len(guests_to_move) == 1:
            success_message = f"{guests_to_move[0].get_full_name()} has been moved."
        else:
            names_list = [guests.get_full_name() for guests in guests_to_move]
            names = ", ".join(names_list[:-1]) + f" and {names_list[-1]}"
            success_message = f"{names} have been moved."

        messages.success(self.request, success_message)

        return redirect(
            "accommodation-requests:detail-actions", pk=self.kwargs.get("pk")
        )


class ReassignGuestsFormWizard(
    PIISafeRecordNameMixin,
    PermissionsMixin,
    SingleObjectMixin,
    NamedUrlSessionWizardView,
):
    model = MvAccommodationRequest
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
    ]
    template_name = (
        "accommodation_requests/"
        "move_guests/"
        "accommodation_requests_move_guests_page.html"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_step_url(self, step):
        return reverse(self.url_name, kwargs={"step": step, "pk": self.object.pk})

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)

        if step == ReassignGuestsFormSteps.GUESTS:
            kwargs["move_type"] = MoveGuestsTypes.REASSIGN
            kwargs["guests_queryset"] = self.object.get_people_restrict_for_user(
                self.request.user
            )

        if step == ReassignGuestsFormSteps.CONFIRMATION:
            kwargs["move_type"] = MoveGuestsTypes.REASSIGN
            has_guests_step = "guests" in self.get_form_list().keys()
            if not has_guests_step:
                kwargs["guests_to_move"] = self.object.get_people_restrict_for_user(
                    self.request.user
                )
            else:
                guests_to_move_data = self.get_cleaned_data_for_step("guests") or {}
                kwargs["guests_to_move"] = guests_to_move_data.get(
                    "guests"
                ) or self.object.get_people_restrict_for_user(self.request.user)

            country_data = self.get_cleaned_data_for_step("country") or {}
            kwargs["country"] = country_data.get("country")
            if "local_authority" in self.get_form_list().keys():
                local_authority_data = (
                    self.get_cleaned_data_for_step("local_authority") or {}
                )
                if local_authority_data.get("local_authority"):
                    kwargs["local_authority"] = local_authority_data.get(
                        "local_authority"
                    ).ltla_name

        if step == ReassignGuestsFormSteps.COUNTRY:
            kwargs["number_of_people"] = (
                len(self.object.person_id) if self.object.person_id else 0
            )

        if step == ReassignGuestsFormSteps.LOCAL_AUTHORITY:
            country_data = self.get_cleaned_data_for_step("country") or {}
            kwargs["country"] = country_data.get("country")

        if step in [
            ReassignGuestsFormSteps.COUNTRY,
            ReassignGuestsFormSteps.LOCAL_AUTHORITY,
            ReassignGuestsFormSteps.REASON,
        ]:
            kwargs["number_of_people"] = (
                len(self.object.person_id) if self.object.person_id else 0
            )

        return kwargs

    def get(self, *args, **kwargs):
        if not self.object.get_people_restrict_for_user(self.request.user).exists():
            return HttpResponse(status=409)

        if self.object.checks_status in [
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
            MvAccommodationRequest.ChecksStatus.CANCELLED,
            MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY,
            MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE,
        ]:
            return HttpResponse(status=409)

        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object()
        context["cancel_url"] = self.get_cancel_url()
        return context

    def get_prefix(self, request, *args, **kwargs):
        return f"reassign_guests_form_wizard_{self.get_object().pk}"

    def done(self, form_list, **kwargs):
        data = self.get_all_cleaned_data()
        ar = self.object

        guests_to_move = data.get("guests") or ar.get_people_restrict_for_user(
            self.request.user
        )
        local_authority = data.get("local_authority")
        reason = data.get("reason")

        try:
            with transaction.atomic():
                ReassignmentRequest.create_reassignment_request(
                    accommodation_request=ar,
                    local_authority=local_authority,
                    reason=reason,
                    user=self.request.user,
                    guests_to_move=guests_to_move,
                )
        except DatabaseError:
            messages.error(
                self.request,
                "The reassignment request was not sent. If "
                "the problem continues raise a support ticket.",
            )
            return redirect(self.get_cancel_url())

        # Set names based on the number of guests moved
        names = guests_to_move[0].get_full_name()
        if len(guests_to_move) > 1:
            names_list = [guests.get_full_name() for guests in guests_to_move]
            names = ", ".join(names_list[:-1]) + f" and {names_list[-1]}"

        messages.success(
            self.request,
            f"You sent a request to move {names} to {local_authority.ltla_name}.",
        )

        return redirect(
            "accommodation-requests:detail-actions", pk=self.kwargs.get("pk")
        )

    def get_cancel_url(self):
        return get_url_for_actions_tab(self.get_object())


class AccommodationTable(tables.Table):
    context: dict[str, Any]
    request: HttpRequest

    full_address = Column(
        verbose_name="Address", attrs=SELECT_ACCOMMODATION_TABLE_COLUMN_ATTRS
    )
    postcode = Column(
        verbose_name="Postcode", attrs=SELECT_ACCOMMODATION_TABLE_COLUMN_ATTRS
    )
    select = Column(accessor="pk", verbose_name="", orderable=False)

    def render_full_address(self, record: MvAccommodation, value):
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{}" target="_blank">{}</a>',
            reverse("accommodations:detail-overview", args=[record.id]),
            value,
        )

    def render_select(self, value):
        return format_html(
            '<form method="post">'
            "{management_form}"
            '<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}"/>'
            '<input type="hidden" name="select_accommodation-accommodation" '
            'id="id_select_accommodation-accommodation" value="{value}"/>'
            '<button type="submit" name="submit" class="govuk-link">Select</button>'
            "</form>",
            management_form=self.context["wizard"]["management_form"],
            value=value,
            csrf_token=get_token(self.request),
        )

    class Meta:
        model = MvAccommodation
        template_name = "webapp/components/tables/table.html"
        fields = ("full_address",)


class AccommodationFilter(FilterPanelMixin, FilterSet):
    search = CharFilter(
        label="Search",
        method="search_filter",
        help_text="Search the data in the table",
    )

    show_temporary = BooleanFilter(
        label="Only show temporary accommodation",
        widget=widgets.CheckboxInput(attrs={"value": "Yes"}),
        method="show_temporary_filter",
    )

    def show_temporary_filter(self, queryset, _, value):
        if not value:
            return queryset
        return queryset.filter(
            accommodation_type=MvAccommodation.AccommodationType.TEMPORARY_ACCOMMODATION
        )

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, ACCOMMODATION_SEARCH_FIELDS)

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
            Fieldset(
                "show_temporary",
                legend="Temporary accommodation",
                legend_size=Size.MEDIUM,
                css_class="govuk-!-margin-top-5",
            ),
        )
        return form

    class Meta:
        model = MvAccommodation
        fields = [
            "search",
            "accommodation_type",
        ]


class RematchSelectAccommodationFormStepView(
    PermissionsMixin, SingleTableMixin, FilterView
):
    model = MvAccommodation
    table_class = AccommodationTable
    filterset_class = AccommodationFilter
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    template_name = (
        "accommodation_requests/"
        "move_guests/"
        "accommodation_requests_move_guests_select_accommodation_step.html"
    )

    def __init__(self, ltla=None, **kwargs):
        self.ltla = ltla
        self.filterset = None
        self.object_list = None
        super().__init__(**kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(ltla_name__in=self.ltla or [])

    def get_context_data(self, **kwargs):
        # Lifted from filters library
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


class MoveGuestsIsStayingInLaFormView(
    PIISafeRecordNameMixin, PermissionsMixin, SingleObjectMixin, FormView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
    ]
    model = MvAccommodationRequest
    form_class = MoveGuestsFormIsStayingInLAStep
    template_name = (
        "accommodation_requests/"
        "move_guests/"
        "accommodation_requests_move_guests_page.html"
    )

    def get_cancel_url(self):
        return get_url_for_actions_tab(self.get_object())

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.get_people_restrict_for_user(self.request.user).exists():
            return HttpResponse(status=409)

        if self.object.checks_status in [
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
            MvAccommodationRequest.ChecksStatus.CANCELLED,
            MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY,
            MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE,
        ]:
            return HttpResponse(status=409)

        return super().get(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.get_cancel_url()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["number_of_people"] = (
            len(self.object.person_id) if self.object.person_id else 0
        )
        return kwargs

    def form_valid(self, form):
        remaining_in_local_authority = form.cleaned_data["within_la"] == "yes"
        if remaining_in_local_authority:
            return redirect(
                reverse(
                    "accommodation-requests:rematch-guests",
                    kwargs={"pk": self.object.pk},
                )
                + "?reset"
            )
        return redirect(
            reverse(
                "accommodation-requests:reassign-guests",
                kwargs={"pk": self.object.pk},
            )
            + "?reset"
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object = None


class AccommodationRequestDetailCommentsView(
    PIISafeRecordNameMixin, MultiLABannerMixin, PermissionsMixin, DetailView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "accommodation_requests/detail_view/detail_view_comments.html"
    model = MvAccommodationRequest

    def get_context_data(self, **kwargs):
        self.add_multi_la_message()
        ctx = super().get_context_data(**kwargs)
        ctx["show_actions_tab"] = self.user_can_edit(
            group_types=AccommodationRequestDetailActionsView.group_type
        )
        ctx["show_history_tab"] = self.user_action_allowed(
            group_types=AccommodationRequestDetailHistoryView.group_type
        )
        comments = Comment.objects.filter(
            attached_accommodation_request_id=self.object.id
        ).order_by("-created_at")
        comment_ids = [str(c.id) for c in comments]

        attachments = (
            CommentAttachment.objects.only("id", "filename", "key", "comment_id")
            .filter(comment_id__in=comment_ids)
            .annotate(
                s3_file_name=Subquery(
                    CommentAttachmentMetadata.objects.filter(
                        attachment_key=OuterRef("key")
                    ).values("file_name")[:1]
                )
            )
            .filter(s3_file_name__isnull=False)
        )

        attachments_by_comment = {}
        for attachment in attachments:
            (
                attachments_by_comment.setdefault(attachment.comment_id, []).append(
                    attachment
                )
            )

        for comment in comments:
            comment.comment_attachments = attachments_by_comment.get(comment.id, [])

        events_with_files: set[uuid.UUID] = set()
        for comment in comments:
            for attachment in getattr(comment, "comment_attachments", []):
                if attachment.s3_file_name and s3_file_exists(
                    FILE_DOWNLOAD_S3_BUCKET_NAME,
                    f"comments/{attachment.s3_file_name}",
                ):
                    events_with_files.add(comment.id)
                    break

        ctx["events_with_files"] = events_with_files
        paginator = Paginator(comments, 30)
        ctx["events"] = paginator.get_page(self.request.GET.get("page"))
        ctx["event_type"] = TimelineEventType.COMMENT

        return ctx


class AccommodationRequestInteractionsDownloadAttachmentView(
    PermissionsMixin, DetailView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    model = MvAccommodationRequest

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.document = None
        self.file_name = None
        self.file_path = None

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        interaction = MvInteraction.objects.filter(
            pk=kwargs.get("interaction_id"),
        ).first()

        if not interaction or not interaction.attachment:
            raise Http404("Interaction not found or has no attachment")

        if (
            not interaction.linked_accommodation_request
            or interaction.linked_accommodation_request.id != self.object.id
        ):
            raise Http404("Interaction not found")

        # Get file metadata
        metadata = MvInteractionAttachmentMetadata.objects.filter(
            rid=interaction.attachment,
        ).first()

        if not metadata or not metadata.filename or not metadata.file_path:
            raise Http404("Missing file metadata")

        self.filename = metadata.filename
        self.file_path = metadata.file_path

        return super().dispatch(request, *args, **kwargs)

    def get(self, *_args, **_kwargs):
        try:
            presigned_url = get_presigned_download_url(
                bucket_name=FILE_DOWNLOAD_S3_BUCKET_NAME,
                file_key=f"interactions/{self.file_path}",
                filename=self.filename,
            )
        except ClientError as e:
            raise Http404("File not found") from e
        return redirect(presigned_url)


class AccommodationRequestCommentsDownloadAttachmentView(PermissionsMixin, DetailView):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    model = MvAccommodationRequest

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filename = None
        self.s3_file_name = None

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        comment = Comment.objects.filter(pk=kwargs.get("comment_id")).first()
        if not comment:
            raise Http404("Comment not found")

        if (
            not comment.attached_accommodation_request_id
            or comment.attached_accommodation_request_id.id != self.object.id
        ):
            raise Http404("Comment not attached to this accommodation request")

        attachment = CommentAttachment.objects.filter(
            pk=kwargs.get("attachment_id"), comment_id=comment.id
        ).first()

        if not comment or not attachment:
            raise Http404("Attachment not found")

        if not attachment or attachment.comment_id != comment.id:
            raise Http404("Attachment not connected to this comment")

        metadata = CommentAttachmentMetadata.objects.filter(
            attachment_key=attachment.key
        ).first()

        if not metadata or not metadata.file_name:
            raise Http404("Missing file metadata")

        self.filename = attachment.filename
        self.file_path = metadata.file_name

        return super().dispatch(request, *args, **kwargs)

    def get(self, *_args, **_kwargs):
        try:
            presigned_url = get_presigned_download_url(
                bucket_name=FILE_DOWNLOAD_S3_BUCKET_NAME,
                file_key=f"comments/{self.file_path}",
                filename=self.filename,
            )
        except ClientError as e:
            raise Http404("File not found") from e
        return redirect(presigned_url)
