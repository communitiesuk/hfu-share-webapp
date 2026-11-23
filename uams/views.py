import os
from functools import partial

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Fieldset, Layout
from crispy_forms_gds.layout.constants import Size
from django.contrib import messages
from django.db import DatabaseError
from django.db.models import Case, OrderBy, QuerySet, TextField, Value, When
from django.http import (
    Http404,
)
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, FormView
from django.views.generic.detail import SingleObjectMixin
from django_filters import CharFilter, FilterSet, MultipleChoiceFilter
from django_filters.views import FilterView
from django_tables2 import (
    Column,
    SingleTableMixin,
    tables,
)

from accounts.enums import GroupType
from case_management.settings import FILE_DOWNLOAD_S3_BUCKET_NAME
from ontology.models import (
    CheckType,
    SponsorshipCertificationAttachmentMetadata,
    SponsorshipCertificationForm,
)
from uams.forms import (
    PreApprovalCheckStatusForm,
    SponsorCertificationCodeEmailedForm,
)
from uams.mixins import UamsChecksMixin
from uams.utils import uam_check_group_types
from webapp.constants import (
    LA_PRE_APPROVAL_CHECK_ALLOWED_STATUSES,
    PRE_APPROVAL_CODE_SENT_EDITABLE_STATUSES,
    UAM_CAN_EDIT_LA_CHECKS_GROUP_TYPE,
    UAM_CAN_EDIT_UKVI_CHECKS_GROUP_TYPE,
    UAMS_SEARCH_FIELDS,
    UKVI_PRE_APPROVAL_CHECK_STATUS_PASSED,
)
from webapp.mixins import (
    DetailViewMixin,
    FilterPanelMixin,
    InteractionTimelineEventsMixin,
    PageTitleMixin,
    PaginatorClassMixin,
    PermissionsMixin,
    PIISafeRecordNameMixin,
    SectionHeadingMixin,
    UserActionsMixinProtocol,
)
from webapp.s3 import (
    get_govuk_forms_attachment_filepath,
    get_presigned_download_url,
    s3_file_exists,
)
from webapp.search import perform_search
from webapp.templatetags.link_renderers import render_govuk_link
from webapp.templatetags.notification_banner_renderers import (
    render_govuk_notification_banner_content,
)
from webapp.templatetags.pre_approval_status_extras import (
    pre_approval_check_status_to_hint,
    pre_approval_check_status_to_title,
    pre_approval_status_to_tag_colour,
)
from webapp.templatetags.tag_renderers import (
    render_app_la_pre_approval_check_code_sent_to_sponsor_tag,
    render_app_la_pre_approval_check_status_tag,
    render_app_pre_approval_status_tag,
    render_app_ukvi_pre_approval_check_status_tag,
)
from webapp.utils import (
    CustomDateColumn,
    CustomDateFromToRangeFilter,
    CustomDateTimeColumn,
    date_hint_text,
)
from webapp.views import SummaryListView
from webapp.widgets import (
    CheckboxSelectMultipleWithTags,
    DatePicker,
    StackedRangeInput,
)

PreApprovalCheckField = SponsorshipCertificationForm.PreApprovalCheckField
PreApprovalStatus = SponsorshipCertificationForm.PreApprovalStatus
PreApprovalCheckStatus = SponsorshipCertificationForm.PreApprovalCheckStatus


class UamsTable(tables.Table):
    sponsor_full_name = Column(verbose_name="Sponsor name")
    pre_approval_status = Column(
        verbose_name="Application status", accessor="get_pre_approval_status"
    )
    sponsor_date_of_birth = CustomDateColumn(verbose_name="Sponsor date of birth")
    email = Column(verbose_name="Email address")
    identification_type = Column(verbose_name="Identification type")
    identification_number = Column(verbose_name="Identification number")
    residential_postcode = Column(verbose_name="Postcode")
    ltla_name = Column(verbose_name="Local authority")
    reference = Column(verbose_name="Sponsorship certification application number")
    created_at = CustomDateTimeColumn(verbose_name="Created at")

    def render_sponsor_full_name(self, record: SponsorshipCertificationForm, value):
        return render_govuk_link(
            value,
            reverse("uams:detail-overview", args=[record.pk]),
        )

    def render_pre_approval_status(self, value: PreApprovalStatus) -> str:
        return render_app_pre_approval_status_tag(value)

    def order_pre_approval_status(
        self, queryset: QuerySet[SponsorshipCertificationForm], is_descending: bool
    ) -> tuple[QuerySet[SponsorshipCertificationForm], bool]:
        statuses = []
        for uam in queryset:
            status = uam.get_pre_approval_status()
            statuses.append(When(pk=uam.pk, then=Value(status)))

        status_column = Case(*statuses, output_field=TextField())

        sort_by_status = OrderBy(status_column, descending=is_descending)
        queryset = queryset.order_by(sort_by_status, "-created_at")

        return queryset, True

    class Meta:
        model = SponsorshipCertificationForm
        template_name = "webapp/components/tables/table.html"
        order_by = "-created_at"
        fields = (
            "sponsor_full_name",
            "pre_approval_status",
            "sponsor_date_of_birth",
            "email",
            "identification_type",
            "identification_number",
            "residential_postcode",
            "ltla_name",
            "reference",
            "created_at",
        )


class UamsFilter(FilterSet, FilterPanelMixin):
    search = CharFilter(
        label="Search",
        method="search_filter",
        help_text="Search the data in the table",
    )

    status = MultipleChoiceFilter(
        choices=PreApprovalStatus.choices,
        label="",
        method="filter_status",
        widget=CheckboxSelectMultipleWithTags(
            label_to_tag_colour=pre_approval_status_to_tag_colour
        ),
    )

    sponsor_date_of_birth = CustomDateFromToRangeFilter(
        label="Sponsor date of birth",
        widget=StackedRangeInput(
            sub_widget=DatePicker,
            attrs={
                "from_help_text": date_hint_text(20000),
                "to_help_text": date_hint_text(9500),
                "from_label": "Date from",
                "to_label": "Date to",
            },
        ),
        error_messages={
            "invalid_range": "'Sponsor date of birth from' must be before "
            "'Sponsor date of birth to'.",
        },
    )

    created_at = CustomDateFromToRangeFilter(
        label="Created at",
        widget=StackedRangeInput(
            sub_widget=DatePicker,
            attrs={
                "from_help_text": date_hint_text(1600),
                "to_help_text": date_hint_text(20),
                "from_label": "Date from",
                "to_label": "Date to",
            },
        ),
        error_messages={
            "invalid_range": "'Created at date from' must be before "
            "'Created at date to'.",
        },
    )

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, UAMS_SEARCH_FIELDS)

    def filter_status(
        self,
        queryset: QuerySet[SponsorshipCertificationForm],
        _name: str,
        value: list[str],
    ) -> QuerySet[SponsorshipCertificationForm]:
        matching_pks = [
            uam.pk for uam in queryset if uam.get_pre_approval_status() in value
        ]
        return queryset.filter(pk__in=matching_pks)

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
            Fieldset(
                "status",
                legend="Suitability checks status",
                legend_size=Size.MEDIUM,
                css_class="govuk-!-margin-bottom-5",
            ),
            Field(
                "sponsor_date_of_birth",
                context={"legend_size": "govuk-fieldset__legend--m"},
            ),
            Field(
                "created_at",
                context={"legend_size": "govuk-fieldset__legend--m"},
            ),
        )
        return form

    class Meta:
        model = SponsorshipCertificationForm
        fields = [
            "search",
            "status",
            "sponsor_date_of_birth",
            "created_at",
        ]


class UamsListView(
    SectionHeadingMixin,
    PermissionsMixin,
    SingleTableMixin,
    PaginatorClassMixin,
    FilterView,
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    model = SponsorshipCertificationForm
    table_class = UamsTable
    filterset_class = UamsFilter
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    template_name = "uams/uams_list_page.html"

    def get_queryset(self):
        fields_needed = [
            "given_name",
            "family_name",
            "sponsor_date_of_birth",
            "email",
            "identification_type",
            "identification_number",
            "residential_postcode",
            "ltla_name",
            "reference",
            "created_at",
            *[field.value for field in PreApprovalCheckField],
        ]
        return super().get_queryset().only(*fields_needed)


class UamsDetailViewMixin(UserActionsMixinProtocol, DetailViewMixin):
    namespace = "uams"
    singular_name = "Application to sponsor a child"
    plural_name = "Applications to sponsor a child"

    @property
    def views_for_record(self):
        return (
            UamsDetailOverviewView,
            UamsChecksView,
            UamsFilesView,
            UamsDetailLinkedRecordsView,
            UamsDetailPropertiesView,
            UamsDetailHistoryView,
        )

    def get_url_args(self):
        return (self.object.pk,)

    def should_show_tab_for_user(self, view_name: str) -> bool:
        match view_name:
            # TODO: Remove both cases when releasing the feature to all
            case "checks":
                return self.user_action_allowed(
                    group_types=uam_check_group_types(UamsChecksView.group_type)
                )
            case "history":
                return self.user_action_allowed(
                    group_types=uam_check_group_types(UamsDetailHistoryView.group_type)
                )
            case _:
                return True

    @property
    def page_heading(self):
        return self.object.get_full_name()


class UamsDetailOverviewView(
    PIISafeRecordNameMixin,
    PermissionsMixin,
    UamsDetailViewMixin,
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
    view_name = "overview"
    model = SponsorshipCertificationForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["fields"].insert(
            0,
            (
                "Sponsor suitability checks status",
                render_app_pre_approval_status_tag(
                    self.object.get_pre_approval_status()
                ),
            ),
        )
        return ctx

    class Meta:
        fields = [
            "given_name",
            "family_name",
            "sponsor_date_of_birth",
            "email",
            "phone_number",
            "nationality",
            "identification_type",
            "identification_number",
            "residential_postcode",
            "ltla_name",
            "reference",
            "certificate_reference",
            "created_at",
        ]


class UamsChecksView(
    PIISafeRecordNameMixin,
    UamsChecksMixin,
    UamsDetailViewMixin,
    SummaryListView,
):
    object: SponsorshipCertificationForm

    group_type = {
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    }

    # TODO: Remove when releasing the feature to all
    def get_group_type(self):
        return uam_check_group_types(self.group_type)

    view_name = "checks"
    model = SponsorshipCertificationForm

    def _checks_edit_url(self, check):
        return reverse(
            "uams:checks-edit",
            kwargs={
                "pk": self.object.pk,
                "check": check.value,
            },
        )

    def _task_list_item(self, check, tag_renderer_func, can_show_link):
        return (
            pre_approval_check_status_to_title(check),
            self._checks_edit_url(check),
            tag_renderer_func(getattr(self.object, check.value)),
            can_show_link,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pre_approval_status = self.object.get_pre_approval_status()
        pre_approval_check_code_sent_status = (
            self.object.get_pre_approval_check_code_sent_status(pre_approval_status)
        )

        can_edit_ukvi_checks = self.can_edit_ukvi_checks()
        can_edit_la_checks = self.can_edit_la_checks(pre_approval_status)
        can_edit_send_code = (
            pre_approval_status in PRE_APPROVAL_CODE_SENT_EDITABLE_STATUSES
        )

        context["can_edit_ukvi_checks"] = can_edit_ukvi_checks
        context["can_edit_la_checks"] = can_edit_la_checks
        context["ukvi_checks_completed"] = (
            pre_approval_status in LA_PRE_APPROVAL_CHECK_ALLOWED_STATUSES
        )

        context["ukvi_checks"] = tuple(
            self._task_list_item(
                check,
                render_app_ukvi_pre_approval_check_status_tag,
                can_edit_ukvi_checks,
            )
            for check in SponsorshipCertificationForm.UKVI_CHECK_FIELDS
        )

        render_app_la_pre_approval_check_status_tag_partial = partial(
            render_app_la_pre_approval_check_status_tag, pre_approval_status
        )

        context["la_checks"] = tuple(
            self._task_list_item(
                check,
                render_app_la_pre_approval_check_status_tag_partial,
                can_edit_la_checks,
            )
            for check in SponsorshipCertificationForm.LA_CHECK_FIELDS
        ) + (
            (
                pre_approval_check_status_to_title(
                    PreApprovalCheckField.SPONSOR_CERTIFICATION_CODE_EMAILED
                ),
                self._checks_edit_url(
                    PreApprovalCheckField.SPONSOR_CERTIFICATION_CODE_EMAILED
                ),
                render_app_la_pre_approval_check_code_sent_to_sponsor_tag(
                    pre_approval_check_code_sent_status
                ),
                can_edit_la_checks and can_edit_send_code,
            ),
        )

        return context


class UamsDetailPropertiesView(
    PIISafeRecordNameMixin,
    PermissionsMixin,
    UamsDetailViewMixin,
    DetailView,
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    view_name = "properties"
    model = SponsorshipCertificationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        uam = self.get_object()

        sponsor_details = [
            ("Given name", uam.given_name),
            ("Family name", uam.family_name),
            ("Has other names", uam.has_other_names),
            ("Other names", uam.other_names),
            ("Sponsor date of birth", uam.sponsor_date_of_birth),
            ("Different address", uam.different_address),
            ("Nationality", uam.nationality),
            ("Has other nationalities", uam.has_other_nationalities),
            ("Identification type", uam.get_identification_type_display()),
            ("Identification number", uam.identification_number),
            ("Email", uam.email),
            ("Phone number", uam.phone_number),
            ("Sponsor declaration", uam.sponsor_declaration),
        ]

        cohabitant_details = [
            ("Cohabitant given name", uam.cohabitant_given_name),
            ("Cohabitant family name", uam.cohabitant_family_name),
            ("Cohabitant date of birth", uam.cohabitant_date_of_birth),
            ("Cohabitant nationality", uam.cohabitant_nationality),
            ("Cohabitant ID", uam.cohabitant_id),
            (
                "Cohabitant ID type and number",
                uam.cohabitant_id_type_and_number,
            ),
        ]

        accommodation_details = [
            ("Residential line 1", uam.residential_line_1),
            ("Residential line 2", uam.residential_line_2),
            ("Residential town", uam.residential_town),
            ("Residential postcode", uam.residential_postcode),
            ("Local authority", uam.ltla_name),
        ]

        child_guest_details = [
            ("Minor given name", uam.minor_given_name),
            ("Minor family name", uam.minor_family_name),
            ("Minor date of birth", uam.minor_date_of_birth),
            ("Minor email", uam.minor_email),
            ("Minor phone number", uam.minor_phone_number),
            ("Minor contact type", uam.minor_contact_type),
        ]

        reference_details = [
            ("Reference", uam.reference),
            ("Certificate reference", uam.certificate_reference),
            ("Created at", uam.created_at),
            ("Started at", uam.started_at),
            ("Notification sent", uam.notification_sent),
            ("Notification timestamp", uam.notification_timestamp),
            ("Ingestion time", uam.ingestion_time),
            ("Notional data", uam.notional_data),
            ("Viewer group names", uam.viewer_group_names),
        ]

        parental_consent_details = [
            (
                "Has parental consent",
                uam.has_parental_consent,
            ),
            (
                "UK parental consent filename",
                uam.uk_parental_consent_filename,
            ),
            (
                "UK parental consent file size",
                uam.uk_parental_consent_file_size,
            ),
            (
                "UK parental consent file type",
                uam.uk_parental_consent_file_type,
            ),
            (
                "UK parental consent saved filename",
                uam.uk_parental_consent_saved_filename,
            ),
            (
                "Ukraine parental consent filename",
                uam.ukraine_parental_consent_filename,
            ),
            (
                "Ukraine parental consent file size",
                uam.ukraine_parental_consent_file_size,
            ),
            (
                "Ukraine parental consent file type",
                uam.ukraine_parental_consent_file_type,
            ),
            (
                "Ukraine parental consent saved filename",
                uam.ukraine_parental_consent_saved_filename,
            ),
        ]

        qualifying_details = [
            ("Is under 18", uam.is_under_18),
            ("Is living December", uam.is_living_december),
            ("Is unaccompanied", uam.is_unaccompanied),
            ("Is committed", uam.is_committed),
            ("Is consent", uam.is_consent),
            ("Is permitted", uam.is_permitted),
        ]

        context.update(
            {
                "sponsor_details": sponsor_details,
                "cohabitant_details": cohabitant_details,
                "accommodation_details": accommodation_details,
                "child_guest_details": child_guest_details,
                "reference_details": reference_details,
                "parental_consent_details": parental_consent_details,
                "qualifying_details": qualifying_details,
            }
        )

        return context


class UamsDetailLinkedRecordsView(
    PIISafeRecordNameMixin, PermissionsMixin, UamsDetailViewMixin, DetailView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    view_name = "linked-records"
    model = SponsorshipCertificationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        uam = self.object
        linked_records = []

        accommodation_requests = uam.get_accommodation_requests_restrict_for_user(user)
        if accommodation_requests.exists():
            linked_records.append(("Accommodation requests", accommodation_requests))

        context["linked_records"] = linked_records

        return context


class UamsFilesView(
    PIISafeRecordNameMixin, PermissionsMixin, UamsDetailViewMixin, DetailView
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    view_name = "files"
    model = SponsorshipCertificationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        uam = self.object

        if uam.reference and uam.reference.startswith("SPON-"):
            # Legacy UAM attachment journey
            if uam.attachments_metadata and uam.attachments_metadata.count() > 0:
                attachments = uam.attachments_metadata.all()
            else:
                person = uam.get_person_restrict_for_user(self.request.user)
                if person is None or person.checks is None:
                    return context
                attachments = SponsorshipCertificationAttachmentMetadata.objects.filter(
                    rid__in=person.checks.filter(
                        check_type__id__in=[
                            CheckType.Id.UK_FORM_UPLOADED,
                            CheckType.Id.UKR_FORM_UPLOADED,
                        ]
                    ).values_list("document", flat=True)
                )

            context["attachments"] = [
                {
                    "url": reverse(
                        "uams:download-attachment",
                        kwargs={
                            "pk": uam.pk,
                            "metadata_id": attachment.id,
                        },
                    ),
                    "name": attachment.filename or "Consent form",
                }
                for attachment in attachments
                if s3_file_exists(
                    bucket_name=FILE_DOWNLOAD_S3_BUCKET_NAME,
                    file_key=f"uams/{attachment.file_path}",
                )
            ]

        elif uam.reference:
            # GOV.UK Forms attachments are retrieved differently
            # Bucket path will be:
            # /uams/govuk_forms/YYYYMMDDThhmmssZ_ABCD1234/filename.jpg
            context["attachments"] = []

            if s3_file_exists(
                bucket_name=FILE_DOWNLOAD_S3_BUCKET_NAME,
                file_key=get_govuk_forms_attachment_filepath(uam, "uk"),
            ):
                context["attachments"].append(
                    {
                        "url": reverse(
                            "uams:download-govuk-forms-attachment",
                            kwargs={"pk": uam.pk, "consent_file_type": "uk"},
                        ),
                        "name": uam.uk_parental_consent_filename,
                    }
                )

            if s3_file_exists(
                bucket_name=FILE_DOWNLOAD_S3_BUCKET_NAME,
                file_key=get_govuk_forms_attachment_filepath(uam, "ukraine"),
            ):
                context["attachments"].append(
                    {
                        "url": reverse(
                            "uams:download-govuk-forms-attachment",
                            kwargs={"pk": uam.pk, "consent_file_type": "ukraine"},
                        ),
                        "name": uam.ukraine_parental_consent_filename,
                    }
                )

        return context


class UamsDetailHistoryView(
    PIISafeRecordNameMixin,
    PermissionsMixin,
    InteractionTimelineEventsMixin,
    UamsDetailViewMixin,
    DetailView,
):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]

    # TODO: Remove when releasing the feature to all
    def get_group_type(self):
        return uam_check_group_types(self.group_type)

    view_name = "history"
    model = SponsorshipCertificationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["history_description"] = (
            "This history shows the dates a change was made to the application to "
            "sponsor a child record on the system."
        )
        return context


class UamsDownloadAttachmentView(PermissionsMixin, SingleObjectMixin, View):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    model = SponsorshipCertificationForm

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.document = None
        self.file_name = None
        self.file_path = None

    def dispatch(self, request, *args, **kwargs):
        uam = self.get_object()
        # permission to uam is validated by the PermissionMixin

        if uam.attachments_metadata and uam.attachments_metadata.count() > 0:
            attachments = uam.attachments_metadata.all()
        else:
            person = uam.get_person_restrict_for_user(self.request.user)
            if person is None or person.checks is None:
                raise Http404(
                    "Missing person or check required to find attachment metadata"
                )
            attachments = SponsorshipCertificationAttachmentMetadata.objects.filter(
                rid__in=person.checks.filter(
                    check_type__id__in=[
                        CheckType.Id.UK_FORM_UPLOADED,
                        CheckType.Id.UKR_FORM_UPLOADED,
                    ]
                ).values_list("document", flat=True)
            )

        metadata = attachments.filter(id=kwargs.get("metadata_id")).first()
        if not metadata or not metadata.file_path:
            raise Http404("Missing file metadata")

        self.file_name = metadata.filename
        self.file_path = metadata.file_path

        return super().dispatch(request, *args, **kwargs)

    def get(self, *_args, **_kwargs):
        presigned_url = get_presigned_download_url(
            bucket_name=FILE_DOWNLOAD_S3_BUCKET_NAME,
            file_key=f"uams/{self.file_path}",
            filename=self.file_name,
        )

        return redirect(presigned_url)


class UamsDownloadGOVUKFormsAttachmentView(PermissionsMixin, SingleObjectMixin, View):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    model = SponsorshipCertificationForm

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.uam = None
        self.consent_file_type = None
        self.filename = None

    def dispatch(self, request, *args, **kwargs):
        self.uam = self.get_object()
        self.consent_file_type = kwargs.get("consent_file_type")

        if self.consent_file_type == "uk":
            self.filename = self.uam.uk_parental_consent_filename
        elif self.consent_file_type == "ukraine":
            self.filename = self.uam.ukraine_parental_consent_filename
        else:
            raise Http404("Consent file type not found")
        return super().dispatch(request, *args, **kwargs)

    def get(self, *_args, **_kwargs):
        presigned_url = get_presigned_download_url(
            bucket_name=FILE_DOWNLOAD_S3_BUCKET_NAME,
            file_key=get_govuk_forms_attachment_filepath(
                self.uam, self.consent_file_type
            ),
            filename=self.filename,
        )

        return redirect(presigned_url)


class UamsChecksEditView(
    PageTitleMixin,
    PIISafeRecordNameMixin,
    UamsChecksMixin,
    SingleObjectMixin,
    FormView,
):
    object: SponsorshipCertificationForm

    group_type = UAM_CAN_EDIT_LA_CHECKS_GROUP_TYPE | UAM_CAN_EDIT_UKVI_CHECKS_GROUP_TYPE

    # TODO: Remove when releasing the feature to all
    def get_group_type(self):
        return uam_check_group_types(self.group_type)

    model = SponsorshipCertificationForm
    template_name = "uams/uams_check_edit_page.html"
    page_caption = "Application to sponsor a child record for"

    _check = None

    @property
    def form_class(self):
        if self._current_check_is_for_code_sent_status():
            return SponsorCertificationCodeEmailedForm

        return PreApprovalCheckStatusForm

    @property
    def check(self) -> PreApprovalCheckField | None:
        if self._check is None:
            try:
                self._check = PreApprovalCheckField(self.kwargs["check"])
            except ValueError:
                # dispatch() raises Http404 for unknown slugs,
                # so self.check is valid beyond it.
                pass

        return self._check

    @property
    def page_heading(self):
        return self.object.get_full_name()

    def _current_check_is_for_code_sent_status(self):
        return self.check is PreApprovalCheckField.SPONSOR_CERTIFICATION_CODE_EMAILED

    def _is_ukvi_check(self):
        return self.check in SponsorshipCertificationForm.UKVI_CHECK_FIELDS

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        pre_approval_status = self.object.get_pre_approval_status()

        ukvi_checks = SponsorshipCertificationForm.UKVI_CHECK_FIELDS
        la_checks = SponsorshipCertificationForm.LA_CHECK_FIELDS + (
            PreApprovalCheckField.SPONSOR_CERTIFICATION_CODE_EMAILED,
        )

        if self.check not in ukvi_checks and self.check not in la_checks:
            raise Http404("Check not recognised.")

        if (self.check in ukvi_checks and not self.can_edit_ukvi_checks()) or (
            self.check in la_checks and not self.can_edit_la_checks(pre_approval_status)
        ):
            raise Http404("You do not have permission to access this page.")

        if self._current_check_is_for_code_sent_status() and (
            pre_approval_status not in PRE_APPROVAL_CODE_SENT_EDITABLE_STATUSES
        ):
            raise Http404("You do not have permission to access this page.")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        value = getattr(self.object, self.check.value)

        if self._current_check_is_for_code_sent_status():
            kwargs["initial"]["status"] = value
        else:
            kwargs["check_label"] = pre_approval_check_status_to_title(self.check)
            kwargs["check_hint"] = pre_approval_check_status_to_hint(self.check)
            kwargs["initial"]["status"] = value or PreApprovalCheckStatus.NOT_STARTED

        return kwargs

    def form_valid(self, form):
        if form.has_changed():
            try:
                previous_pre_approval_status = self.object.get_pre_approval_status()

                self.object.update_pre_approval_check_status(
                    self.check,
                    form.cleaned_data["status"],
                    self.request.user,
                )

                self._set_success_banner(
                    previous_check_status=(
                        form.initial["status"]
                        if self._current_check_is_for_code_sent_status()
                        else PreApprovalCheckStatus(form.initial["status"])
                    ),
                    previous_pre_approval_status=previous_pre_approval_status,
                    current_check_status=(
                        form.cleaned_data["status"]
                        if self._current_check_is_for_code_sent_status()
                        else PreApprovalCheckStatus(form.cleaned_data["status"])
                    ),
                    current_pre_approval_status=self.object.get_pre_approval_status(),
                )
            except DatabaseError:
                self._set_unsuccessful_banner()

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["is_ukvi_check"] = self._is_ukvi_check()

        context["page_caption"] = self.page_caption
        context["cancel_url"] = self.get_cancel_url()

        return context

    def _get_checks_url(self):
        return reverse(
            "uams:detail-checks",
            kwargs={
                "pk": self.object.pk,
            },
        )

    @staticmethod
    def _changed_to(
        previous: PreApprovalStatus,
        current: PreApprovalStatus,
        target: PreApprovalStatus | set[PreApprovalStatus],
    ) -> bool:
        if isinstance(target, set):
            return previous not in target and current in target
        else:
            return previous is not target and current is target

    @staticmethod
    def _changed_from(
        previous: PreApprovalStatus,
        current: PreApprovalStatus,
        target: PreApprovalStatus | set[PreApprovalStatus],
    ) -> bool:
        if isinstance(target, set):
            return previous in target and current not in target
        else:
            return previous is target and current is not target

    @staticmethod
    def _check_status_text(status: PreApprovalCheckStatus | bool) -> str:
        if isinstance(status, bool):
            return "yes" if status else "no"

        return status.value.lower()

    def _ukvi_banner_message(
        self,
        previous_pre_approval_status: PreApprovalStatus,
        current_pre_approval_status: PreApprovalStatus,
        heading: str,
        changed_warning: str,
    ):
        def _changed_to(target):
            return self._changed_to(
                previous_pre_approval_status, current_pre_approval_status, target
            )

        def _changed_from(target):
            return self._changed_from(
                previous_pre_approval_status, current_pre_approval_status, target
            )

        body = None
        warning = None

        # UKVI changed from not passed to passed
        if _changed_to(UKVI_PRE_APPROVAL_CHECK_STATUS_PASSED):
            ltla_name = (
                self.object.ltla_name[0]
                if self.object.ltla_name
                else "The local authority"
            )
            body = (
                "Sponsor passed all UK Visas and Immigration checks. "
                f"{ltla_name} will now complete their checks."
            )

        # UKVI changed from not failed to failed
        elif _changed_to(PreApprovalStatus.FAILED_UKVI_CHECKS):
            body = (
                "Sponsor failed UK Visas and Immigration checks. "
                "The Ministry of Housing, Communities and Local Government (MHCLG) "
                "will contact the sponsor with this decision."
            )

        # UKVI changed from passed to not passed or
        # UKVI changed from failed to not failed
        if _changed_from(UKVI_PRE_APPROVAL_CHECK_STATUS_PASSED) or _changed_from(
            PreApprovalStatus.FAILED_UKVI_CHECKS
        ):
            warning = changed_warning

        return heading, body, warning

    def _la_banner_message(
        self,
        previous_pre_approval_status: PreApprovalStatus,
        current_pre_approval_status: PreApprovalStatus,
        heading: str,
        changed_warning: str,
    ):
        def _changed_to(target):
            return self._changed_to(
                previous_pre_approval_status, current_pre_approval_status, target
            )

        def _changed_from(target):
            return self._changed_from(
                previous_pre_approval_status, current_pre_approval_status, target
            )

        body = None
        warning = None

        # LA changed from not complete to complete
        if _changed_to(PreApprovalStatus.COMPLETED):
            heading = (
                "All checks passed and Sponsor Certification code sent to sponsor."
            )

        # LA changed from complete to not complete
        elif _changed_from(PreApprovalStatus.COMPLETED):
            if self._current_check_is_for_code_sent_status():
                heading = "Sponsor certification code marked as not sent"

            warning = (
                f"Checks status changed from {previous_pre_approval_status.value} "
                f"to {current_pre_approval_status.value}. "
                "If the Sponsor Certification code has already been sent, contact "
                "the Ministry of Housing, Communities and Local Government (MHCLG)"
            )

        # LA changed from not passed to passed
        elif _changed_to(PreApprovalStatus.PASSED_ALL_CHECKS):
            body = "Sponsor passed all suitability checks."
            warning = (
                "Send the Sponsor Certification code "
                f"{self.object.certificate_reference} to the sponsor."
            )

        # LA changed from not failed to failed
        if _changed_to(PreApprovalStatus.FAILED_LA_CHECKS):
            body = (
                "Sponsor failed local authority checks. "
                "The Ministry of Housing, Communities and Local Government (MHCLG) "
                "will contact the sponsor with this decision."
            )

        # LA changed from passed to not passed and not all checks completed
        # LA changed from failed to not failed
        if (
            _changed_from(PreApprovalStatus.PASSED_ALL_CHECKS)
            and not _changed_to(PreApprovalStatus.COMPLETED)
        ) or _changed_from(PreApprovalStatus.FAILED_LA_CHECKS):
            warning = changed_warning

        return heading, body, warning

    def _get_success_banner_message(
        self,
        previous_check_status: PreApprovalCheckStatus | bool,
        previous_pre_approval_status: PreApprovalStatus,
        current_check_status: PreApprovalCheckStatus | bool,
        current_pre_approval_status: PreApprovalStatus,
    ) -> tuple[str, str | None, str | None]:
        # So mypy knows that check cannot be None at this point
        assert self.check is not None

        name_of_check = pre_approval_check_status_to_title(self.check)
        previous_check_status_text = self._check_status_text(previous_check_status)
        current_check_status_text = self._check_status_text(current_check_status)

        default_heading = f"{name_of_check}: {current_check_status_text}"
        changed_warning = (
            f"You changed {name_of_check} from {previous_check_status_text} to "
            f"{current_check_status_text}. "
            "Raise a support ticket to stop any follow-on actions."
        )

        if self._is_ukvi_check():
            return self._ukvi_banner_message(
                previous_pre_approval_status,
                current_pre_approval_status,
                default_heading,
                changed_warning,
            )

        return self._la_banner_message(
            previous_pre_approval_status,
            current_pre_approval_status,
            default_heading,
            changed_warning,
        )

    def _set_success_banner(
        self,
        previous_check_status: PreApprovalCheckStatus | bool,
        previous_pre_approval_status: PreApprovalStatus,
        current_check_status: PreApprovalCheckStatus | bool,
        current_pre_approval_status: PreApprovalStatus,
    ):
        message_heading, message_body, warning_message = (
            self._get_success_banner_message(
                previous_check_status,
                previous_pre_approval_status,
                current_check_status,
                current_pre_approval_status,
            )
        )

        messages.success(
            self.request,
            (
                render_govuk_notification_banner_content(
                    heading=message_heading, body=message_body
                )
                if message_body
                else (message_heading)
            ),
            extra_tags="html_safe" if message_body else "",
        )

        if warning_message:
            messages.warning(self.request, warning_message)

    def _set_unsuccessful_banner(self):
        messages.error(
            self.request,
            f"{pre_approval_check_status_to_title(self.check)} update has not "
            "been saved. If the problem continues raise a support ticket.",
        )

    def get_cancel_url(self):
        return self._get_checks_url()

    def get_success_url(self):
        return self._get_checks_url()
