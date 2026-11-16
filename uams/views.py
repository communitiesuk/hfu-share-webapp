import os
from enum import Enum

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Fieldset, Layout
from crispy_forms_gds.layout.constants import Size
from django.core.exceptions import PermissionDenied
from django.db.models import Case, OrderBy, QuerySet, TextField, Value, When
from django.http import (
    Http404,
    JsonResponse,
)
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView
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
from uams.mixins import UamsChecksMixin
from webapp.constants import (
    UAM_CAN_EDIT_LA_CHECKS_GROUP_TYPE,
    UAM_CAN_EDIT_UKVI_CHECKS_GROUP_TYPE,
    UAMS_SEARCH_FIELDS,
)
from webapp.mixins import (
    DetailViewMixin,
    FilterPanelMixin,
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
from webapp.templatetags.pre_approval_status_extras import (
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

    def render_pre_approval_status(
        self, value: SponsorshipCertificationForm.PreApprovalStatus
    ) -> str:
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
        choices=SponsorshipCertificationForm.PreApprovalStatus.choices,
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
            *SponsorshipCertificationForm.UKVI_CHECK_FIELDS,
            *SponsorshipCertificationForm.LA_CHECK_FIELDS,
            "sponsor_certification_code_emailed",
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
        )

    def get_url_args(self):
        return (self.object.pk,)

    def should_show_tab_for_user(self, view_name: str) -> bool:
        match view_name:
            case "checks":
                return self.user_action_allowed(group_types=UamsChecksView.group_type)
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
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    view_name = "checks"
    model = SponsorshipCertificationForm

    def _checks_edit_url(self, check: Enum):
        return reverse(
            "uams:checks-edit",
            kwargs={
                "pk": self.object.pk,
                "check": check.value,
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pre_approval_status = self.object.get_pre_approval_status()
        pre_approval_check_code_sent_status = (
            self.object.get_pre_approval_check_code_sent_status()
        )

        can_edit_ukvi_checks = self.can_edit_ukvi_checks()
        can_edit_la_checks = self.can_edit_la_checks(pre_approval_status)
        can_send_code = pre_approval_check_code_sent_status in (
            SponsorshipCertificationForm.PreApprovalCheckCodeSentStatus.CODE_NOT_SENT,
            SponsorshipCertificationForm.PreApprovalCheckCodeSentStatus.CODE_SENT,
        )

        context["can_edit_ukvi_checks"] = can_edit_ukvi_checks
        context["can_edit_la_checks"] = can_edit_la_checks

        context["ukvi_checks"] = (
            (
                "UK consent form",
                self._checks_edit_url(
                    UamsChecksEditView.UKVIChecks.UK_CONSENT_FORM_STATUS
                ),
                render_app_ukvi_pre_approval_check_status_tag(
                    self.object.uk_consent_form_status
                ),
                can_edit_ukvi_checks,
            ),
            (
                "Ukraine consent form",
                self._checks_edit_url(
                    UamsChecksEditView.UKVIChecks.UKRAINE_CONSENT_FORM_STATUS
                ),
                render_app_ukvi_pre_approval_check_status_tag(
                    self.object.ukraine_consent_form_status
                ),
                can_edit_ukvi_checks,
            ),
            (
                "Sponsor immigration eligibility",
                self._checks_edit_url(
                    UamsChecksEditView.UKVIChecks.SPONSOR_IMMIGRATION_ELIGIBILITY_STATUS
                ),
                render_app_ukvi_pre_approval_check_status_tag(
                    self.object.sponsor_immigration_eligibility_status
                ),
                can_edit_ukvi_checks,
            ),
            (
                "Sponsor and household security checks",
                self._checks_edit_url(
                    UamsChecksEditView.UKVIChecks.SPONSOR_HOUSEHOLD_SECURITY_CHECKS_STATUS
                ),
                render_app_ukvi_pre_approval_check_status_tag(
                    self.object.sponsor_household_security_checks_status
                ),
                can_edit_ukvi_checks,
            ),
        )

        context["la_checks"] = (
            (
                "Sponsor and household members enhanced DBS",
                self._checks_edit_url(
                    UamsChecksEditView.LAChecks.SPONSOR_HOUSEHOLD_ENHANCED_DBS_STATUS,
                ),
                render_app_la_pre_approval_check_status_tag(
                    pre_approval_status,
                    self.object.sponsor_household_enhanced_dbs_status,
                ),
                can_edit_la_checks,
            ),
            (
                "Accommodation exists",
                self._checks_edit_url(
                    UamsChecksEditView.LAChecks.ACCOMMODATION_EXISTS_STATUS,
                ),
                render_app_la_pre_approval_check_status_tag(
                    pre_approval_status, self.object.accommodation_exists_status
                ),
                can_edit_la_checks,
            ),
            (
                "Accommodation suitable",
                self._checks_edit_url(
                    UamsChecksEditView.LAChecks.ACCOMMODATION_SUITABLE_STATUS,
                ),
                render_app_la_pre_approval_check_status_tag(
                    pre_approval_status, self.object.accommodation_suitable_status
                ),
                can_edit_la_checks,
            ),
            (
                "Sponsor role and expectations",
                self._checks_edit_url(
                    UamsChecksEditView.LAChecks.SPONSOR_ROLE_AND_EXPECTATIONS_STATUS,
                ),
                render_app_la_pre_approval_check_status_tag(
                    pre_approval_status,
                    self.object.sponsor_role_and_expectations_status,
                ),
                can_edit_la_checks,
            ),
            (
                "Sponsor arrangements suitable",
                self._checks_edit_url(
                    UamsChecksEditView.LAChecks.SPONSOR_ARRANGEMENTS_SUITABLE_STATUS,
                ),
                render_app_la_pre_approval_check_status_tag(
                    pre_approval_status,
                    self.object.sponsor_arrangements_suitable_status,
                ),
                can_edit_la_checks,
            ),
            (
                "Code sent to sponsor",
                self._checks_edit_url(
                    UamsChecksEditView.LAChecks.SPONSOR_CERTIFICATION_CODE_EMAILED,
                ),
                render_app_la_pre_approval_check_code_sent_to_sponsor_tag(
                    pre_approval_check_code_sent_status
                ),
                can_edit_la_checks and can_send_code,
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
    View,
):
    group_type = UAM_CAN_EDIT_LA_CHECKS_GROUP_TYPE.union(
        UAM_CAN_EDIT_UKVI_CHECKS_GROUP_TYPE
    )
    model = SponsorshipCertificationForm

    class UKVIChecks(Enum):
        UK_CONSENT_FORM_STATUS = "uk-consent-form-status"
        UKRAINE_CONSENT_FORM_STATUS = "ukraine-consent-form-status"
        SPONSOR_IMMIGRATION_ELIGIBILITY_STATUS = (
            "sponsor-immigration-eligibility-status"
        )
        SPONSOR_HOUSEHOLD_SECURITY_CHECKS_STATUS = (
            "sponsor-household-security-checks-status"
        )

    class LAChecks(Enum):
        SPONSOR_HOUSEHOLD_ENHANCED_DBS_STATUS = "sponsor-household-enhanced-dbs-status"
        ACCOMMODATION_EXISTS_STATUS = "accommodation-exists-status"
        ACCOMMODATION_SUITABLE_STATUS = "accommodation-suitable-status"
        SPONSOR_ROLE_AND_EXPECTATIONS_STATUS = "sponsor-role-and-expectations-status"
        SPONSOR_ARRANGEMENTS_SUITABLE_STATUS = "sponsor-arrangements-suitable-status"
        SPONSOR_CERTIFICATION_CODE_EMAILED = "sponsor-certification-code-emailed"

    def dispatch(self, request, *args, **kwargs):
        check = kwargs["check"]

        self.object = self.get_object()
        pre_approval_status = self.object.get_pre_approval_status()

        ukvi_checks = [ukvi_check.value for ukvi_check in UamsChecksEditView.UKVIChecks]
        la_checks = [la_check.value for la_check in UamsChecksEditView.LAChecks]

        if check not in ukvi_checks and check not in la_checks:
            raise Http404("Check not recognised.")

        if (check in ukvi_checks and not self.can_edit_ukvi_checks()) or (
            check in la_checks and not self.can_edit_la_checks(pre_approval_status)
        ):
            raise PermissionDenied("You do not have permission to access this page.")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # TODO: Update this in the next PR
        return JsonResponse(
            {"detail": "I'm a teapot"},
            status=418,
        )
