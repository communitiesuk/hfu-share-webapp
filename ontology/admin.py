import logging
import uuid

from auditlog.admin import LogEntryAdmin
from auditlog.filters import ResourceTypeFilter
from auditlog.mixins import AuditlogHistoryAdminMixin
from auditlog.models import LogEntry
from django.contrib import admin
from django.db import DatabaseError
from django.db.models import (
    DateTimeField,
    F,
    ForeignKey,
    ManyToManyField,
    Max,
    OuterRef,
    QuerySet,
    Subquery,
)
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from ontology.actions.reassignment_request_actions import (
    fill_missing_ltla_utla,
    normalise_outcome_values,
)
from ontology.admin_actions import (
    process_update_guest_titles,
    solve_duplicate_record_sponsor_checks,
)
from ontology.admin_filters import (
    ARsCreatedOrModifiedSinceShareGoLiveFilter,
    ChecksSinceShareGoLiveFilter,
    DateRangeFilter,
    GuestsWithIncorrectTitlesExcludingDuplicatesFilter,
)
from ontology.models import (
    Announcement,
    CheckType,
    Comment,
    CommentAttachment,
    CommentAttachmentMetadata,
    DevCheckV2,
    ExportToolObject,
    HiddenUnassignedAccommodationRequest,
    MvAccommodation,
    MvAccommodationRequest,
    MvInteraction,
    MvInteractionAttachmentMetadata,
    MvPerson,
    MvVolunteer,
    ReassignmentRequest,
    SafeguardingNotification,
    SafeguardingReferral,
    SponsorshipCertificationAttachmentMetadata,
    SponsorshipCertificationForm,
    VisaApplication,
    VisaInformationRequest,
    VisaInformationRequestComments,
)


@admin.action(description="Create stub safeguarding checks")
def create_safeguarding_checks(_, __, queryset: QuerySet[MvAccommodationRequest]):
    for accommodation_request in queryset:
        for check_type_id in [
            CheckType.Id.ACCOMM_SUITABLE,
            CheckType.Id.ACCOMM_EXISTS,
            CheckType.Id.SPONSOR_DBS,
            CheckType.Id.GROUP_ARRIVED,
        ]:
            check = DevCheckV2()
            check.id = uuid.uuid4()
            check.check_type = CheckType.objects.get(id=check_type_id)
            check.save()
            check.AR.add(accommodation_request)
            check.save()


def devcheckv2_detail_view(obj):
    checks = obj.devcheckv2_set.all()
    if not checks:
        return "(None)"
    return format_html_join(
        mark_safe("<br>"),
        '<a href={} target="_blank">{}</a>',
        [
            (
                reverse(
                    f"admin:{check._meta.app_label}_{check._meta.model_name}_change",
                    args=[check.id],
                ),
                check.check_type,
            )
            for check in checks
        ],
    )


@admin.action(description="Recalculate checks status")
def recalculate_checks_status(_, request, queryset):
    for accommodation_request in queryset:
        try:
            new_status = (
                accommodation_request.determine_checks_status_from_linked_objects()
            )
            accommodation_request.update_checks_status(new_status, request.user)
        except Exception as e:
            # Log the exception for debugging and output AR id and reason

            logging.error(
                "Exception in recalculate_checks_status for AR id %s: %s",
                accommodation_request.id,
                e,
            )
            continue


class OntologyAdmin(admin.ModelAdmin):
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        # set raw_id_fields automatically,
        # this is a performance optimisation which prevents the edit pages from
        # pulling a full list of every object in the system when showing the select
        # widget for related fields.
        if not self.raw_id_fields:
            self.raw_id_fields = []
        self.raw_id_fields.extend(
            field.name
            for field in model._meta.get_fields()
            if isinstance(field, (ForeignKey, ManyToManyField))
        )


class CustomLogEntryAdmin(LogEntryAdmin):
    LogEntryAdmin.list_display = [
        f for f in LogEntryAdmin.list_display if f != "cid_url"
    ]
    list_filter = ["action", ResourceTypeFilter, ("timestamp", DateRangeFilter)]


class VisaApplicationAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    list_display = [
        "Q44g_full_name",
        "visa_status",
        "application_event_datetime",
        "ltla_name",
        "gwf",
        "application_unique_application_number",
    ]
    search_fields = [
        "Q44g_full_name",
        "ltla_name",
        "application_unique_application_number",
        "gwf",
    ]
    list_filter = ["visa_status", "is_notional"]

    def has_change_permission(self, request, obj=None):
        # This table cannot be edited in the Django admin
        return False


class AccommodationRequestAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    list_display = [
        "title",
        "ltla_name",
        "utla_name",
        "status",
        "checks_status",
        "unique_application_number",
    ]
    search_fields = ["title", "unique_application_number", "ltla_name", "utla_name"]
    list_filter = [
        "checks_status",
        "status",
        "notional_data",
        "edited_in_app",
        "is_principal",
        ARsCreatedOrModifiedSinceShareGoLiveFilter,
    ]
    readonly_fields = [
        "detail_view",
        "devcheckv2_detail_view",
    ]
    actions = [create_safeguarding_checks, recalculate_checks_status]

    def detail_view(self, obj):
        if obj.pk:
            return format_html(
                '<a href={} target="_blank">Detail page</a>',
                reverse("accommodation-requests:detail-overview", args=[obj.pk]),
            )
        return "-"

    def devcheckv2_detail_view(self, obj):
        return devcheckv2_detail_view(obj)


class MvPersonAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    list_display = ["first_name", "last_name", "id", "visa_status"]
    search_fields = ["first_name", "last_name", "id", "gwf"]
    readonly_fields = ["devcheckv2_detail_view"]
    list_filter = [
        "visa_status",
        "is_principal",
        GuestsWithIncorrectTitlesExcludingDuplicatesFilter,
    ]
    actions = ["update_guest_titles_action"]

    def get_queryset(self, request):
        return MvPerson.objects_including_archived.all()

    def devcheckv2_detail_view(self, obj):
        return devcheckv2_detail_view(obj)

    @admin.action(description="Update selected guest titles")
    def update_guest_titles_action(self, request, queryset):
        success_count = 0
        already_correct_count = 0
        error_count = 0

        for person in queryset:
            try:
                result = process_update_guest_titles(person)

                if result:
                    success_count += 1
                else:
                    already_correct_count += 1
            except DatabaseError:
                error_count += 1

        summary = (
            f"Guest title processing complete: "
            f"{success_count} updated successfully, "
            f"{already_correct_count} already correct (skipped), "
            f"{error_count} failed due to errors."
        )

        self.message_user(request, summary)


class DevCheckV2Admin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    list_display = ["id", "check_type", "check_status", "active", "create_at"]
    search_fields = ["id"]
    list_filter = [
        "check_type",
        "check_status",
        "active",
        ChecksSinceShareGoLiveFilter,
    ]

    actions = [solve_duplicate_record_sponsor_checks]


class AccommodationAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    search_fields = ["full_address", "id"]
    list_display = ["full_address", "is_available_for_rematch", "accommodation_type"]
    list_filter = ["accommodation_type", "notional_data", "is_principal"]
    readonly_fields = ["detail_view"]

    def get_queryset(self, request):
        return MvAccommodation.objects_including_archived.all()

    def detail_view(self, obj):
        if obj.pk:
            return format_html(
                '<a href={} target="_blank">Detail page</a>',
                reverse("accommodations:detail-overview", args=[obj.pk]),
            )
        return "-"


class HiddenUnassignedAccommodationRequestAdmin(
    AuditlogHistoryAdminMixin, OntologyAdmin
):
    show_auditlog_history_link = True
    list_display = ["accommodation_request", "hidden_by", "hidden_at"]
    list_filter = [("hidden_at", DateRangeFilter)]
    search_fields = ["accommodation_request__id"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReassignmentRequestAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    readonly_fields = ["detail_view"]
    actions = [normalise_outcome_values, fill_missing_ltla_utla]
    search_fields = [
        "accommodation_request_title",
        "destination_ltla_name",
        "source_ltla_name",
        "id",
    ]
    list_filter = ["type", "outcome"]

    def detail_view(self, obj):
        if obj.pk:
            return format_html(
                '<a href={} target="_blank">Detail page</a>',
                reverse("reassignment-requests:detail-made", args=[obj.pk]),
            )
        return "-"


class UamAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    readonly_fields = ["detail_view"]
    list_display = ["given_name", "family_name", "email", "created_at"]
    search_fields = ["given_name", "family_name", "email"]
    list_filter = ["notional_data"]

    def detail_view(self, obj):
        if obj.pk:
            return format_html(
                '<a href={} target="_blank">Detail page</a>',
                reverse("uams:detail-overview", args=[obj.pk]),
            )
        return "-"

    def has_change_permission(self, request, obj=None):
        # This table cannot be edited in the Django admin
        return False


class AnnouncementAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    list_display = [
        "title",
        "get_body_preview",
        "type",
        "link_text",
        "link",
        "publish_at",
    ]
    search_fields = ["title", "body", "type"]
    readonly_fields = ["created_at", "created_by"]

    @admin.display(description="Body")
    def get_body_preview(self, obj):
        preview = (
            (obj.body[:70] + "...") if obj.body and len(obj.body) > 70 else obj.body
        )
        return preview

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class ExportToolObjectAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    list_display = [
        "export_tool_id",
        "title",
        "group_title",
        "sponsor_full_name",
        "person_full_name",
        "ltla_name",
        "utla_name",
    ]
    search_fields = [
        "export_tool_id",
        "title",
        "group_title",
        "sponsor_full_name",
        "person_full_name",
    ]
    list_filter = ["export_tool_id"]


class MvVolunteerAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    list_display = [
        "full_name",
        "email",
        "last_updated_date",
        "application_unique_application_number",
    ]
    search_fields = ["full_name", "email", "application_unique_application_number"]
    list_filter = ["sponsor_type", "is_sponsor", "notional_data", "is_principal"]

    def get_queryset(self, request):
        return MvVolunteer.objects_including_archived.all()


class MvInteractionAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    list_display = [
        "interaction_type",
        "interaction_contact",
        "created_by",
        "linked_accommodation_request",
        "linked_match",
        "linked_old_interaction",
        "linked_safeguarding_notification",
        "old_accommodation_request",
    ]
    search_fields = ["linked_accommodation_request__title"]
    list_filter = ["interaction_type"]


class SafeguardingNotificationAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    list_display = [
        "pk",
        "alert_type",
        "linked_ar",
        "linked_check",
        "linked_sponsor",
        "created_at",
        "modified_at",
    ]
    search_fields = ["pk", "ar__title", "sponsor_names"]
    list_filter = [
        "alert_type",
        "dev_check_v2__check_type",
        ("created_at", DateRangeFilter),
        ("modified_at", DateRangeFilter),
        "notional_data",
    ]
    ordering = ["-modified_at", "-created_at"]

    @admin.display(description="Accommodation request")
    def linked_ar(self, obj):
        if obj.ar:
            url = reverse(
                "admin:ontology_mvaccommodationrequest_change", args=[obj.ar.id]
            )
            return format_html('<a href="{}">{}</a>', url, obj.ar.title or obj.ar.id)
        return "-"

    @admin.display(description="Linked safeguarding check")
    def linked_check(self, obj):
        if obj.dev_check_v2:
            url = reverse(
                "admin:ontology_devcheckv2_change", args=[obj.dev_check_v2.id]
            )
            return format_html(
                '<a href="{}">{}</a>', url, obj.dev_check_v2.get_check_failed_title()
            )

    @admin.display(description="Linked sponsor")
    def linked_sponsor(self, obj):
        if not obj.sponsor_ids:
            return "-"

        sponsors = MvVolunteer.objects.filter(id__in=obj.sponsor_ids)
        links = []

        for sponsor in sponsors:
            url = reverse("admin:ontology_mvvolunteer_change", args=[sponsor.id])
            links.append(
                format_html('<a href="{}">{}</a>', url, sponsor.get_full_name())
            )

        return format_html(", ".join(links))


class SafeguardingReferralAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    list_display = [
        "pk",
        "alerted_status",
        "person",
        "person_gwf",
        "person_application_number",
        "latest_alert_date",
        "created_at",
        "modified_at",
    ]
    search_fields = [
        "pk",
        "person__gwf",
        "person__application_number",
        "person__first_name",
        "person__last_name",
        "person__id",
    ]
    list_filter = [
        "alerted_status",
        ("created_at", DateRangeFilter),
        ("modified_at", DateRangeFilter),
        "notional_data",
    ]
    ordering = [
        "-modified_at",
        "-created_at",
        "person__first_name",
        "person__last_name",
    ]

    def get_queryset(self, request):
        qs = (
            super()
            .get_queryset(request)
            .select_related("person")
            .only(
                "id",
                "created_at",
                "modified_at",
                "alerted_status",
                "notional_data",
                "person_id",
                "person__first_name",
                "person__last_name",
                "person__gwf",
                "person__application_number",
            )
        )

        latest_alert_date_subquery = (
            SafeguardingNotification.objects.filter(
                ar=OuterRef("person__accommodation_request")
            )
            .order_by()
            .values("ar")
            .annotate(max_date=Max("created_at"))
            .values("max_date")[:1]
        )

        return qs.annotate(
            latest_alert_date=Coalesce(
                Subquery(latest_alert_date_subquery, output_field=DateTimeField()),
                F("created_at"),
            )
        )

    @admin.display(description="All linked GWFs")
    def person_gwf(self, obj):
        person = obj.person
        if not person or not person.gwf:
            return None
        return ", ".join(person.gwf)

    @admin.display(description="All linked UANs")
    def person_application_number(self, obj):
        person = obj.person
        if not person or not person.application_number:
            return None
        return ", ".join(person.application_number)

    @admin.display(description="Latest alert date", ordering="latest_alert_date")
    def latest_alert_date(self, obj):
        return obj.latest_alert_date


class VisaInformationRequestCommentsAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    list_display = ["pk", "visa_information_request", "comment_type", "current_status"]
    search_fields = ["pk"]
    list_filter = ["comment_type", "current_status"]


class VisaInformationRequestAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    list_display = ["pk", "request_title", "ltla_name", "utla_name", "request_status"]
    search_fields = [
        "pk",
        "request_title",
        "ltla_name",
        "utla_name",
        "visa_application__gwf",
    ]
    list_filter = ["request_type", "request_status"]
    actions = ["fix_incorrect_values"]

    def _fix_request_type(self, obj):
        changed = False
        if obj.request_type in ["GENERAL", "Checks"]:
            obj.request_type = "General"
            changed = True
        elif obj.request_type == "CHILD_SPONSORED_BY_PARENTS":
            obj.request_type = "Child Sponsored by Parent"
            changed = True
        return changed

    def _fix_requested_check_type_id(self, obj):
        check_types = obj.requested_check_type_id
        if not check_types:
            return False
        needs_update = False
        new_check_types = []
        for ct in check_types:
            if ct == "ACCOMM_SUITABLE":
                new_check_types.append("2")
                needs_update = True
            elif ct == "SPONSOR_DBS":
                new_check_types.append("3")
                needs_update = True
            else:
                new_check_types.append(ct)
        if needs_update:
            obj.requested_check_type_id = new_check_types
        return needs_update

    def _fix_request_status(self, obj):
        status = obj.request_status
        if status in ["Closed - Not needed", "Closed - Resolved"]:
            obj.request_status = "Closed"
            return True
        if status == "Waiting on LA":
            obj.request_status = "Awaiting LA"
            return True
        if status in ["Waiting on UKVI", "Waiting on MHCLG", "Waiting on DLUHC"]:
            obj.request_status = "Awaiting UKVI"
            return True
        return False

    @admin.action(description="Fix VIR values mismatch")
    def fix_incorrect_values(self, request, queryset):
        updated = 0
        for obj in queryset:
            changed = False
            if self._fix_request_type(obj):
                changed = True
            if self._fix_requested_check_type_id(obj):
                changed = True
            if self._fix_request_status(obj):
                changed = True
            if changed:
                obj.save()
                updated += 1
        self.message_user(
            request, f"Updated {updated} record(s) with corrected values."
        )


class SponsorshipCertificationAttachmentMetadataAdmin(
    AuditlogHistoryAdminMixin, OntologyAdmin
):
    show_auditlog_history_link = True
    list_display = [
        "id",
        "filename",
        "size_bytes",
        "media_type",
        "file_path",
    ]


class MvInteractionAttachmentMetadataAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    list_display = ["id", "filename", "size_bytes", "media_type", "file_path", "rid"]
    search_fields = ["id", "filename", "rid"]


class CommentAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    list_display = [
        "id",
        "attached_accommodation_request_id",
        "attached_reassignment_request_id",
    ]


class CommentAttachmentAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    list_display = ["id", "comment_id", "filename", "media_type"]


class CommentAttachmentMetadataAdmin(AuditlogHistoryAdminMixin, OntologyAdmin):
    show_auditlog_history_link = True
    list_display = [
        "id",
        "file_name",
        "file_size",
    ]


admin.site.unregister(LogEntry)
admin.site.register(LogEntry, CustomLogEntryAdmin)
admin.site.register(VisaApplication, VisaApplicationAdmin)
admin.site.register(MvPerson, MvPersonAdmin)
admin.site.register(MvAccommodationRequest, AccommodationRequestAdmin)
admin.site.register(MvAccommodation, AccommodationAdmin)
admin.site.register(MvVolunteer, MvVolunteerAdmin)
admin.site.register(MvInteraction, MvInteractionAdmin)
admin.site.register(DevCheckV2, DevCheckV2Admin)
admin.site.register(SafeguardingNotification, SafeguardingNotificationAdmin)
admin.site.register(SafeguardingReferral, SafeguardingReferralAdmin)
admin.site.register(ReassignmentRequest, ReassignmentRequestAdmin)
admin.site.register(SponsorshipCertificationForm, UamAdmin)
admin.site.register(VisaInformationRequest, VisaInformationRequestAdmin)
admin.site.register(VisaInformationRequestComments, VisaInformationRequestCommentsAdmin)
admin.site.register(Announcement, AnnouncementAdmin)
admin.site.register(ExportToolObject, ExportToolObjectAdmin)
admin.site.register(
    HiddenUnassignedAccommodationRequest,
    HiddenUnassignedAccommodationRequestAdmin,
)
admin.site.register(
    SponsorshipCertificationAttachmentMetadata,
    SponsorshipCertificationAttachmentMetadataAdmin,
)
admin.site.register(
    MvInteractionAttachmentMetadata, MvInteractionAttachmentMetadataAdmin
)
admin.site.register(Comment, CommentAdmin)
admin.site.register(CommentAttachment, CommentAttachmentAdmin)
admin.site.register(CommentAttachmentMetadata, CommentAttachmentMetadataAdmin)
