import os
from datetime import datetime, timedelta

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Button, Div, Field, Layout
from crispy_forms_gds.layout.constants import Size
from django import forms
from django.contrib.messages.views import SuccessMessageMixin
from django.db import DatabaseError, transaction
from django.forms import ValidationError
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin
from django_filters import (
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
from accounts.models import GroupInfo
from case_management.settings import sentry_sdk
from ontology.models import ReassignmentRequest
from ontology.models.MvAccommodationRequest import MvAccommodationRequest
from ontology.models.MvInteraction import MvInteraction
from ontology.models.MvPerson import MvPerson
from reassignment_requests.forms import CancelReassignmentRequestForm
from webapp.constants import REASSIGNMENT_REQUEST_SEARCH_FIELDS
from webapp.enhanced_sentry_logging import db_values, log_event, log_persistence_check
from webapp.mixins import (
    FilterPanelMixin,
    PermissionsMixin,
)
from webapp.search import perform_search
from webapp.templatetags.reassignment_request_extras import (
    reassignment_request_outcome_label_to_tag_colour,
)
from webapp.utils import CustomDateColumn, CustomDateFromToRangeFilter, LazyChoiceFilter
from webapp.views import (
    SummaryListRow,
    SummaryListView,
)
from webapp.widgets import (
    CheckboxSelectMultipleWithTags,
    DatePicker,
    SearchableSelect,
    StackedRangeInput,
)


class ReassignmentRequestsMadeTable(tables.Table):
    guest_full_names = Column(verbose_name="Name")
    created_at = CustomDateColumn(verbose_name="Date of request")
    destination_ltla_name = Column(verbose_name="Moving to")
    outcome = Column(verbose_name="Status")

    def render_guest_full_names(self, record: ReassignmentRequest):
        names = record.formatted_guest_names()

        if not names:
            return "No guests"

        return format_html(
            "<a class='govuk-link' href={}>{}</a>",
            f"{record.pk}/",
            names,
        )

    def render_outcome(self, record: ReassignmentRequest):
        return render_to_string(
            "webapp/components/reassignment_request/reassignment_request_outcome_tag.html",
            {"outcome": ReassignmentRequest.Outcome(record.outcome.capitalize())},
        )

    class Meta:
        model = ReassignmentRequest
        template_name = "webapp/components/tables/table.html"
        fields = ("guest_full_names", "created_at", "destination_ltla_name", "outcome")
        empty_text = "You have no requests"
        order_by = ("-created_at",)


class ReassignmentRequestsReceivedTable(tables.Table):
    guest_full_names = Column(verbose_name="Name")
    created_at = CustomDateColumn(verbose_name="Date of request")
    source_ltla_name = Column(verbose_name="Moving from")
    outcome = Column(verbose_name="Status")

    def render_guest_full_names(self, record: ReassignmentRequest):
        names = record.formatted_guest_names()

        if not names:
            return "No guests"

        return format_html(
            "<a class='govuk-link' href={}>{}</a>",
            f"{record.pk}/",
            names,
        )

    def render_outcome(self, record: ReassignmentRequest):
        return render_to_string(
            "webapp/components/reassignment_request/reassignment_request_outcome_tag.html",
            {"outcome": ReassignmentRequest.Outcome(record.outcome.capitalize())},
        )

    def render_source_ltla_name(self, record: ReassignmentRequest):
        return "|".join(
            ltla_name for ltla_name in record.source_ltla_name if ltla_name is not None
        )

    class Meta:
        model = ReassignmentRequest
        template_name = "webapp/components/tables/table.html"
        fields = ("guest_full_names", "created_at", "source_ltla_name", "outcome")
        empty_text = "You have no requests"
        order_by = ("-created_at",)


class ReassignmentRequestsMadeFilter(FilterSet, FilterPanelMixin):
    outcome = MultipleChoiceFilter(
        choices=[
            choice
            for choice in ReassignmentRequest.Outcome.choices
            if choice[0] != "Needs Accommodation Request"
        ],
        label="Status",
        widget=CheckboxSelectMultipleWithTags(
            label_to_tag_colour=reassignment_request_outcome_label_to_tag_colour
        ),
    )

    created_at = CustomDateFromToRangeFilter(
        label="Date of request",
        field_name="created_at",
        widget=StackedRangeInput(
            sub_widget=DatePicker,
            attrs={
                "from_hint": f"For example "
                f"{(datetime.today() - timedelta(days=20)).strftime('%d/%m/%Y')}",
                "to_hint": f"For example "
                f"{(datetime.today() - timedelta(days=600)).strftime('%d/%m/%Y')}",
                "from_label": "Date from",
                "to_label": "Date to",
            },
        ),
        distinct=True,
        error_messages={
            "invalid_range": "'Date from' must be before 'Date to'.",
        },
    )

    destination_ltla_name = LazyChoiceFilter(
        choices=lambda: [
            (ltla, ltla)
            for ltla in ReassignmentRequest.objects.get_queryset()
            .values_list("destination_ltla_name", flat=True)
            .distinct()
            if ltla and len(ltla) > 0
        ],
        label="Moving to",
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
        return perform_search(value, queryset, REASSIGNMENT_REQUEST_SEARCH_FIELDS)

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
            Field.text("destination_ltla_name", small=True, label_size=Size.MEDIUM),
            Field("created_at", context={"legend_size": "govuk-fieldset__legend--m"}),
            Field("outcome", context={"label_size": "govuk-fieldset__legend--m"}),
        )
        return form

    class Meta:
        model = ReassignmentRequest
        fields = [
            "search",
            "outcome",
            "created_at",
            "destination_ltla_name",
        ]


class ReassignmentRequestsReceivedFilter(FilterSet, FilterPanelMixin):
    outcome = MultipleChoiceFilter(
        choices=[
            choice
            for choice in ReassignmentRequest.Outcome.choices
            if choice[0] != "Needs Accommodation Request"
        ],
        label="Status",
        widget=CheckboxSelectMultipleWithTags(
            label_to_tag_colour=reassignment_request_outcome_label_to_tag_colour
        ),
    )

    created_at = CustomDateFromToRangeFilter(
        label="Date of request",
        field_name="created_at",
        widget=StackedRangeInput(
            sub_widget=DatePicker,
            attrs={
                "from_hint": f"For example "
                f"{(datetime.today() - timedelta(days=20)).strftime('%d/%m/%Y')}",
                "to_hint": f"For example "
                f"{(datetime.today() - timedelta(days=600)).strftime('%d/%m/%Y')}",
                "from_label": "Date from",
                "to_label": "Date to",
            },
        ),
        distinct=True,
        error_messages={
            "invalid_range": "'Date from' must be before 'Date to'.",
        },
    )

    source_ltla_name = LazyChoiceFilter(
        choices=lambda: [
            (ltla, ltla)
            for ltla in sorted(
                {
                    name
                    for names in ReassignmentRequest.objects.values_list(
                        "source_ltla_name", flat=True
                    )
                    if names
                    for name in names
                    if name is not None
                }
            )
        ],
        label="Moving from",
        empty_label="",
        method="filter_source_ltla_name",
        widget=SearchableSelect(),
    )

    def filter_source_ltla_name(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(source_ltla_name__overlap=[value])

    search = CharFilter(
        label="Search",
        method="search_filter",
        help_text="Search the data in the table",
    )

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, REASSIGNMENT_REQUEST_SEARCH_FIELDS)

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
            Field.text("source_ltla_name", small=True, label_size=Size.MEDIUM),
            Field("created_at", context={"legend_size": "govuk-fieldset__legend--m"}),
            Field("outcome", context={"label_size": "govuk-fieldset__legend--m"}),
        )
        return form

    class Meta:
        model = ReassignmentRequest
        fields = [
            "search",
            "outcome",
            "created_at",
            "source_ltla_name",
        ]


class ReassignmentRequestsMadePageView(PermissionsMixin, SingleTableMixin, FilterView):
    model = ReassignmentRequest
    group_type = [
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.DEV,
        GroupType.MHCLG,
    ]

    table_class = ReassignmentRequestsMadeTable
    paginator_class = LazyPaginator
    filterset_class = ReassignmentRequestsMadeFilter
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    template_name = "reassignment_requests/reassignment_requests_tab_page.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .model.made.get_for_user(self.request.user)
            .only("pk", "created_at", "destination_ltla_name", "outcome")
            .prefetch_related("guests")
            .exclude(outcome=ReassignmentRequest.Outcome.NEEDS_ACCOMMODATION_REQUEST)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["title"] = "Requests made"
        context["description"] = (
            "Requests to move a guest from your local authority to "
            "another are listed here. Select a request to view details "
            "or cancel the request."
        )

        return context


class ReassignmentRequestsReceivedPageView(
    PermissionsMixin, SingleTableMixin, FilterView
):
    model = ReassignmentRequest
    group_type = [
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.DEV,
        GroupType.MHCLG,
    ]

    table_class = ReassignmentRequestsReceivedTable
    filterset_class = ReassignmentRequestsReceivedFilter
    paginator_class = LazyPaginator
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    template_name = "reassignment_requests/reassignment_requests_tab_page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["title"] = "Requests received"
        context["description"] = (
            "Requests to move a guest from your local authority to "
            "another are listed here. Select a request to approve or reject it."
        )

        return context

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .model.received.get_for_user(self.request.user)
            .only("pk", "created_at", "source_ltla_name", "outcome")
            .prefetch_related("guests")
            .exclude(outcome=ReassignmentRequest.Outcome.NEEDS_ACCOMMODATION_REQUEST)
        )


class AcceptRejectReassignmentRequestForm(forms.Form):
    action = forms.ChoiceField(
        choices=[
            ("accept", "Accept request"),
            ("reject", "Reject request"),
        ],
        widget=forms.RadioSelect,
        required=True,
        label="",
    )
    comments = forms.CharField(
        widget=forms.Textarea(),
        required=True,
        label="Reason",
        help_text=(
            "You must add a reason. The text you enter should be short and clear."
        ),
    )

    def __init__(self, *args, reassignment_request=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.reassignment_request = reassignment_request

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.radios(
                "action",
                legend_size=Size.LARGE,
            ),
            Field.textarea(
                "comments", label_size=Size.LARGE, rows=5, max_characters=500
            ),
            Div(
                Button("submit", "Confirm"),
                HTML(
                    '<a href="{{ cancel_url }}"'
                    'class="govuk-link govuk-link--no-visited-state govuk-body">'
                    "Cancel"
                    "</a>"
                ),
                css_class="govuk-button-group",
            ),
        )

    def clean(self):
        accommodation_request = self.reassignment_request.get_accommodation_request()

        if not accommodation_request:
            raise ValidationError(
                "We are unable to find the the accommodation request for this "
                "reassignment request. "
                "Please check the accommodation request is attached to the "
                "reassignment request."
            )


class ReassignmentRequestDetailView(
    PermissionsMixin,
    SuccessMessageMixin,
    FormView,
    SummaryListView,
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.SERVICE_SUPPORT,
    ]
    model = ReassignmentRequest
    template_name = "reassignment_requests/detail_view.html"
    form_class = AcceptRejectReassignmentRequestForm

    created_at = SummaryListRow(verbose_name="Request date")
    source_ltla_name = SummaryListRow(verbose_name="Moving from")
    destination_ltla_name = SummaryListRow(verbose_name="Moving to")

    def render_guests(self, record: ReassignmentRequest):
        return record.formatted_guest_names()

    def render_source_ltla_name(self, record: ReassignmentRequest):
        return "|".join(ltla_name for ltla_name in record.source_ltla_name if ltla_name)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        return super().post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if self.object is None:
            self.object = super().get_object(queryset)

            if self.object is None:
                return HttpResponse(status=404)

        return self.object

    def get_success_url(self):
        return reverse("reassignment-requests:received")

    def get_cancel_url(self):
        return reverse("reassignment-requests:received")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["reassignment_request"] = self.get_object()

        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["fields"] = self.build_name_value_pairs(self.get_all_fields())
        ctx["cancel_url"] = self.get_cancel_url()
        ctx["show_accept_reject_form"] = (
            ReassignmentRequest.received.get_for_user(self.request.user)
            .filter(
                pk=self.get_object().pk,
                outcome=ReassignmentRequest.Outcome.PENDING,
            )
            .exists()
        )

        ctx["show_cancel_request_button"] = (
            ReassignmentRequest.made.get_for_user(self.request.user)
            .filter(
                pk=self.get_object().pk,
                outcome=ReassignmentRequest.Outcome.PENDING,
            )
            .exists()
        )

        return ctx

    def form_valid(self, form):
        data = form.cleaned_data
        reassignment_request = self.get_object()
        action = data["action"]
        comments = data["comments"]
        is_partial = False

        guest_ids = [g.id for g in reassignment_request.guests.all()]

        log_event(
            f"{action}_reassignment_request: started",
            reassignment_request_pk=reassignment_request.pk,
            ar_pk=reassignment_request.accommodation_request_id,
            guest_pks=guest_ids,
            source_ltla_name=reassignment_request.source_ltla_name,
            destination_ltla_name=reassignment_request.destination_ltla_name,
            user_pk=self.request.user.pk,
        )

        try:
            with transaction.atomic():
                formatted_guest_names = reassignment_request.formatted_guest_names()

                from_ltla_name = (
                    self.render_source_ltla_name(reassignment_request) or "Unknown LTLA"
                )

                if action == "accept":
                    reassignment_request.outcome = ReassignmentRequest.Outcome.ACCEPTED

                    # current ar
                    ar = reassignment_request.accommodation_request

                    # determine if all AR guests are moved or just partial
                    is_partial = (
                        reassignment_request.guests.count()
                        != reassignment_request.accommodation_request.number_of_people
                    )

                    if is_partial:
                        # create an interaction to display on the old, combined AR
                        partial_interaction = MvInteraction.create_interaction(
                            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
                            interaction_type=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
                            linked_accommodation_request=ar,
                            interaction_notes=f"{reassignment_request.destination_ltla_name}"
                            f" accepted the reassignment request from "
                            f"{from_ltla_name} for "
                            f"[names_list]{formatted_guest_names}.[names_list_end]"
                            f" Reason for accepting: {comments}",
                            created_by=self.request.user,
                            title=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
                        )
                        log_event(
                            "accept_reassignment_request:"
                            " partial split interaction created",
                            reassignment_request_pk=reassignment_request.pk,
                            original_ar_pk=ar.pk,
                            interaction_pk=partial_interaction.pk,
                            interaction_type=partial_interaction.interaction_type,
                        )

                        # new ar resulted from splitting
                        pre_split_ar = ar
                        pre_split_person_id = list(pre_split_ar.person_id or [])
                        ar = ar.split_guests(guest_ids)
                        log_event(
                            "accept_reassignment_request: guests split to new AR",
                            reassignment_request_pk=reassignment_request.pk,
                            original_ar_pk=pre_split_ar.pk,
                            new_ar_pk=ar.pk,
                            guest_pks=guest_ids,
                        )
                        persisted_pre_split = db_values(
                            pre_split_ar, "person_id", "edited_in_app"
                        )
                        log_persistence_check(
                            "accept_reassignment_request:"
                            " original AR guests after split",
                            reassignment_request_pk=reassignment_request.pk,
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
                        persisted_new_split = db_values(
                            ar, "person_id", "edited_in_app"
                        )
                        log_persistence_check(
                            "accept_reassignment_request: new AR guests after split",
                            reassignment_request_pk=reassignment_request.pk,
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

                    group_info = GroupInfo.objects.filter(
                        ltla_name=reassignment_request.destination_ltla_name
                    ).first()

                    gss_code = None
                    if group_info and group_info.gss_code:
                        gss_code = [group_info.gss_code]

                    utla_gss_code = None
                    if group_info and group_info.utla_gss_code:
                        utla_gss_code = [group_info.utla_gss_code]

                    # Update location with destination details
                    ar.ltla_name = [reassignment_request.destination_ltla_name]
                    ar.ltla_code_id = gss_code
                    # ar.ltla_code we don't use UkLocalAuthority m2m relationship
                    ar.utla_name = [reassignment_request.destination_utla_name]
                    ar.utla_code_id = utla_gss_code
                    # ar.utla_code we don't use UkLocalAuthority m2m relationship

                    # Update rest of the details
                    ar.checks_status = (
                        MvAccommodationRequest.ChecksStatus.REMATCH_REQUIRED
                    )
                    ar.save()

                    persisted_ar = db_values(
                        ar,
                        "ltla_name",
                        "utla_name",
                        "checks_status",
                        "person_id",
                        "edited_in_app",
                    )
                    log_persistence_check(
                        "accept_reassignment_request: AR updated",
                        reassignment_request_pk=reassignment_request.pk,
                        ar_pk=ar.pk,
                        changes={
                            "ltla_name": (ar.ltla_name, persisted_ar.get("ltla_name")),
                            "utla_name": (ar.utla_name, persisted_ar.get("utla_name")),
                            "checks_status": (
                                ar.checks_status,
                                persisted_ar.get("checks_status"),
                            ),
                            "person_id": (
                                ar.person_id,
                                persisted_ar.get("person_id"),
                            ),
                            "edited_in_app": (
                                ar.edited_in_app,
                                persisted_ar.get("edited_in_app"),
                            ),
                        },
                    )

                    guest_ar_links = list(
                        MvPerson.objects.filter(id__in=guest_ids).values(
                            "id", "accommodation_request_id"
                        )
                    )
                    log_event(
                        "accept_reassignment_request: guest AR links",
                        reassignment_request_pk=reassignment_request.pk,
                        ar_pk=ar.pk,
                        guest_ar_links=guest_ar_links,
                    )

                    # Update AR accommodations
                    ar.update_accommodation(
                        new_accommodation=None, author=self.request.user
                    )
                    persisted_accommodation = db_values(
                        ar,
                        "accommodation_id",
                        "primary_accommodation_id",
                        "postcode",
                        "edited_in_app",
                    )
                    log_persistence_check(
                        "accept_reassignment_request: accommodation unlinked",
                        reassignment_request_pk=reassignment_request.pk,
                        ar_pk=ar.pk,
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

                    # Unlink hosts from AR
                    ar.unlink_host(author=self.request.user)
                    persisted_host = db_values(
                        ar,
                        "active_host_id",
                        "active_eoi_host_id",
                        "is_eoi_host",
                        "edited_in_app",
                    )
                    log_persistence_check(
                        "accept_reassignment_request: host unlinked",
                        reassignment_request_pk=reassignment_request.pk,
                        ar_pk=ar.pk,
                        changes={
                            "active_host_id": (
                                ar.active_host_id,
                                persisted_host.get("active_host_id"),
                            ),
                            "active_eoi_host_id": (
                                ar.active_eoi_host_id,
                                persisted_host.get("active_eoi_host_id"),
                            ),
                            "is_eoi_host": (
                                ar.is_eoi_host,
                                persisted_host.get("is_eoi_host"),
                            ),
                            "edited_in_app": (
                                ar.edited_in_app,
                                persisted_host.get("edited_in_app"),
                            ),
                        },
                    )

                    # Create interaction for reassignment request accepted
                    accepted_interaction = MvInteraction.create_interaction(
                        interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
                        interaction_type=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
                        linked_accommodation_request=ar,
                        interaction_notes=f"{reassignment_request.destination_ltla_name}"
                        f" accepted the reassignment request from "
                        f"{from_ltla_name} for "
                        f"[names_list]{formatted_guest_names}.[names_list_end]"
                        f" Reason for accepting: {comments}",
                        created_by=self.request.user,
                        title=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
                    )
                    log_event(
                        "accept_reassignment_request: interaction created",
                        reassignment_request_pk=reassignment_request.pk,
                        ar_pk=ar.pk,
                        interaction_pk=accepted_interaction.pk,
                        interaction_type=accepted_interaction.interaction_type,
                    )

                    self.success_message = (
                        f"You have approved the request to move "
                        f"{formatted_guest_names} from {from_ltla_name}"
                    )

                elif action == "reject":
                    reassignment_request.outcome = ReassignmentRequest.Outcome.REJECTED

                    # Create interaction for reassignment request rejected
                    rejected_interaction = MvInteraction.create_interaction(
                        interaction_contact=(
                            MvInteraction.InteractionContact.REASSIGNMENT_REJECTED
                        ),
                        interaction_type=(
                            MvInteraction.InteractionContact.REASSIGNMENT_REJECTED
                        ),
                        linked_accommodation_request=(
                            reassignment_request.accommodation_request
                        ),
                        interaction_notes=f"{reassignment_request.destination_ltla_name}"
                        f" rejected the reassignment request from "
                        f"{from_ltla_name} for "
                        f"[names_list]{formatted_guest_names}.[names_list_end]"
                        f" Reason for rejecting: {comments}",
                        created_by=self.request.user,
                        title=MvInteraction.InteractionContact.REASSIGNMENT_REJECTED,
                    )
                    log_event(
                        "reject_reassignment_request: interaction created",
                        reassignment_request_pk=reassignment_request.pk,
                        ar_pk=reassignment_request.accommodation_request_id,
                        interaction_pk=rejected_interaction.pk,
                        interaction_type=rejected_interaction.interaction_type,
                    )

                    self.success_message = (
                        f"You have rejected the request to move "
                        f"{formatted_guest_names} from {from_ltla_name}"
                    )

                reassignment_request.responded_at = timezone.now()
                reassignment_request.responded_by = self.request.user
                reassignment_request.comments = comments
                reassignment_request.save()

                persisted_rr = db_values(
                    reassignment_request, "outcome", "responded_at"
                )
                log_persistence_check(
                    f"{action}_reassignment_request: outcome set",
                    reassignment_request_pk=reassignment_request.pk,
                    changes={
                        "outcome": (
                            reassignment_request.outcome,
                            persisted_rr.get("outcome"),
                        ),
                        "responded_at": (
                            reassignment_request.responded_at,
                            persisted_rr.get("responded_at"),
                        ),
                    },
                )

                # Send Sentry metric for journey completion regardless of status
                sentry_sdk.metrics.count(
                    "reassignment_request",
                    1,
                    attributes={
                        "action": action,
                        "user_id": self.request.user.id,
                        "is_partial": is_partial,
                    },
                )

        except DatabaseError:
            form.add_error(
                None,
                "The reassignment request was not updated. If"
                " the problem continues raise a support ticket.",
            )
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_all_fields(self):
        url_name = self.request.resolver_match.url_name
        fields = ["created_at", "guests", "reason"]

        # Insert before 'reason' based on the URL name
        if url_name == "detail-made":
            fields.insert(-1, "destination_ltla_name")
        elif url_name == "detail-received":
            fields.insert(-1, "source_ltla_name")

        return fields

    class Meta:
        fields = [
            "created_at",
            "guests",
            "source_ltla_name",
            "destination_ltla_name",
            "reason",
        ]


class CancelReassignmentRequestView(
    PermissionsMixin,
    SingleObjectMixin,
    SuccessMessageMixin,
    FormView,
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
    ]
    model = ReassignmentRequest
    form_class = CancelReassignmentRequestForm
    template_name = "reassignment_requests/cancel_request_view.html"

    def get_cancel_url(self):
        return "./"

    def get_success_url(self):
        return reverse(
            "accommodation-requests:detail-actions",
            kwargs={"pk": self.get_object().accommodation_request.pk},
        )

    def get_success_message(self, cleaned_data):
        return (
            f"You have cancelled the request to move "
            f"{self.get_object().formatted_guest_names()} to "
            f"{self.get_object().destination_ltla_name}"
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["reassignment_request"] = self.get_object()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.get_cancel_url()
        return context

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        return super().get(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        reassignment_request: ReassignmentRequest = self.get_object()

        log_event(
            "cancel_reassignment_request: started",
            reassignment_request_pk=reassignment_request.pk,
            ar_pk=reassignment_request.accommodation_request_id,
            user_pk=self.request.user.pk,
        )

        reassignment_request.outcome = ReassignmentRequest.Outcome.REJECTED
        reassignment_request.comments = "Cancelled by sending LA"
        reassignment_request.responded_at = timezone.now()
        reassignment_request.responded_by = self.request.user
        reassignment_request.save()

        persisted_rr = db_values(reassignment_request, "outcome")
        log_persistence_check(
            "cancel_reassignment_request: outcome set",
            reassignment_request_pk=reassignment_request.pk,
            changes={
                "outcome": (reassignment_request.outcome, persisted_rr.get("outcome")),
            },
        )

        # Send Sentry metric for completed user journey (cancel action)
        # No information about whether the request is partial or not, so just
        # set to False for now
        sentry_sdk.metrics.count(
            "reassignment_request",
            1,
            attributes={
                "action": "cancelled",
                "user_id": self.request.user.id,
                "is_partial": False,
            },
        )

        return super().form_valid(form)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object = None
