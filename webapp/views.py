import inspect
import logging
import os
from dataclasses import dataclass
from functools import reduce
from typing import Any

import django_filters
from django.contrib.auth.decorators import login_not_required
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db.models import ForeignKey, Manager, TextField
from django.forms import TextInput
from django.forms.widgets import CheckboxSelectMultiple
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.middleware.csrf import get_token
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, TemplateView
from django_filters import FilterSet, MultipleChoiceFilter
from django_tables2 import (
    Column,
    MultiTableMixin,
    tables,
)

from accounts.enums import GroupType
from accounts.models import AccessRequest
from ontology.models import (
    MvAccommodationRequest,
    ReassignmentRequest,
    VisaApplication,
    VisaInformationRequest,
)
from ontology.utils import LinkedRecordData
from user_management.templatetags.access_request_extras import (
    render_name_label_from_group_info,
)
from webapp.constants import (
    ACCESS_REQUEST_TABLE_COLUMN_ATTRS,
    UNASSIGNED_ACCOMMODATION_REQUESTS_ALLOWED_GROUP_TYPES,
    VisaStatus,
    no_visa_status,
    visa_status_by_name,
    visa_status_some_issued,
)
from webapp.mixins import (
    UserActionsMixin,
)
from webapp.utils import (
    CustomDateTimeColumn,
)

logger = logging.getLogger(__name__)


@login_not_required
def favicon_redirect(request: HttpRequest):
    return HttpResponseRedirect(
        staticfiles_storage.url("gds/assets/images/favicon.ico")
    )


def combine_visa_statuses(status_names: list[str]) -> VisaStatus:
    statuses = [
        visa_status_by_name[name]
        for name in status_names
        if name in visa_status_by_name
    ]
    if not statuses:
        return no_visa_status
    if len(statuses) == 1:
        # Only one
        return statuses[0]
    if all(status.id == statuses[0].id for status in statuses):
        # All the same
        return statuses[0]
    if any(status.id == 2 for status in statuses):
        # At least one (but not all) issued
        return visa_status_some_issued
    # else return max ID
    return sorted(statuses, key=lambda status: status.id, reverse=True)[0]


class ExampleTable(tables.Table):
    Q44g_full_name = Column(verbose_name="Accommodation request")

    def render_visa_status(self, value):
        return format_html(
            '<strong class="govuk-tag govuk-tag--{}">{}</strong>',
            "green" if value == "Issued" else "red",
            value,
        )

    class Meta:
        model = VisaApplication
        template_name = "webapp/components/tables/table.html"
        fields = (
            "Q44g_full_name",
            "country",
            "applicant_final_address",
            "ingestion_time",
            "visa_status",
        )


class ExampleTableFilter(FilterSet):
    visa_status = MultipleChoiceFilter(
        choices=(
            ("Issued", "Issued"),
            ("Withdrawn", "Withdrawn"),
            ("Lapsed", "Lapsed"),
            ("Pending", "Pending"),
        ),
        label="Visa application status",
        widget=CheckboxSelectMultiple(attrs={"class": "govuk-checkboxes__input"}),
    )

    class Meta:
        model = VisaApplication
        fields = {
            "country": ["icontains"],
        }
        filter_overrides = {
            TextField: {
                "filter_class": django_filters.CharFilter,
                "extra": lambda f: {
                    "widget": TextInput(
                        attrs={"placeholder": "Country", "class": "govuk-input"}
                    )
                },
            },
        }


class PendingAccessRequestsTable(tables.Table):
    group_info = Column(
        verbose_name="Request",
        attrs=ACCESS_REQUEST_TABLE_COLUMN_ATTRS,
    )
    created_at = CustomDateTimeColumn(
        verbose_name="Date of request",
        attrs=ACCESS_REQUEST_TABLE_COLUMN_ATTRS,
    )

    def render_group_info(self, value, record):
        return format_html(
            '<a class="govuk-link govuk-link--no-visited-state" href={}>{}</a>',
            reverse("user-management:access-request-your-request", args=[record.pk]),
            render_name_label_from_group_info(value),
        )

    class Meta:
        model = AccessRequest
        template_name = "webapp/components/tables/table.html"
        fields = ("group_info", "created_at", "justification")
        empty_text = "You have no pending requests"


class RejectedAccessRequestsTable(tables.Table):
    group_info = Column(
        verbose_name="Request",
        attrs=ACCESS_REQUEST_TABLE_COLUMN_ATTRS,
    )
    created_at = CustomDateTimeColumn(
        verbose_name="Date of request",
        attrs=ACCESS_REQUEST_TABLE_COLUMN_ATTRS,
    )
    rejection_justification = Column(verbose_name="Reason")
    remove = Column(
        verbose_name="Actions",
        orderable=False,
        empty_values=(),
        attrs={
            "th": {"visually_hidden_header": True},
            "td": {"style": "text-align: right;"},
        },
    )

    def render_group_info(self, value, record):
        return format_html(
            '<a class="govuk-link govuk-link--no-visited-state" href={}>{}</a>',
            reverse("user-management:access-request-your-request", args=[record.pk]),
            render_name_label_from_group_info(value),
        )

    def render_remove(self, record):
        csrf_token = getattr(self, "csrf_token", "")
        action_url = reverse(
            "user-management:hide-access-request", kwargs={"pk": record.pk}
        )

        return format_html(
            '<form method="post" action={action_url} style="display: inline;">'
            '<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">'
            '<button type="submit" class="govuk-link govuk-link--no-visited-state">'
            "Remove"
            "</button>"
            "</form>",
            action_url=action_url,
            csrf_token=csrf_token,
        )

    class Meta:
        model = AccessRequest
        template_name = "webapp/components/tables/table.html"
        fields = ("group_info", "created_at", "rejection_justification")
        empty_text = "You have no rejected requests"


class ApprovedAccessRequestsTable(tables.Table):
    group_info = Column(
        verbose_name="Request",
        attrs=ACCESS_REQUEST_TABLE_COLUMN_ATTRS,
    )
    created_at = CustomDateTimeColumn(
        verbose_name="Date of request",
        attrs=ACCESS_REQUEST_TABLE_COLUMN_ATTRS,
    )

    def render_group_info(self, value, record):
        return format_html(
            '<a class="govuk-link govuk-link--no-visited-state" href={}>{}</a>',
            reverse("user-management:access-request-your-request", args=[record.pk]),
            render_name_label_from_group_info(value),
        )

    class Meta:
        model = AccessRequest
        template_name = "webapp/components/tables/table.html"
        fields = ("group_info", "created_at")
        empty_text = "You have no approved requests"


class LandingPageView(UserActionsMixin, MultiTableMixin, TemplateView):
    # pylint: disable=view-missing-access-control

    template_name = "webapp/pages/landing_page/landing_page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        csrf_token = get_token(self.request)
        table_instances = self.get_tables()
        for table in table_instances:
            if hasattr(table, "render_remove"):
                table.csrf_token = csrf_token

        context["tables"] = table_instances
        user_groups = self.request.user.groups.values_list(
            "groupinfo__group_type", flat=True
        )
        if GroupType.MHCLG in user_groups:
            context["pending_virs"] = VisaInformationRequest.objects.filter(
                request_status__in=[
                    VisaInformationRequest.RequestStatus.AWAITING_LA,
                    VisaInformationRequest.RequestStatus.AWAITING_UKVI,
                ]
            ).count()
        elif GroupType.HOME_OFFICE in user_groups:
            context["pending_virs"] = VisaInformationRequest.objects.filter(
                request_status=VisaInformationRequest.RequestStatus.AWAITING_UKVI,
            ).count()
        elif GroupType.LOCAL_AUTHORITY in user_groups:
            context["pending_virs"] = (
                VisaInformationRequest.objects.get_for_user(self.request.user)
                .filter(
                    request_status=VisaInformationRequest.RequestStatus.AWAITING_LA,
                )
                .count()
            )
        else:
            context["pending_virs"] = None

        context["pending_reassignments"] = (
            ReassignmentRequest.received.get_for_user(self.request.user)
            .filter(
                outcome=ReassignmentRequest.Outcome.PENDING,
            )
            .count()
            if GroupType.LOCAL_AUTHORITY in user_groups
            else None
        )

        context["unassigned_accommodation_requests_count"] = (
            MvAccommodationRequest.objects.unassigned().not_hidden().count()
            if set(user_groups) & UNASSIGNED_ACCOMMODATION_REQUESTS_ALLOWED_GROUP_TYPES
            else None
        )

        # TEMP: Set show_guests_option for use in fix deduplication title
        context["show_guests_option"] = self.request.user.groups.filter(
            name="dev"
        ).exists()

        return context

    def get_tables(self):
        pending_sort = self.request.GET.get("pending-sort") or "-created_at"
        rejected_sort = self.request.GET.get("rejected-sort") or "-created_at"
        approved_sort = self.request.GET.get("approved-sort") or "-created_at"

        table_pending = PendingAccessRequestsTable(
            AccessRequest.objects.filter(
                status__in=[AccessRequest.Status.PENDING],
                requester=self.request.user,
            ).order_by(pending_sort),
            prefix="pending-",
        )
        table_rejected = RejectedAccessRequestsTable(
            AccessRequest.objects.filter(
                status__in=[AccessRequest.Status.REJECTED],
                requester=self.request.user,
                hidden_by_requester=False,
            ).order_by(rejected_sort),
            prefix="rejected-",
        )
        table_approved = ApprovedAccessRequestsTable(
            AccessRequest.objects.filter(
                status__in=[AccessRequest.Status.APPROVED],
                requester=self.request.user,
                access_revoked=False,
            ).order_by(approved_sort),
            prefix="approved-",
        )

        table_pending.paginate(
            page=self.request.GET.get("pending-page", 1),
            per_page=os.environ.get("PAGINATION_PAGE_SIZE"),
        )
        table_rejected.paginate(
            page=self.request.GET.get("rejected-page", 1),
            per_page=os.environ.get("PAGINATION_PAGE_SIZE"),
        )
        table_approved.paginate(
            page=self.request.GET.get("approved-page", 1),
            per_page=os.environ.get("PAGINATION_PAGE_SIZE"),
        )

        return [table_pending, table_rejected, table_approved]


class AccessibilityStatementView(TemplateView):
    # pylint: disable=view-missing-access-control
    template_name = "webapp/pages/accessibility_statement/accessibility_statement.html"


class CookiesView(TemplateView):
    # pylint: disable=view-missing-access-control
    template_name = "webapp/pages/cookies/cookies.html"


@dataclass
class SummaryListRow:
    verbose_name: str


class SummaryListLink:
    """Adds a link in a summary list that's not associated directly to a model"""

    def __init__(self, view_name: str, object_id: Any, title: str):
        self.data = LinkedRecordData(view_name, object_id, title)

    def display_link_data(self, *args, **kwargs):
        return self.data


class SummaryListViewBase(DetailView):
    # pylint: disable=view-missing-access-control
    Meta: object

    def build_name_value_pairs(self, fields):
        label_overrides = self.get_meta_attr("label_overrides")
        result = []

        for full_field_name in fields:
            split_field_name = full_field_name.split("__")
            field, _model = self._get_field_and_model(split_field_name)
            if hasattr(field, "verbose_name"):
                value = self._compute_field_value(field, split_field_name)

                if label_overrides and full_field_name in label_overrides:
                    name = label_overrides[full_field_name]
                else:
                    name = self._compute_field_name(split_field_name, full_field_name)
                result.append((name, value))

        return result

    def _get_field_and_model(self, split_field_name: list[str], model=None):
        field_name = split_field_name[0]
        potential_field = getattr(model or self.model, field_name)
        if hasattr(potential_field, "field"):
            field = potential_field.field
            model = field.related_model
        if hasattr(potential_field, "related"):
            field = potential_field.related.field
            model = potential_field.related.related_model
        if len(split_field_name) > 1:
            return self._get_field_and_model(split_field_name[1:], model)
        return field, model

    def _compute_field_value(self, field, split_field_name):
        field_name = "__".join(split_field_name)
        value = reduce(
            getattr,
            split_field_name,
            self.object,
        )

        if value is None:
            return None

        if hasattr(self, f"render_{field_name}"):
            return self._use_render_override(field_name, value)

        if hasattr(self.object, f"get_{field_name}_display"):
            return getattr(self.object, f"get_{field_name}_display")()

        if isinstance(value, Manager):
            related_objects = value.all()
            value = (
                [obj.pk for obj in related_objects]
                if len(related_objects) > 0
                else None
            )
            return value

        is_immediate_foreign_key = (
            value is not None
            and isinstance(field, ForeignKey)
            and len(split_field_name) == 1
        )
        if is_immediate_foreign_key:
            if field.one_to_one or field.many_to_one:
                return value.pk
        return value

    def _use_render_override(self, field_name, value):
        render_function = getattr(self, f"render_{field_name}")
        parameters = list(inspect.signature(render_function).parameters.keys())
        render_kwargs = {}
        if "value" in parameters:
            render_kwargs["value"] = value
        if "record" in parameters:
            render_kwargs["record"] = self.object
        value = getattr(self, f"render_{field_name}")(**render_kwargs)
        return value

    def _compute_field_name(self, split_field_name, full_field_name):
        name = []
        current_model = self.model
        for linked_field in split_field_name:
            current_field, current_model = self._get_field_and_model(
                [linked_field], current_model
            )
            if not hasattr(current_field, "verbose_name"):
                break
            name += [
                current_field.verbose_name[0].upper() + current_field.verbose_name[1:]
            ]
        name = ", ".join(name)

        if hasattr(self, full_field_name):
            summary_list_row = getattr(self, full_field_name)
            if hasattr(summary_list_row, "verbose_name"):
                name = summary_list_row.verbose_name
        return name

    def get_sorted_fields_from_model(self):
        exclude_fields = self.get_meta_attr("exclude_fields") or []
        return [
            getattr(field, "accessor_name", field.name)
            for field in sorted(
                filter(
                    lambda field: field.name not in exclude_fields
                    and not field.is_relation,
                    self.model._meta.get_fields(),
                ),
                key=lambda f: getattr(f, "verbose_name", f.name).lower(),
            )
        ]

    def get_meta_attr(self, key):
        return getattr(getattr(self, "Meta", None), key, None)

    def get_all_fields(self):
        if hasattr(self, "get_fields"):
            return self.get_fields()
        return self.get_meta_attr("fields") or self.get_sorted_fields_from_model()


class SummaryListView(SummaryListViewBase):
    # pylint: disable=view-missing-access-control
    """
    For use with the record_summary_list,
    Pass list of fields in Meta.fields,
    by default shows all fields in model alphabetically
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fields"] = self.build_name_value_pairs(self.get_all_fields())
        return context


class TwoColumnSummaryListView(SummaryListViewBase):
    # pylint: disable=view-missing-access-control
    """
    Either specify left_fields and right_fields on the Meta class
    or this will take the fields list and split the fields list in half
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        left_fields = self.get_meta_attr("left_fields")
        right_fields = self.get_meta_attr("right_fields")
        split_columns_at_field = self.get_meta_attr("split_columns_at_field")

        if not (left_fields and right_fields):
            all_fields = self.get_all_fields()
            if split_columns_at_field and split_columns_at_field in all_fields:
                split_index = all_fields.index(split_columns_at_field)
                left = self.build_name_value_pairs(all_fields[:split_index])
                right = self.build_name_value_pairs(all_fields[split_index:])
                context["left_fields"] = left
                context["right_fields"] = right
            else:
                name_value_pairs = self.build_name_value_pairs(all_fields)
                left, right = self._split_name_value_pairs(name_value_pairs)
                context["left_fields"] = left
                context["right_fields"] = right
        else:
            context["left_fields"] = self.build_name_value_pairs(left_fields)
            context["right_fields"] = self.build_name_value_pairs(right_fields)

        return context

    def _split_name_value_pairs(self, name_value_pairs):
        def estimate_lines(value):
            if value is None or value == "" or value == []:
                return 1
            if isinstance(value, str):
                return 1 + value.count("\n")
            if isinstance(value, list):
                return sum(estimate_lines(v) for v in value) or 1
            return 1

        line_counts = [estimate_lines(value) for _, value in name_value_pairs]
        total = sum(line_counts)
        best_split = 0
        min_diff = float("inf")
        left_sum = 0

        for i in range(1, len(name_value_pairs)):
            left_sum += line_counts[i - 1]
            right_sum = total - left_sum
            diff = abs(left_sum - right_sum)
            if diff < min_diff:
                min_diff = diff
                best_split = i

        left = name_value_pairs[:best_split]
        right = name_value_pairs[best_split:]
        return left, right


@dataclass
class Action:
    """
    Base action for use with ActionsListView
    """

    label: str
    value: str | None = None
    content: str | None = None


@dataclass
class LinkAction(Action):
    """
    For use with ActionsListView, represents an action with a label, text
    and clickable link
    """

    def __init__(
        self,
        label: str,
        url: str | None = None,
        url_text: str | None = None,
        text: str | None = None,
    ):
        super().__init__(
            label=label,
            value=format_html(
                '<a href="{url}" class="govuk-link--no-visited-state">{url_text}</a>',
                url=url,
                url_text=url_text,
            )
            if url
            else "",
            content=text,
        )


@dataclass
class TagAction(Action):
    """
    For use with ActionsListView, represents a (disabled) action with a tag indicator.
    """

    def __init__(
        self, label: str, tag_text: str, tag_colour_class: str = "govuk-tag--grey"
    ):
        super().__init__(
            label=label,
            value=format_html(
                '<strong class="govuk-tag {tag_colour_class}" style="max-width: 100%">'
                "{tag_text}"
                "</strong>",
                tag_colour_class=tag_colour_class,
                tag_text=tag_text,
            ),
        )


class ActionsListView(DetailView):
    # pylint: disable=view-missing-access-control
    """
    For use with the record_action_list,
    Pass list of actions in context.
    Each action should have a label, action name and a link.
    By default, renders an empty list of actions.
    """

    def get_actions(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} has no get_actions method "
            f"but is subclassing ActionsListView"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["actions"] = self.get_actions()
        return context


@method_decorator(csrf_exempt, name="dispatch")
class CSPReportView(View):
    """
    This view is only used if SENTRY_CSP_REPORT_URI environment var is not configured.
    """

    # pylint: disable=view-missing-access-control
    def post(self, request):
        # Log the CSP report
        logger.warning("CSP Violation: %s", request.body.decode())

        return HttpResponse(status=204)  # No Content

    def get(self, request):
        # Should always be a POST request
        return HttpResponse(status=405)
