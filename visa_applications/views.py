import math
import os
import uuid
from datetime import datetime, timedelta
from typing import Any

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Fieldset, Layout
from crispy_forms_gds.layout.constants import Size
from django.contrib import messages
from django.db.models import QuerySet
from django.forms.widgets import CheckboxSelectMultiple
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.views.generic import DetailView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormView
from django_filters import CharFilter, FilterSet, MultipleChoiceFilter
from django_filters.views import FilterView
from django_tables2 import (
    Column,
    LazyPaginator,
    SingleTableMixin,
    tables,
)

from accounts.enums import GroupType
from accounts.mixins import user_in_any_group_types
from accounts.models import GroupInfo, User
from ontology.models import (
    MvAccommodationRequest,
    MvVolunteer,
    VisaApplication,
    VisaInformationRequest,
    VisaInformationRequestComments,
)
from visa_applications.forms import (
    AddVIRCommentForm,
    StartVIRForm,
    VIRCloseConfirmForm,
    VIRReopenConfirmForm,
)
from visa_applications.templatetags.visa_application_extras import (
    vir_status_to_tag_colour,
    visa_status_to_tag_colour,
)
from webapp.constants import (
    VIR_SEARCH_FIELDS,
    VISA_APPLICATION_SEARCH_FIELDS,
    vir_status_list,
    visa_status_list,
)
from webapp.mixins import (
    FilterPanelMixin,
    PermissionsMixin,
    PIISafeRecordNameMixin,
)
from webapp.search import perform_search
from webapp.utils import (
    CustomDateColumn,
    CustomDateFromToRangeFilter,
    CustomDateTimeColumn,
    LazyChoiceFilter,
)
from webapp.views import SummaryListView, SummaryListViewBase
from webapp.widgets import (
    CheckboxSelectMultipleWithTags,
    DatePicker,
    SearchableSelect,
    StackedRangeInput,
)


def can_user_see_vir_tab(user, visa_application=None):
    """
    Returns True if the user can see the VIR tab:
    - DEV or UKVI users always see it.
    - LA or DA users see it if there is at least one VIR for the application.
    - LA or DA users cannot see the tab if there are no VIRs for the application.
    """
    if user_in_any_group_types(user, [GroupType.DEV, GroupType.HOME_OFFICE]):
        return True
    if user_in_any_group_types(
        user,
        [GroupType.LOCAL_AUTHORITY, GroupType.DEVOLVED_ADMINISTRATION, GroupType.MHCLG],
    ):
        if visa_application is not None:
            virs = VisaInformationRequest.objects.filter(
                visa_application=visa_application
            )
            return virs.exists()
    return False


class VisaApplicationsTable(tables.Table):
    application_event_datetime = CustomDateTimeColumn(verbose_name="Application date")
    visa_decision_date = CustomDateTimeColumn(verbose_name="Decision date")
    title = Column(verbose_name="Name")
    ltla_name = Column(verbose_name="Local authority")
    Q97c_sponsor_name = Column(verbose_name="Sponsor name")
    gwf = Column(verbose_name="Global web form number (GWF)")

    def render_visa_status(self, value):
        return render_to_string(
            "webapp/components/visa_status_tag/visa_status_tag.html",
            {"visa_status": value},
        )

    def render_title(self, record, value):
        return format_html(
            (
                '<a class="govuk-body-s govuk-link"'
                'style="white-space: normal" href="{}">'
                "{}"
                "</a>"
            ),
            reverse(
                "visa-applications:detail-overview", args=[record.visa_application_id]
            ),
            value,
        )

    class Meta:
        model = VisaApplication
        template_name = "webapp/components/tables/table.html"
        fields = (
            "title",
            "visa_status",
            "application_event_datetime",
            "visa_decision_date",
            "Q97c_sponsor_name",
            "ltla_name",
            "gwf",
            "application_unique_application_number",
        )
        order_by = ("-application_event_datetime",)


class VisaApplicationsTableFilter(FilterSet, FilterPanelMixin):
    visa_status = MultipleChoiceFilter(
        choices=[(value.name, value.name) for value in visa_status_list],
        label="Visa status",
        widget=CheckboxSelectMultipleWithTags(
            label_to_tag_colour=visa_status_to_tag_colour
        ),
    )

    application_event_datetime = CustomDateFromToRangeFilter(
        label="Application date",
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
        error_messages={
            "invalid_range": "'Date from' must be before 'Date to'.",
        },
    )

    visa_decision_date = CustomDateFromToRangeFilter(
        label="Decision date",
        widget=StackedRangeInput(
            sub_widget=DatePicker,
            attrs={
                "from_hint": f"For example "
                f"{(datetime.today() - timedelta(days=50)).strftime('%d/%m/%Y')}",
                "to_hint": f"For example "
                f"{(datetime.today() + timedelta(days=400)).strftime('%d/%m/%Y')}",
                "from_label": "Date from",
                "to_label": "Date to",
            },
        ),
        error_messages={
            "invalid_range": "'Date from' must be before 'Date to'.",
        },
    )

    ltla_name = LazyChoiceFilter(
        choices=lambda: [
            (ltla, ltla)
            for ltla in MvAccommodationRequest.objects.get_queryset().ltla_names()
        ],
        label="Local authority",
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
        return perform_search(value, queryset, VISA_APPLICATION_SEARCH_FIELDS)

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
            Field("visa_status", context={"label_size": "govuk-fieldset__legend--m"}),
            Field.text("ltla_name", small=True, label_size=Size.MEDIUM),
            Field(
                "application_event_datetime",
                context={
                    "legend_size": "govuk-fieldset__legend--m",
                },
            ),
            Field(
                "visa_decision_date",
                context={"legend_size": "govuk-fieldset__legend--m"},
            ),
        )
        return form

    class Meta:
        model = VisaApplication
        fields = [
            "search",
            "visa_status",
            "ltla_name",
            "application_event_datetime",
            "visa_decision_date",
        ]


class VisaApplicationListView(PermissionsMixin, SingleTableMixin, FilterView):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    model = VisaApplication
    table_class = VisaApplicationsTable
    filterset_class = VisaApplicationsTableFilter
    template_name = "visa_applications/visa_applications.html"
    paginate_by = os.environ.get("PAGINATION_PAGE_SIZE")
    paginator_class = LazyPaginator

    def get_queryset(self):
        fields_needed = [
            "title",
            "visa_status",
            "application_event_datetime",
            "visa_decision_date",
            "Q97c_sponsor_name",
            "ltla_name",
            "gwf",
            "application_unique_application_number",
            "Q11b_applicant_date_of_birth",
        ]
        return (
            super()
            .get_queryset()
            .only(*fields_needed)
            .order_by("-application_event_datetime")
        )


class VisaApplicationPropertiesView(
    PIISafeRecordNameMixin, PermissionsMixin, SummaryListViewBase
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "visa_applications/detail_view/detail_view_properties.html"
    model = VisaApplication

    def _split_columns(self, fields: list[str], split_at_field: str | None = None):
        if split_at_field and split_at_field in fields:
            split_point = fields.index(split_at_field)
        else:
            split_point = math.ceil(len(fields) / 2)
        return fields[:split_point], fields[split_point:]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_fields = self.get_all_fields()

        property_fields = [field for field in all_fields if not field.startswith("Q")]
        question_fields = sorted(
            [field for field in all_fields if field.startswith("Q")],
            key=lambda x: int("".join(filter(str.isdigit, x.split("_")[0]))),
        )

        property_left, property_right = self._split_columns(
            property_fields, self.get_meta_attr("split_properties_columns_at_field")
        )
        question_left, question_right = self._split_columns(question_fields)
        context.update(
            {
                "properties_left": self.build_name_value_pairs(property_left),
                "properties_right": self.build_name_value_pairs(property_right),
                "questions_left": self.build_name_value_pairs(question_left),
                "questions_right": self.build_name_value_pairs(question_right),
            }
        )
        context["show_vir_tab"] = can_user_see_vir_tab(self.request.user, self.object)

        return context

    class Meta:
        exclude_fields = [
            "viewer_group_names",
            "viewer_group_names_multi_la",
        ]
        split_properties_columns_at_field = "mapping_postcode"


class VisaApplicationOverviewView(
    PIISafeRecordNameMixin, PermissionsMixin, SummaryListView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "visa_applications/detail_view/detail_view_overview.html"
    model = VisaApplication

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        visa_application = self.object

        context["show_vir_tab"] = can_user_see_vir_tab(self.request.user, self.object)
        context["fields"] = [
            (
                "Guest name",
                [
                    guest.get_full_name()
                    for guest in visa_application.get_guests_restrict_for_user(user)
                ],
            ),
            (
                "Visa status",
                visa_application.visa_status,
            ),
            (
                "Application date",
                (
                    visa_application.application_event_datetime.strftime(
                        "%d %b %Y at %-I:%M%p"
                    )
                    .replace("AM", "am")
                    .replace("PM", "pm")
                    if visa_application.application_event_datetime
                    else None
                ),
            ),
            (
                "Decision date",
                (
                    visa_application.visa_decision_date.strftime("%d %b %Y at %-I:%M%p")
                    .replace("AM", "am")
                    .replace("PM", "pm")
                    if visa_application.visa_decision_date
                    else None
                ),
            ),
            (
                "Sponsor name",
                [
                    sponsor.get_full_name()
                    for sponsor in visa_application.get_sponsors_restrict_for_user(user)
                ],
            ),
            (
                "Local authority",
                visa_application.ltla_name,
            ),
            (
                "Global web form number (GWF)",
                visa_application.gwf,
            ),
            (
                "Unique application number (UAN)",
                visa_application.application_unique_application_number,
            ),
        ]
        return context


class VisaApplicationLinkedRecordsView(
    PIISafeRecordNameMixin, PermissionsMixin, DetailView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "visa_applications/detail_view/detail_view_linked_records.html"
    model = VisaApplication

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        visa_application: VisaApplication = self.object

        linked_records = []
        user = self.request.user

        accommodation_requests: QuerySet[MvAccommodationRequest] = (
            visa_application.get_accommodation_requests_restrict_for_user(user)
        )
        if accommodation_requests.exists():
            linked_records.append(("Accommodation request", accommodation_requests))

        guests = visa_application.get_guests_restrict_for_user(user)
        if guests.exists():
            linked_records.append(("Guest", guests))

        sponsors = visa_application.get_sponsors_restrict_for_user(user)
        if sponsors.exists():
            linked_records.append(("Sponsor", sponsors))

        hosts: list[MvVolunteer] = []
        for ar in accommodation_requests:
            if host := ar.get_host_restrict_for_user(user):
                hosts.append(host)

        if len(hosts) != 0:
            linked_records.append(("Host", hosts))

        accommodations = visa_application.get_accommodations_restrict_for_user(user)
        if accommodations:
            linked_records.append(("Accommodation", accommodations))

        ctx["fields"] = linked_records
        ctx["show_vir_tab"] = can_user_see_vir_tab(self.request.user, self.object)
        return ctx


class VisaApplicationVIRView(
    PIISafeRecordNameMixin, PermissionsMixin, SingleObjectMixin, FormView
):
    template_name = "visa_applications/detail_view/detail_view_vir.html"
    model = VisaApplication

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.object = None

    def get_group_type(self):
        obj = self.object or self.get_object()
        groups = [
            GroupType.DEV,
            GroupType.MHCLG,
            GroupType.HOME_OFFICE,
            GroupType.SERVICE_SUPPORT,
        ]
        if can_user_see_vir_tab(self.request.user, obj):
            groups.append(GroupType.LOCAL_AUTHORITY)
            groups.append(GroupType.DEVOLVED_ADMINISTRATION)
        return groups

    def get_form_class(self):
        vir = self.get_latest_vir()
        if vir is None:
            return StartVIRForm
        if vir.request_status != VisaInformationRequest.RequestStatus.CLOSED:
            return AddVIRCommentForm
        return StartVIRForm

    def get_latest_vir(self):
        return (
            VisaInformationRequest.objects.filter(visa_application=self.get_object())
            .order_by("-created_at")
            .first()
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        latest_vir = self.get_latest_vir()
        user_can_close_vir = self.user_action_allowed(
            group_types=[GroupType.DEV, GroupType.HOME_OFFICE]
        )
        if (
            latest_vir
            and latest_vir.request_status != VisaInformationRequest.RequestStatus.CLOSED
        ):
            add_comment_form = AddVIRCommentForm(user_can_close_vir=user_can_close_vir)
            return self.render_to_response(
                self.get_context_data(add_comment_form=add_comment_form)
            )
        return super().get(request, *args, **kwargs)

    def get_action(self, form, request):
        if isinstance(form, StartVIRForm) and "start_vir_submit" in request.POST:
            return "start_vir"
        if isinstance(form, AddVIRCommentForm) and "add_comment_submit" in request.POST:
            return "add_comment"
        if isinstance(form, AddVIRCommentForm) and "close_vir_submit" in request.POST:
            return "close_vir"
        return None

    def handle_action(self, form, action, request, *args, **kwargs):
        if action == "close_vir":
            return redirect(
                reverse("visa-applications:close-vir-confirm", args=[self.object.pk])
            )
        form_is_valid = form.is_valid()
        if form_is_valid:
            if action == "add_comment":
                return self.handle_add_comment(form)
            if action == "start_vir":
                return self.handle_start_vir(form)
        else:
            if action in ("add_comment", "start_vir"):
                return self.form_invalid(form)
        return self.get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        user_can_close_vir = self.user_action_allowed(
            group_types=[GroupType.DEV, GroupType.HOME_OFFICE]
        )
        if form_class is AddVIRCommentForm:
            form = form_class(self.request.POST, user_can_close_vir=user_can_close_vir)
        else:
            form = form_class(self.request.POST)

        action = self.get_action(form, request)
        return self.handle_action(form, action, request, *args, **kwargs)

    def handle_start_vir(self, form):
        if not self.user_action_allowed(
            group_types=[GroupType.DEV, GroupType.HOME_OFFICE]
        ):
            messages.error(self.request, "You do not have permission to start a VIR.")
            return redirect(
                reverse("visa-applications:detail-vir", args=[self.object.pk])
            )

        vir = form.save(commit=False)
        vir.visa_information_request_id = str(uuid.uuid4())
        vir.visa_application = self.object
        vir.created_by = (
            self.request.user.username if self.request.user.is_authenticated else None
        )
        vir.request_status = VisaInformationRequest.RequestStatus.AWAITING_LA.value
        now = timezone.now()
        vir.created_at = now
        vir.requested_at = now
        vir.ltla_name = self.object.ltla_name
        vir.utla_name = self.object.utla_name
        vir.save()

        comment_text = form.cleaned_data.get("comment", "").strip()
        VisaInformationRequestComments.objects.create(
            id=str(uuid.uuid4()),
            visa_information_request=vir,
            comment=comment_text,
            created_at=now,
            created_by_uid=(
                self.request.user.username
                if self.request.user.is_authenticated
                else None
            ),
            display_name=self._get_display_name(self.request.user, vir.ltla_name),
        )

        messages.success(self.request, "Successfully started VIR.")
        return redirect(reverse("visa-applications:detail-vir", args=[self.object.pk]))

    def handle_add_comment(self, form):
        comment = form.save(commit=False)
        vir = VisaInformationRequest.objects.filter(
            visa_application=self.object
        ).latest("created_at")
        comment.visa_information_request = vir
        comment.id = str(uuid.uuid4())
        comment.created_at = timezone.now()
        comment.created_by_uid = (
            self.request.user.username if self.request.user.is_authenticated else None
        )
        comment.display_name = self._get_display_name(self.request.user, vir.ltla_name)
        comment.save()

        user = self.request.user
        user_groups = set(user.groups.values_list("groupinfo__group_type", flat=True))
        if user_groups & {
            GroupType.LOCAL_AUTHORITY,
            GroupType.DEVOLVED_ADMINISTRATION,
            GroupType.MHCLG,
        }:
            vir.request_status = VisaInformationRequest.RequestStatus.AWAITING_UKVI
            vir.save(update_fields=["request_status"])
        elif user_groups & {GroupType.HOME_OFFICE}:
            vir.request_status = VisaInformationRequest.RequestStatus.AWAITING_LA
            vir.save(update_fields=["request_status"])

        messages.success(self.request, "Comment added successfully.")
        return redirect(reverse("visa-applications:detail-vir", args=[self.object.pk]))

    def _get_display_name(self, user, vir_ltla_name=None):
        user_groups = set(user.groups.values_list("groupinfo__group_type", flat=True))
        if user_groups & {GroupType.HOME_OFFICE}:
            return "UKVI"
        if GroupType.LOCAL_AUTHORITY in user_groups:
            la_groups = user.groups.filter(
                groupinfo__group_type=GroupType.LOCAL_AUTHORITY
            )
            display_name = "Local Authority User"
            if vir_ltla_name:
                group = la_groups.filter(groupinfo__ltla_name=vir_ltla_name).first()
                if group and group.groupinfo and group.groupinfo.ltla_name:
                    display_name = group.groupinfo.ltla_name
                else:
                    group = la_groups.first()
                    if group and group.groupinfo and group.groupinfo.ltla_name:
                        display_name = group.groupinfo.ltla_name
            else:
                group = la_groups.first()
                if group and group.groupinfo and group.groupinfo.ltla_name:
                    display_name = group.groupinfo.ltla_name
            return display_name
        if user_groups & {GroupType.MHCLG}:
            return "MHCLG Ops"
        if user_groups & {GroupType.DEV}:
            return "MHCLG Admin"
        return user.username

    def _get_display_time(self, created_at, now):
        if created_at:
            delta = now - created_at
            if delta.total_seconds() < 60:
                return "now"
            if delta.total_seconds() < 3600:
                minutes = int(delta.total_seconds() // 60)
                return f"{minutes}m"
            if delta.total_seconds() < 86400:
                hours = int(delta.total_seconds() // 3600)
                return f"{hours}h"
            if abs((now - created_at).days) > 365:
                return created_at.strftime("%d %b %y")
            return created_at.strftime("%d %b")
        return ""

    def _get_conversations(self, virs, comments):
        conversations = {vir.visa_information_request_id: [] for vir in virs}
        for comment in comments:
            vir_id = comment.visa_information_request_id
            conversations.setdefault(vir_id, []).append(comment)
        return conversations

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visa_application = self.object
        context["show_vir_tab"] = can_user_see_vir_tab(
            self.request.user, visa_application
        )

        virs = VisaInformationRequest.objects.filter(visa_application=visa_application)
        comments = VisaInformationRequestComments.objects.filter(
            visa_information_request__in=virs
        ).order_by("-created_at")
        conversations = self._get_conversations(virs, comments)
        now = timezone.now()
        user_ids = {
            comment.created_by_uid for comment in comments if comment.created_by_uid
        }
        users = User.objects.filter(username__in=user_ids).prefetch_related(
            "groups__groupinfo"
        )
        user_map = {u.username: u for u in users}
        for comment_list in conversations.values():
            for comment in comment_list:
                if comment.display_name:
                    pass
                else:
                    user = user_map.get(comment.created_by_uid)
                    comment.display_name = (
                        self._get_display_name(
                            user, comment.visa_information_request.ltla_name
                        )
                        if user
                        else "Unknown user"
                    )
                comment.display_time = self._get_display_time(comment.created_at, now)

        context["virs"] = virs
        context["conversations"] = conversations
        context["start_vir_form"] = kwargs.get("start_vir_form", StartVIRForm)
        latest_vir = self.get_latest_vir()
        if (
            latest_vir
            and latest_vir.request_status != VisaInformationRequest.RequestStatus.CLOSED
        ):
            context["add_comment_form"] = kwargs.get(
                "add_comment_form", AddVIRCommentForm
            )
        context["user_can_reopen_vir"] = (
            latest_vir
            and latest_vir.request_status == VisaInformationRequest.RequestStatus.CLOSED
            and self.user_action_allowed(
                group_types=[GroupType.DEV, GroupType.HOME_OFFICE]
            )
        )
        return context

    def form_invalid(self, form):
        if isinstance(form, StartVIRForm):
            context = self.get_context_data(start_vir_form=form)
        elif isinstance(form, AddVIRCommentForm):
            context = self.get_context_data(add_comment_form=form)
        else:
            context = self.get_context_data()
        return self.render_to_response(context)


class VIRTable(tables.Table):
    name = Column(accessor="visa_application__title", verbose_name="Name")
    local_authority = Column(
        accessor="visa_application__ltla_name", verbose_name="Local authority"
    )
    gwf = Column(
        accessor="visa_application__gwf", verbose_name="Global Web Form number (GWF)"
    )
    requested_at = CustomDateColumn(
        accessor="requested_at", verbose_name="VIR start date"
    )
    vir_status = Column(accessor="request_status", verbose_name="VIR status")
    visa_status = Column(
        accessor="visa_application__visa_status", verbose_name="Visa status"
    )

    def render_visa_status(self, value):
        return render_to_string(
            "webapp/components/visa_status_tag/visa_status_tag.html",
            {"visa_status": value},
        )

    def render_name(self, record, value):
        return format_html(
            (
                '<a class="govuk-body-s govuk-link"'
                'style="white-space: normal" href="{}">'
                "{}"
                "</a>"
            ),
            reverse(
                "visa-applications:detail-overview",
                args=[record.visa_application.visa_application_id],
            ),
            value,
        )

    def render_vir_status(self, record):
        value = record.request_status
        label = VisaInformationRequest.RequestStatus(value).label
        return render_to_string(
            "webapp/components/vir_status_tag/vir_status_tag.html",
            {"vir_status": value, "vir_status_label": label},
        )

    class Meta:
        template_name = "webapp/components/tables/table.html"
        fields = (
            "name",
            "local_authority",
            "gwf",
            "requested_at",
            "vir_status",
            "visa_status",
        )
        order_by = ("requested_at",)


class VIRFilter(FilterSet, FilterPanelMixin):
    search = CharFilter(
        label="Search",
        method="search_filter",
        help_text="Search the data in the table",
    )

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, VIR_SEARCH_FIELDS)

    request_status = MultipleChoiceFilter(
        choices=[(value.name, value.name) for value in vir_status_list],
        label="VIR status",
        widget=CheckboxSelectMultipleWithTags(
            label_to_tag_colour=vir_status_to_tag_colour
        ),
    )

    visa_application__visa_status = MultipleChoiceFilter(
        choices=[(value.name, value.name) for value in visa_status_list],
        label="Visa status",
        widget=CheckboxSelectMultipleWithTags(
            label_to_tag_colour=visa_status_to_tag_colour
        ),
    )

    requested_at = CustomDateFromToRangeFilter(
        label="",
        field_name="requested_at",
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

    ltla_name = LazyChoiceFilter(
        choices=lambda: [
            (ltla, ltla)
            for ltla in VisaInformationRequest.objects.get_queryset()
            .values_list("ltla_name", flat=True)
            .distinct()
            if ltla and len(ltla) > 0
        ],
        label="Local authority",
        empty_label="",
        lookup_expr="icontains",
        widget=SearchableSelect(),
    )

    def country_filter(self, queryset, _, value):
        if not value:
            return queryset

        filtered_ltlas = GroupInfo.objects.filter(
            group_type=GroupType.LOCAL_AUTHORITY, da_name__in=value
        ).values_list("ltla_name", flat=True)

        return queryset.filter(ltla_name__in=filtered_ltlas)

    country = MultipleChoiceFilter(
        choices=[
            ("England", "England"),
            ("Scotland", "Scotland"),
            ("Northern Ireland", "Northern Ireland"),
            ("Wales", "Wales"),
        ],
        label="Country",
        widget=CheckboxSelectMultiple(),
        method="country_filter",
    )

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
            Field(
                "request_status", context={"label_size": "govuk-fieldset__legend--m"}
            ),
            Field(
                "visa_application__visa_status",
                context={"label_size": "govuk-fieldset__legend--m"},
            ),
            Fieldset(
                "requested_at",
                legend="VIR start date",
                legend_size="m",
            ),
            Field(
                "ltla_name",
                context={"label_size": "govuk-fieldset__legend--m"},
            ),
            Field.checkboxes("country", small=True, legend_size=Size.MEDIUM),
        )
        return form

    class Meta:
        model = VisaInformationRequest
        fields = {
            "request_status",
            "visa_application__visa_status",
            "requested_at",
            "ltla_name",
        }


class VIRListView(PermissionsMixin, SingleTableMixin, FilterView):
    group_type = [
        GroupType.DEV,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
    ]
    model = VisaInformationRequest
    table_class = VIRTable
    filterset_class = VIRFilter
    template_name = "visa_applications/virs.html"
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}

    def get_queryset(self):
        fields_needed = [
            "requested_at",
            "request_status",
            "ltla_name",
            "visa_application__title",
            "visa_application__ltla_name",
            "visa_application__gwf",
            "visa_application__visa_status",
        ]
        return super().get_queryset().only(*fields_needed)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["has_virs"] = VisaInformationRequest.objects.get_for_user(self.request.user)
        ctx["user_can_start_vir"] = self.user_action_allowed(
            group_types=[
                GroupType.DEV,
                GroupType.HOME_OFFICE,
            ]
        )
        return ctx


class VIRCloseConfirmView(PermissionsMixin, SingleObjectMixin, FormView):
    group_type = [
        GroupType.DEV,
        GroupType.HOME_OFFICE,
    ]
    model = VisaApplication
    template_name = "visa_applications/detail_view/vir/vir_close_confirm.html"
    form_class = VIRCloseConfirmForm

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def get_success_url(self):
        return reverse("visa-applications:detail-vir", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["return_url"] = reverse(
            "visa-applications:detail-vir", args=[self.object.pk]
        )
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class()
        context = self.get_context_data(form=form, object=self.object)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(request.POST)
        if form.is_valid():
            if form.cleaned_data["confirm_close"]:
                vir = (
                    VisaInformationRequest.objects.is_open()
                    .filter(visa_application=self.object)
                    .order_by("-created_at")
                    .first()
                )
                if vir:
                    vir.request_status = VisaInformationRequest.RequestStatus.CLOSED
                    vir.closed_at = timezone.now()
                    vir.save(update_fields=["request_status", "closed_at"])
                    messages.success(
                        request, "You have closed this Visa Information Request."
                    )
            return redirect(self.get_success_url())
        context = self.get_context_data(form=form, object=self.object)
        return self.render_to_response(context)


class VIRReopenConfirmView(PermissionsMixin, SingleObjectMixin, FormView):
    group_type = [
        GroupType.DEV,
        GroupType.HOME_OFFICE,
    ]
    model = VisaApplication
    template_name = "visa_applications/detail_view/vir/vir_reopen_confirm.html"
    form_class = VIRReopenConfirmForm

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def get_success_url(self):
        return reverse("visa-applications:detail-vir", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["return_url"] = reverse(
            "visa-applications:detail-vir", args=[self.object.pk]
        )
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class()
        context = self.get_context_data(form=form, object=self.object)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(request.POST)
        if form.is_valid():
            if form.cleaned_data["confirm_reopen"]:
                vir = (
                    VisaInformationRequest.objects.filter(
                        visa_application=self.object,
                        request_status=VisaInformationRequest.RequestStatus.CLOSED,
                    )
                    .order_by("-created_at")
                    .first()
                )
                if vir:
                    vir.request_status = (
                        VisaInformationRequest.RequestStatus.AWAITING_UKVI
                    )
                    vir.closed_at = None
                    vir.save(update_fields=["request_status", "closed_at"])
                    messages.success(
                        request, "Visa Information Request has been re-opened."
                    )
            return redirect(self.get_success_url())
        context = self.get_context_data(form=form, object=self.object)
        return self.render_to_response(context)
