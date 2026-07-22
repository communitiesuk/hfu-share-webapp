import re
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone as dt_timezone
from typing import Any, Optional, Protocol, Set, cast

from auditlog.models import LogEntry
from dateutil import parser
from dateutil.parser import ParserError
from dateutil.tz import gettz
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Field, Model, OuterRef, QuerySet, Subquery
from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.datastructures import MultiValueDict
from django.utils.html import format_html, format_html_join
from django_filters import MultipleChoiceFilter

from accounts.enums import GroupType
from accounts.mixins import GroupRequiredMixin
from case_management.settings import FILE_DOWNLOAD_S3_BUCKET_NAME
from deduplication.models import (
    AccommodationDuplicateGroup,
    GuestDuplicateGroup,
    SponsorDuplicateGroup,
)
from ontology.models import (
    Announcement,
    MvAccommodation,
    MvAccommodationRequest,
    MvInteraction,
    MvInteractionAttachmentMetadata,
    MvPerson,
    MvVolunteer,
)
from webapp.constants import AUDIT_EVENT_TYPE_ACTION
from webapp.s3 import s3_file_exists
from webapp.templatetags.timeline_extras import (
    AuditEventType,
    TimelineEventType,
    format_interaction_content,
)

NONE_TYPES = {None, "None", "", "None None", "[]"}
GO_LIVE_CUTOFF = datetime(2025, 9, 15, tzinfo=dt_timezone.utc)


class LocalAuthorityAccessMixinGetObjectProtocol(Protocol):
    def get_object(self, queryset: QuerySet | None = None) -> Model:
        return Model()

    def get_queryset(self) -> QuerySet:
        return QuerySet()


class LocalAuthorityAccessMixin:
    """
    A mixin to ensure the logged-in user only accesses objects in their group.
    """

    request: HttpRequest
    model: type[Model]

    def _raise_not_implemented(self, name, method):
        raise NotImplementedError(f"{name} must have a {method} method.")

    def get_queryset(self):
        model = self.model or super().get_queryset().model
        return model.objects.get_for_user(self.request.user)

    def get_object(
        self: LocalAuthorityAccessMixinGetObjectProtocol,
        queryset: QuerySet | None = None,
    ):
        return super().get_object(self.get_queryset())


@dataclass
class Filter:
    name: str
    options: list[tuple[str, str]]


class FilterPanelMixin:
    """
    A mixin for FilterSets to add functionality to the filters panel.
    """

    request: HttpRequest
    base_filters: Any

    @property
    def show_filters_panel(self):
        return self.request.GET.get("show_filters_panel") is not None

    @property
    def show_selected_filters_section(self):
        return len(self.applied_filters) > 0

    @property
    def clear_filters_link(self):
        url_without_query_params = self.request.get_full_path().split("?")[0]
        query_params_without_filter_params = self.request.GET.copy()

        for param in self.request.GET:
            if param in self.base_filters or (
                self.__is_a_subwidget(param)
                and self.__get_subwidget_filter_base_name(param) in self.base_filters
            ):
                del query_params_without_filter_params[param]

        return (
            url_without_query_params
            + "?"
            + query_params_without_filter_params.urlencode()
        )

    @property
    def applied_filters(self):
        filter_params = self.__get_filter_params_from_request(self.request.GET)

        applied_filters: list[Filter] = []

        for filter_name, applied_options in filter_params.lists():
            filter_label = self.__get_filter_label(filter_name)

            applied_options_with_remove_urls = (
                self.__get_filter_applied_options_with_remove_urls(
                    applied_options, filter_name
                )
            )

            applied_filters.append(
                Filter(name=filter_label, options=applied_options_with_remove_urls)
            )
        return applied_filters

    def __get_filter_params_from_request(self, request: QueryDict) -> MultiValueDict:
        filter_params: MultiValueDict = MultiValueDict()

        for name, values in request.lists():
            if name not in self.base_filters and not (
                self.__is_a_subwidget(name)
                and self.__get_subwidget_filter_base_name(name) in self.base_filters
            ):
                continue

            options = [option for option in values if option != ""]
            if len(options) == 0:
                continue

            filter_params.setlist(name, options)

        return filter_params

    def __get_filter_applied_options_with_remove_urls(
        self, applied_options: list[str], filter_name: str
    ) -> list[tuple[str, str]]:
        applied_options_with_remove_urls = []
        for option in applied_options:
            remove_filter_option_url = self.__get_remove_filter_option_url(
                applied_options, filter_name, option
            )
            applied_options_with_remove_urls.append(
                (self.__get_option_label(filter_name, option), remove_filter_option_url)
            )
        return applied_options_with_remove_urls

    def __get_remove_filter_option_url(
        self, applied_options: list[str], filter_name: str, option: str
    ) -> str:
        query_params_with_option_removed = self.request.GET.copy()
        query_params_with_option_removed.setlist(
            filter_name,
            [
                selected_option
                for selected_option in applied_options
                if selected_option != option
            ],
        )
        url_without_query_params = self.request.get_full_path().split("?")[0]
        remove_filter_link = (
            url_without_query_params
            + "?"
            + query_params_with_option_removed.urlencode()
        )
        return remove_filter_link

    def __parse_filter_name(self, filter_name: str) -> tuple[str, str]:
        split_filter_name = filter_name.split("_")
        base_filter_name = "_".join(split_filter_name[:-1])
        filter_sub_index = split_filter_name[-1]

        return base_filter_name, filter_sub_index

    def __is_a_subwidget(self, filter_name: str) -> bool:
        return filter_name[-1].isdigit()

    def __is_a_multiple_choice_filter(self, filter_name: str) -> bool:
        if filter_name not in self.base_filters:
            return False

        if self.__is_a_subwidget(filter_name):
            return False
        return isinstance(self.base_filters[filter_name], MultipleChoiceFilter)

    def __get_subwidget_filter_base_name(self, filter_name: str) -> str:
        return "_".join(filter_name.split("_")[:-1])

    def __get_filter_label(self, filter_name: str) -> str:
        if self.__is_a_subwidget(filter_name):
            base_filter_name, filter_sub_index = self.__parse_filter_name(filter_name)
            filter_label = self.base_filters[base_filter_name].label
            if filter_sub_index == "0":
                filter_label += " from"
            elif filter_sub_index == "1":
                filter_label += " to"

            return filter_label
        return (
            self.base_filters[filter_name].label
            if self.base_filters[filter_name].label
            else self.base_filters[filter_name].field_name.replace("_", " ").title()
        )

    def __get_option_label(self, filter_name: str, option_name: str) -> str:
        if self.__is_a_multiple_choice_filter(filter_name):
            multi_choice_filter = self.base_filters[filter_name]
            if option_name == multi_choice_filter.null_value:
                return multi_choice_filter.extra["null_label"]
            lookup_choices = multi_choice_filter.extra["choices"]
            if callable(lookup_choices):
                lookup_choices = lookup_choices()
            return next(
                choice for choice in lookup_choices if choice[0] == option_name
            )[1]

        return option_name


class ReadOnlyFieldsMixin:
    """
    A mixin that provides a reusable method for rendering read-only fields in forms.
    Displays 'Yes'/'No' for boolean values.
    """

    def render_readonly_field(self, label, field_name):
        value = getattr(self.instance, field_name, None)
        if isinstance(value, bool):
            value = "Yes" if value else "No"
        return render_to_string(
            "webapp/components/forms/readonly_form_field.html",
            {"label": label, "value": value},
        )


class UserUtilitiesMixin:
    def _get_user_group_types(self, user: Optional[object] = None) -> Set:
        """
        Returns a set of group types for the given user.
        If no user is provided, uses self.request.user.
        """
        if user is None:
            user = getattr(self, "request", None)
            if user is not None:
                user = getattr(user, "user", user)
        if hasattr(user, "groups"):
            return set(user.groups.values_list("groupinfo__group_type", flat=True))
        return set()


class UserActionsMixin(UserUtilitiesMixin):
    """
    Mixin for controlling user action permissions (edit/download) by group type.

    Usage:
    - user_can_edit(group_types, mode) / user_can_download(group_types, mode):
      Returns True if user can perform the action.
    - group_types: Single or iterable of group types. If None/empty, allows all.
    - mode: ALLOW (default) allows only users in group_types,
                  DENY denies users in group_types.
    - Override context vars in views for multiple actions as needed.

    Example for multiple user actions with different permissions in a view:
        ctx["user_can_edit_overview"] = self.user_can_edit(
            group_types=[GroupType.DEV, GroupType.LOCAL_AUTHORITY]
        )
        ctx["user_can_edit_change_alerted_status"] = self.user_can_edit(
            group_types=GroupType.HOME_OFFICE
        )
    """

    ALLOW = "allow"
    DENY = "deny"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["user_can_edit"] = self.user_can_edit(
            group_types=[
                GroupType.DEV,
                GroupType.LOCAL_AUTHORITY,
                GroupType.DEVOLVED_ADMINISTRATION,
                GroupType.HOME_OFFICE,
            ]
        )
        ctx["user_can_download"] = self.user_can_download(
            group_types=[
                GroupType.DEV,
                GroupType.LOCAL_AUTHORITY,
                GroupType.DEVOLVED_ADMINISTRATION,
                GroupType.HOME_OFFICE,
                GroupType.MHCLG,
            ]
        )
        ctx["available_announcements"] = self.get_announcements()
        return ctx

    def _normalize_group_types(self, group_types):
        if group_types is None:
            return []
        if isinstance(group_types, (list, tuple, set)):
            return group_types
        return [group_types]

    def user_action_allowed(self, group_types=None, mode=ALLOW):
        request = getattr(self, "request", None)
        if request is None:
            return True
        user = getattr(request, "user", None)
        normalized_group_types = self._normalize_group_types(group_types)
        if not normalized_group_types:
            return True
        user_group_types = self._get_user_group_types(user)
        group_types_set = set(normalized_group_types)
        in_group = bool(user_group_types & group_types_set)
        return in_group if mode == self.ALLOW else not in_group

    def user_can_edit(self, group_types=None, mode=ALLOW):
        return self.user_action_allowed(group_types=group_types, mode=mode)

    def user_can_download(self, group_types=None, mode=ALLOW):
        return self.user_action_allowed(group_types=group_types, mode=mode)

    def get_announcements(self):
        return Announcement.objects.filter(
            publish_at__lte=timezone.now(), hidden=False
        ).order_by("-publish_at")[:3]


class PermissionsMixin(UserActionsMixin, GroupRequiredMixin, LocalAuthorityAccessMixin):
    """
    Combined mixin that provides both user action permissions and group-based
    access control.

    This mixin combines the functionality of:
    - UserActionsMixin: Controls user action permissions (e.g., making MHCLG
      pages read-only)
    - GroupRequiredMixin: Provides group-based access control for views
    - LocalAuthorityAccessMixin: Provides local authority-based queryset filtering

    Use this instead of inheriting from UserActionsMixin, GroupRequiredMixin,
    and LocalAuthorityAccessMixin separately.

    Usage:
    class MyView(PermissionsMixin, SomeViewClass):
        group_type = [GroupType.LOCAL_AUTHORITY, GroupType.HOME_OFFICE]
        # ... rest of view configuration
    """


class SummaryListTestCaseMixinProtocol(Protocol):
    def assertRegex(self, *args, **kwargs):
        pass

    def assertNotRegex(self, *args, **kwargs):
        pass


class SummaryListTestCaseMixin:
    def assertSummaryListContainsRow(
        self: SummaryListTestCaseMixinProtocol,
        response: HttpResponse,
        key: str,
        value: str,
    ):
        escaped_key = re.escape(key)
        escaped_value = re.escape(value)
        return self.assertRegex(
            response.content.decode(),
            rf"(?s)<dt[^>]*>{escaped_key}.*?dt>.*?<dd[^>]*>.*?{escaped_value}.*?dd>",
        )

    def assertSummaryListContainsRowWithStatusTag(
        self: SummaryListTestCaseMixinProtocol,
        response: HttpResponse,
        key: str,
        value: str,
        status: str,
    ):
        escaped_key = re.escape(key)
        escaped_value = re.escape(value)
        escaped_status = re.escape(status)
        return self.assertRegex(
            response.content.decode(),
            rf"(?s)<dt[^>]*>{escaped_key}.*?dt>.*?<dd[^>]*>.*?"
            rf"{escaped_value}.*?{escaped_status}.*?dd>",
        )

    def assertSummaryListNotContainsRow(
        self: SummaryListTestCaseMixinProtocol,
        response: HttpResponse,
        key: str,
        value: str,
    ):
        escaped_key = re.escape(key)
        escaped_value = re.escape(value)
        return self.assertNotRegex(
            response.content.decode(),
            rf"(?s)<dt[^>]*>{escaped_key}.*?dt>.*?<dd[^>]*>.*?{escaped_value}.*?dd>",
        )

    def assertSummaryListNotContainsRowWithStatusTag(
        self: SummaryListTestCaseMixinProtocol,
        response: HttpResponse,
        key: str,
        value: str,
        status: str,
    ):
        escaped_key = re.escape(key)
        escaped_value = re.escape(value)
        escaped_status = re.escape(status)
        return self.assertNotRegex(
            response.content.decode(),
            rf"(?s)<dt[^>]*>{escaped_key}.*?dt>.*?<dd[^>]*>.*?"
            rf"{escaped_value}.*?{escaped_status}.*?dd>",
        )


class MultiLABannerMixin:
    def add_multi_la_message(self):
        ltla_name = self.object.ltla_name
        if not ltla_name or len(ltla_name) > 1:
            linked_records_url = reverse(
                "accommodation-requests:detail-linked-records",
                kwargs={"pk": self.object.id},
            )
            multi_la_message = format_html(
                "This accommodation request is linked to multiple local "
                "authorities (LAs). One or more of the guests on this"
                " accommodation request have visa applications in more than one LA."
                "<br><br>Some actions may be unavailable.<br><br>"
                "You can find guests who are linked to multiple local authorities in"
                " the <a class='govuk-link "
                "govuk-link--no-visited-state' href='{}'>linked records tab</a>.",
                linked_records_url,
            )
            messages.info(
                self.request,
                multi_la_message,
                extra_tags="html_safe content_full_width",
            )


@dataclass
class TimelineItemFileAttachment:
    filename: str
    download_url: str


@dataclass
class TimelineItem:
    title: str
    content: str
    date: datetime
    author_display_name: str | None = None
    attached_file: TimelineItemFileAttachment | None = None


class BaseTimelineEventsMixin(UserUtilitiesMixin):
    def _show_events(self):
        return True

    def _get_timeline_start(self):
        return timezone.make_aware(datetime.min)

    def _get_timeline_end(self):
        return timezone.make_aware(datetime.max)

    def get_timeline_events(self, obj) -> list[TimelineItem]:
        return []

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        events = sorted(
            self.get_timeline_events(self.object),
            key=lambda event: event.date,
            reverse=True,
        )
        paginator = Paginator(events, 6)
        ctx["events"] = paginator.get_page(self.request.GET.get("page"))
        ctx["event_type"] = TimelineEventType.LOG_ENTRY
        return ctx

    @staticmethod
    def _get_display_name(value, date: Optional[datetime] = None):
        if date is not None:
            date_to_compare = date
            if timezone.is_naive(date_to_compare):
                date_to_compare = timezone.make_aware(date_to_compare, dt_timezone.utc)
            if date_to_compare < GO_LIVE_CUTOFF:
                return value

        return value if value is not None else "System"

    def _ensure_aware_datetime(self, dt: datetime) -> datetime:
        if isinstance(dt, datetime) and timezone.is_naive(dt):
            return timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    def _get_timeline_range(self):
        start = self._get_timeline_start()
        end = self._get_timeline_end()
        start = self._ensure_aware_datetime(start)
        end = self._ensure_aware_datetime(end)
        return start, end


class AuditLogTimelineEventsMixinProtocol(Protocol):
    object: Model
    request: HttpRequest

    def get_timeline_events(self, obj) -> list[TimelineItem]:
        return []


class AuditLogTimelineEventsMixin(BaseTimelineEventsMixin):
    """
    Mixin to provide all audit log events for an object.

    To restrict audit log visibility for specific user groups, set an
    `audit_log_restrictions` attribute on your view, e.g.:

        audit_log_restrictions = {
            GroupType.LOCAL_AUTHORITY: {"hide_audit_logs": True},
        }
    """

    def _should_show_audit_logs(self) -> bool:
        restrictions = getattr(self, "audit_log_restrictions", None)
        if not restrictions or not getattr(self, "request", None):
            return True
        user_group_types = self._get_user_group_types()
        for group_type in user_group_types:
            config = restrictions.get(group_type)
            if config and config.get("hide_audit_logs", False):
                return False
        return True

    def determine_audit_event_type(self, old, new) -> AuditEventType:
        if old in NONE_TYPES and new not in NONE_TYPES:
            return AuditEventType.ADDED
        elif old not in NONE_TYPES and new in NONE_TYPES:
            return AuditEventType.DELETED
        elif old not in NONE_TYPES and new not in NONE_TYPES and old != new:
            return AuditEventType.CHANGED

        return AuditEventType.UNCHANGED

    def build_change_item(self, field: str, old, new) -> Optional[dict]:
        change_type = self.determine_audit_event_type(old, new)
        if change_type is AuditEventType.UNCHANGED:
            return None
        return {
            "field": field,
            "old": old,
            "new": new,
            "change_type": change_type,
        }

    def build_changes_list_from_entry(self, entry: LogEntry) -> list[dict]:
        changes_list: list[dict] = []
        for field, (old, new) in entry.changes_dict.items():
            item = self.build_change_item(field, old, new)
            if item is not None:
                changes_list.append(item)
        return changes_list

    def format_field_name(
        self: AuditLogTimelineEventsMixinProtocol, field_name: str
    ) -> str:
        field = self.object._meta.get_field(field_name)
        if not hasattr(field, "verbose_name"):
            return field_name
        return field.verbose_name[0].upper() + field.verbose_name[1:]

    def format_field_value(
        self: AuditLogTimelineEventsMixinProtocol, field_name: str, field_value: str
    ) -> str:
        field = cast(Field, self.object._meta.get_field(field_name))
        field_type = field.get_internal_type()

        if field_type in ["DateTimeField", "DateField"]:
            try:
                value = parser.parse(field_value)
            except ParserError:
                return field_value

            if field_type == "DateField":
                return value.date().strftime("%-d %B %Y")
            elif field_type == "DateTimeField":
                value = value.replace(tzinfo=dt_timezone.utc)
                value = value.astimezone(gettz(settings.TIME_ZONE))
                return value.strftime("%-d %B %Y")

        elif field_type == "ArrayField":
            return field_value[1:-1]
        elif field_type == "BooleanField":
            if field_value == "True":
                return "Yes"
            elif field_value == "False":
                return "No"

        elif choices := getattr(field, "choices", None):
            choices_dict = dict(choices)
            return choices_dict.get(field_value, field_value)

        return field_value

    def render_field_change(self, change):
        field_name = self.format_field_name(change["field"])
        old = self.format_field_value(change["field"], change["old"])
        new = self.format_field_value(change["field"], change["new"])
        if change["change_type"] == AuditEventType.CHANGED:
            return format_html(
                "{} {}: was {} now {}.",
                field_name,
                AUDIT_EVENT_TYPE_ACTION[AuditEventType.CHANGED],
                old,
                new,
            )
        elif change["change_type"] == AuditEventType.ADDED:
            return format_html(
                "{} {}: now {}.",
                field_name,
                AUDIT_EVENT_TYPE_ACTION[AuditEventType.ADDED],
                new,
            )
        elif change["change_type"] == AuditEventType.DELETED:
            return format_html(
                "{} {}: was {}.",
                field_name,
                AUDIT_EVENT_TYPE_ACTION[AuditEventType.DELETED],
                old,
            )

    def render_changes_for_timeline(self, changes):
        rendered_changes = []
        for change in changes:
            change = self.render_field_change(change)
            rendered_changes.append(change)

        if len(rendered_changes) == 1:
            return rendered_changes[0]

        return format_html(
            '<ul class="govuk-list govuk-list--bullet">{}</ul>',
            format_html_join(
                "", "<li>{}</li>", ((change,) for change in rendered_changes)
            ),
        )

    def get_timeline_events(self, obj) -> list[TimelineItem]:
        if not self._show_events() or not self._should_show_audit_logs():
            return []

        start, end = self._get_timeline_range()
        audit_log_entries = LogEntry.objects.get_for_object(obj).filter(
            timestamp__gte=start, timestamp__lte=end
        )

        events: list[TimelineItem] = super().get_timeline_events(obj)

        for entry in audit_log_entries:
            changes_list = self.build_changes_list_from_entry(entry)
            if changes_list:
                item = TimelineItem(
                    title="Details changed",
                    date=entry.timestamp,
                    content=self.render_changes_for_timeline(changes_list),
                    author_display_name=self._get_display_name(
                        entry.actor.email if entry.actor else None
                    ),
                )
                events.append(item)
        return events


class BaseInteractionTimelineEventsMixin(BaseTimelineEventsMixin):
    """
    Base mixin to provide all interaction events for an object.
    """

    request: HttpRequest

    def get_interactions(self, obj, start, end):
        if isinstance(obj, MvAccommodationRequest):
            return MvInteraction.objects.filter(
                linked_accommodation_request=obj,
                created_at__gte=start,
                created_at__lte=end,
            )
        elif isinstance(obj, MvPerson):
            return MvInteraction.objects.filter(
                linked_guest=obj,
                created_at__gte=start,
                created_at__lte=end,
            )
        elif isinstance(obj, MvVolunteer):
            return MvInteraction.objects.filter(
                linked_sponsor=obj,
                created_at__gte=start,
                created_at__lte=end,
            )
        elif isinstance(obj, MvAccommodation):
            return MvInteraction.objects.filter(
                linked_accommodation=obj,
                created_at__gte=start,
                created_at__lte=end,
            )
        return MvInteraction.objects.none()

    def _get_applicable_group_configs(self) -> list[dict]:
        """Resolve which interaction restriction configs apply to the current user.

        Expected on the view:

            interaction_restrictions = {
                GroupType.SOME_GROUP: {
                    "allowed_contacts": [
                        MvInteraction.InteractionContact.SOME_VALUE,
                        ...
                    ],
                    "show_actor_names": bool,
                },
                ...
            }
        """
        restrictions = getattr(self, "interaction_restrictions", None)
        # If the view does not define restrictions or there is no request, do nothing
        if not getattr(self, "request", None) or not restrictions:
            return []

        user_group_types = self._get_user_group_types()
        applicable_group_types = user_group_types.intersection(restrictions.keys())
        return [restrictions[group_type] for group_type in applicable_group_types]

    def get_restricted_interactions_queryset(self, interactions: QuerySet) -> QuerySet:
        applicable_configs = self._get_applicable_group_configs()
        if not applicable_configs:
            return interactions

        allowed_contacts: set = set()
        for config in applicable_configs:
            contacts = config.get("allowed_contacts")
            if isinstance(contacts, (list, set, tuple)):
                allowed_contacts.update(contacts)

        if not allowed_contacts:
            return interactions

        return interactions.filter(interaction_contact__in=allowed_contacts)

    def should_show_actor_names(self) -> bool:
        applicable_configs = self._get_applicable_group_configs()
        if not applicable_configs:
            return True

        for config in applicable_configs:
            if config.get("show_actor_names") is False:
                return False
        return True


class InteractionWithFilesTimelineEventsMixin(BaseInteractionTimelineEventsMixin):
    """
    Mixin to provide all an object's interaction events with files enabled.
    """

    def _get_interaction_download_url(self, obj, interaction):
        if isinstance(obj, MvAccommodationRequest):
            download_url = reverse(
                "accommodation-requests:interactions-download-attachment",
                kwargs={
                    "pk": interaction.linked_accommodation_request.id,
                    "interaction_id": interaction.pk,
                },
            )
            return download_url
        raise NotImplementedError(
            f"You must implement the download URL for"
            f" {obj._meta.verbose_name} interactions."
        )

    def get_timeline_events(self, obj) -> list[TimelineItem]:
        if not self._show_events():
            return []
        start, end = self._get_timeline_range()
        events = super().get_timeline_events(obj)
        interactions_qs = self.get_interactions(obj, start, end)
        interactions_qs = self.get_restricted_interactions_queryset(interactions_qs)
        interactions = interactions_qs.annotate(
            filename=Subquery(
                MvInteractionAttachmentMetadata.objects.filter(
                    rid=OuterRef("attachment")
                ).values("filename")[:1]
            ),
            file_path=Subquery(
                MvInteractionAttachmentMetadata.objects.filter(
                    rid=OuterRef("attachment")
                ).values("file_path")[:1]
            ),
        ).order_by("-created_at")

        show_actor_names = self.should_show_actor_names()

        for interaction in interactions:
            if show_actor_names and interaction.created_at is not None:
                raw_author = getattr(interaction.created_by, "email", None)
                author_display_name = self._get_display_name(
                    raw_author, interaction.created_at
                )
            else:
                author_display_name = None

            interaction_timeline_item = TimelineItem(
                title=interaction.title,
                date=interaction.created_at,
                author_display_name=author_display_name,
                content=format_interaction_content(interaction.interaction_notes),
            )
            if (
                interaction.file_path
                and FILE_DOWNLOAD_S3_BUCKET_NAME
                and s3_file_exists(
                    FILE_DOWNLOAD_S3_BUCKET_NAME,
                    f"interactions/{interaction.file_path}",
                )
            ):
                interaction_timeline_item.attached_file = TimelineItemFileAttachment(
                    filename=interaction.filename,
                    download_url=self._get_interaction_download_url(
                        obj=obj,
                        interaction=interaction,
                    ),
                )
            events.append(interaction_timeline_item)
        return events


class InteractionTimelineEventsMixin(BaseInteractionTimelineEventsMixin):
    """
    Mixin to provide all interaction events for an object.
    """

    def get_timeline_events(self, obj) -> list[TimelineItem]:
        if not self._show_events():
            return []
        start, end = self._get_timeline_range()
        events = super().get_timeline_events(obj)
        interactions = self.get_interactions(obj, start, end)
        interactions = self.get_restricted_interactions_queryset(interactions)
        interactions = interactions.order_by("-created_at")

        show_actor_names = self.should_show_actor_names()

        for interaction in interactions:
            if show_actor_names and getattr(interaction, "created_by", None):
                raw_author = interaction.created_by.email
                author_display_name = self._get_display_name(
                    raw_author, interaction.created_at
                )
            else:
                author_display_name = None

            interaction_timeline_item = TimelineItem(
                title=interaction.title,
                date=interaction.created_at,
                author_display_name=author_display_name,
                content=format_interaction_content(interaction.interaction_notes),
            )
            events.append(interaction_timeline_item)
        return events


class PIISafeRecordNameMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not hasattr(self.object, "get_pii_safe_record_name"):
            raise NotImplementedError(
                f"{self.object.__class__.__name__} is missing the implementation of "
                "the get_pii_safe_record_name() method."
            )

        # yes this looks odd, update the request here, not the context
        # so it can be used by the general context processor
        # do this here in get_context_data for the correct timing
        # i.e - after auth and record is fetched from the DB
        self.request.record_name = self.object.get_pii_safe_record_name()

        return context


class IsDuplicateMixin:
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_duplicate"] = not self.object.is_principal

        type_mappings = {
            MvVolunteer: {
                "model": SponsorDuplicateGroup,
                "filter_query": "sponsors__pk__in",
                "url_name": "sponsors:detail-overview",
                "name_attribute": "full_name",
                "sentence_partial_format": "sponsor and host record for {}",
            },
            MvAccommodation: {
                "model": AccommodationDuplicateGroup,
                "filter_query": "accommodations__pk__in",
                "url_name": "accommodations:detail-overview",
                "name_attribute": "full_address",
                "sentence_partial_format": "accommodation record for {}",
            },
            MvPerson: {
                "model": GuestDuplicateGroup,
                "filter_query": "guests__pk__in",
                "url_name": "guests:detail-overview",
                "name_attribute": "get_full_name",
                "sentence_partial_format": "guest record for {}",
            },
        }

        dedup_group = None
        for obj_type, config in type_mappings.items():
            if isinstance(self.object, obj_type):
                dedup_group = (
                    config["model"]
                    .objects.filter(**{config["filter_query"]: [self.object.pk]})
                    .only("principal_record")
                    .first()
                )
                if dedup_group and dedup_group.principal_record:
                    ctx["dedup_principal_url"] = reverse(
                        config["url_name"],
                        kwargs={"pk": dedup_group.principal_record.pk},
                    )
                    name_value = getattr(
                        dedup_group.principal_record, config["name_attribute"]
                    )
                    if callable(name_value):
                        name_value = name_value()
                    ctx["dedup_principal_url_text"] = config[
                        "sentence_partial_format"
                    ].format(name_value)
                break

        return ctx
