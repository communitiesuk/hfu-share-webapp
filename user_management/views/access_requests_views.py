import os
from datetime import datetime, timedelta

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Layout, Size
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.views.generic import FormView
from django_filters import (
    CharFilter,
    FilterSet,
    MultipleChoiceFilter,
)
from django_filters.views import FilterView
from django_tables2 import Column, LazyPaginator, SingleTableMixin, tables
from formtools.wizard.views import SessionWizardView

from accounts.enums import GroupType
from accounts.mixins import AdminAccessRequiredMixin
from accounts.models import AccessRequest, GroupInfo
from accounts.models.User import User
from user_management.templatetags.access_request_extras import (
    access_request_status_label_to_tag_colour,
    render_name_label_from_group_info,
)
from user_management.views.form_wizard_views import ACCESS_REQUEST_FORM_BREADCRUMBS
from webapp.constants import ACCESS_REQUEST_SEARCH_FIELDS
from webapp.mixins import FilterPanelMixin, PIISafeRecordNameMixin, UserActionsMixin
from webapp.search import perform_search
from webapp.utils import CustomDateFromToRangeFilter, CustomDateTimeColumn
from webapp.views import SummaryListRow, SummaryListView
from webapp.widgets import CheckboxSelectMultipleWithTags, DatePicker, StackedRangeInput


class AccessRequestsTable(tables.Table):
    requester = Column(verbose_name="Name")
    group_type = Column(verbose_name="User group")
    group_info = Column(
        verbose_name="Location group",
        order_by="group_info__group__name",
    )
    justification = Column(verbose_name="Why access is required")
    created_at = CustomDateTimeColumn(
        verbose_name="Request date", attrs={"td": {"style": "white-space: nowrap;"}}
    )
    status = Column(verbose_name="Status")

    def render_requester(self, record: AccessRequest):
        if record.requester.first_name and record.requester.last_name:
            return format_html(
                '<div style="white-space: nowrap">'
                '<a class="govuk-link" href="{}">{} {}</a></div>'
                "<div>({})</div>",
                reverse(
                    "user-management:access-request-details",
                    args=[record.reference_number],
                ),
                record.requester.first_name,
                record.requester.last_name,
                record.requester.email,
            )

        return format_html(
            '<a class="govuk-link" href="{url}">{value}</a>',
            url=reverse(
                "user-management:access-request-details", args=[record.reference_number]
            ),
            value=record.requester.email,
        )

    def render_status(self, record: AccessRequest):
        return render_to_string(
            "webapp/components/access_request/access_request_status_tag.html",
            {"status": AccessRequest.Status(record.status)},
        )

    def render_group_type(self, record: AccessRequest):
        group_type = GroupType(record.group_type)
        if group_type == GroupType.DEVOLVED_ADMINISTRATION:
            return (
                f"{group_type.label} - "
                f"{AccessRequest.DaGroupType(record.da_group_type).label}"
            )
        return group_type.label

    def render_group_info(self, value):
        if value.group_type in [
            GroupType.DEVOLVED_ADMINISTRATION,
            GroupType.LOCAL_AUTHORITY,
        ]:
            return render_name_label_from_group_info(value)
        return ""

    class Meta:
        model = AccessRequest
        template_name = "webapp/components/tables/table.html"
        fields = (
            "requester",
            "group_type",
            "group_info",
            "justification",
            "created_at",
            "status",
        )


class AccessRequestsFilter(FilterSet, FilterPanelMixin):
    created_at = CustomDateFromToRangeFilter(
        label="Request date",
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

    status = MultipleChoiceFilter(
        choices=AccessRequest.Status.choices,
        widget=CheckboxSelectMultipleWithTags(
            label_to_tag_colour=access_request_status_label_to_tag_colour
        ),
    )

    search = CharFilter(
        label="Search",
        method="search_filter",
        help_text="Search the data in the table",
    )

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, ACCESS_REQUEST_SEARCH_FIELDS)

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
            Field(
                "created_at",
                context={"legend_size": "govuk-fieldset__legend--m"},
            ),
            Field(
                "status",
                context={"label_size": "govuk-fieldset__legend--m"},
            ),
        )

        return form

    class Meta:
        model = AccessRequest
        fields = ["search", "created_at", "status"]


class AccessRequestsListView(AdminAccessRequiredMixin, SingleTableMixin, FilterView):
    model = AccessRequest
    table_class = AccessRequestsTable
    filterset_class = AccessRequestsFilter
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    paginator_class = LazyPaginator
    template_name = "user_management/access_requests/access_requests_list_page.html"


class AccessRequestsDetailsPage(
    PIISafeRecordNameMixin,
    UserActionsMixin,
    AdminAccessRequiredMixin,
    SessionWizardView,
):
    model = AccessRequest
    template_name = "user_management/access_requests/access_request_details_page.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.object = self.get_object()

    def get_object(self):
        return AccessRequest.objects.get(pk=self.kwargs["pk"])

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        access_request = self.get_object()
        context["status_pending"] = (
            access_request.status == AccessRequest.Status.PENDING
        )
        context["title"] = (
            "Review access request"
            if access_request.status == AccessRequest.Status.PENDING
            else "Read access request"
        )

        group_type = GroupType(access_request.group_type)
        group_info = access_request.group_info
        request_summary = {
            "status": {
                "question": "Status",
                "answer": render_to_string(
                    "webapp/components/access_request/access_request_status_tag.html",
                    {"status": AccessRequest.Status(access_request.status)},
                ),
            },
            "request_date": {
                "question": "Request date",
                "answer": access_request.created_at.date(),
            },
            "requester": {
                "question": "Name",
                "answer": access_request.requester.full_name_or_email,
            },
            "group_type": {
                "question": (
                    "Choose level of permissions"
                    if group_type in [GroupType.MHCLG, GroupType.SERVICE_SUPPORT]
                    else "User group"
                ),
                "answer": (access_request.group_type_label()),
            },
            "group_info": {
                "question": "Country group" if group_info.is_da else "Local authority",
                "answer": render_name_label_from_group_info(access_request.group_info),
            },
            "justification": {
                "question": "Tell us why access is needed",
                "answer": access_request.justification,
            },
        }

        review_summary = {}

        if access_request.status == AccessRequest.Status.PENDING:
            request_summary.pop("status")

        if group_type in [
            GroupType.HOME_OFFICE,
            GroupType.MHCLG,
            GroupType.SERVICE_SUPPORT,
        ]:
            request_summary.pop("group_info")

        if access_request.status == AccessRequest.Status.APPROVED:
            review_summary.update(
                {
                    "approved_date": {
                        "question": "Approved date",
                        "answer": access_request.reviewed_at.date(),
                    },
                    "approved_by": {
                        "question": "Approved by",
                        "answer": access_request.reviewer.full_name_or_email,
                    },
                }
            )

        if access_request.status == AccessRequest.Status.REJECTED:
            review_summary.update(
                {
                    "rejected_date": {
                        "question": "Rejected date",
                        "answer": access_request.reviewed_at.date(),
                    },
                    "rejected_by": {
                        "question": "Rejected by",
                        "answer": access_request.reviewer.full_name_or_email,
                    },
                    "rejection_justification": {
                        "question": "Reason rejected",
                        "answer": access_request.rejection_justification,
                    },
                }
            )

        context["access_request_summary"] = request_summary
        context["access_review_summary"] = review_summary
        return context

    def done(self, form_list, **kwargs):
        data = self.get_all_cleaned_data()

        approval_status = data.get("approval_status")
        rejection_justification = data.get("rejection_justification", None)

        access_request = self.get_object()

        access_request.reviewer = self.request.user
        access_request.status = AccessRequest.Status[approval_status]
        access_request.rejection_justification = rejection_justification
        access_request.reviewed_at = timezone.now()

        if approval_status == AccessRequest.Status.APPROVED:
            requester = access_request.requester
            group = access_request.group_info.group
            requester.groups.add(group)

        access_request.save()

        url = reverse("user-management:access-requests")
        return redirect(f"{url}?status=PENDING&sort=-created_at")


class AccessRequestYourRequestView(UserActionsMixin, SummaryListView):
    # pylint: disable=view-missing-access-control
    template_name = (
        "user_management/access_requests/access_requests_your_request_page.html"
    )
    model = AccessRequest

    created_at = SummaryListRow(verbose_name="Request date")
    requester__first_name = SummaryListRow(verbose_name="Name")
    group_info = SummaryListRow(verbose_name="Local Authority")
    justification = SummaryListRow(verbose_name="Tell us why access is needed")
    group_type = SummaryListRow(verbose_name="User group")
    rejection_justification = SummaryListRow(verbose_name="Reason for rejections")

    def render_requester__first_name(self, record: AccessRequest):
        return User.objects.get(pk=record.requester.pk).full_name_or_email

    def render_group_info(self, value: GroupInfo):
        return render_name_label_from_group_info(value)

    def render_group_type(self, record: AccessRequest):
        return record.group_type_label()

    def get_queryset(self):
        return AccessRequest.objects.filter(requester=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = ACCESS_REQUEST_FORM_BREADCRUMBS.get("your_request")
        return context

    def get_fields(self):
        fields = None
        if self.object.group_type == GroupType.LOCAL_AUTHORITY:
            self.group_info.verbose_name = "Local Authority"
            self.group_type.verbose_name = "User group"
            fields = [
                "created_at",
                "requester__first_name",
                "group_info",
                "justification",
            ]
        elif self.object.group_type == GroupType.DEVOLVED_ADMINISTRATION:
            if self.object.da_group_type == AccessRequest.DaGroupType.CENTRAL_USER:
                self.group_info.verbose_name = "Country group"
                self.group_type.verbose_name = "User group"
                fields = [
                    "created_at",
                    "requester__first_name",
                    "group_type",
                    "group_info",
                    "justification",
                ]
            if self.object.da_group_type == AccessRequest.DaGroupType.LOCAL_AUTHORITY:
                self.group_info.verbose_name = "Local Authority"
                self.group_type.verbose_name = "User group"
                fields = [
                    "created_at",
                    "requester__first_name",
                    "group_type",
                    "group_info",
                    "justification",
                ]
        elif self.object.group_type == GroupType.MHCLG:
            self.group_info.verbose_name = "Local Authority"
            self.group_type.verbose_name = "Choose level of permissions"
            fields = [
                "created_at",
                "requester__first_name",
                "group_type",
                "justification",
            ]
        elif self.object.group_type == GroupType.SERVICE_SUPPORT:
            self.group_info.verbose_name = "Local Authority"
            self.group_type.verbose_name = "Choose level of permissions"
            fields = [
                "created_at",
                "requester__first_name",
                "group_type",
                "justification",
            ]
        elif self.object.group_type == GroupType.HOME_OFFICE:
            self.group_info.verbose_name = "Local Authority"
            self.group_type.verbose_name = "User group"
            fields = [
                "created_at",
                "requester__first_name",
                "group_type",
                "justification",
            ]

        if fields is None:
            raise NotImplementedError(
                f"No match for AccessRequestYourRequestView for access request"
                f" with group_type {self.object.group_type} and "
                f"da_group_type {self.object.da_group_type}"
            )

        if self.object.status == AccessRequest.Status.REJECTED:
            fields += ["rejection_justification"]

        return fields


class AccessRequestHideRequest(FormView):
    # pylint: disable=view-missing-access-control
    model = AccessRequest
    form_class = None

    def post(self, request, *args, **kwargs):
        request_to_hide = get_object_or_404(
            AccessRequest, pk=kwargs["pk"], requester=request.user
        )

        if request_to_hide.status == AccessRequest.Status.PENDING:
            return HttpResponse(status=409)

        AccessRequest.set_hidden_by_requester(request_to_hide.reference_number)
        return redirect(reverse("webapp:landing-page"))
