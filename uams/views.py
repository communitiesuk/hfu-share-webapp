import os
from datetime import datetime, timedelta

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Layout
from crispy_forms_gds.layout.constants import Size
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.views import View
from django.views.generic import DetailView
from django.views.generic.detail import SingleObjectMixin
from django_filters import CharFilter, FilterSet
from django_filters.views import FilterView
from django_tables2 import (
    Column,
    LazyPaginator,
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
from webapp.constants import UAMS_SEARCH_FIELDS
from webapp.mixins import FilterPanelMixin, PermissionsMixin, PIISafeRecordNameMixin
from webapp.s3 import get_presigned_download_url, s3_file_exists
from webapp.search import perform_search
from webapp.utils import (
    CustomDateColumn,
    CustomDateFromToRangeFilter,
    CustomDateTimeColumn,
)
from webapp.views import SummaryListView
from webapp.widgets import DatePicker, StackedRangeInput


class UamsTable(tables.Table):
    sponsor_full_name = Column(verbose_name="Sponsor name")
    sponsor_date_of_birth = CustomDateColumn(verbose_name="Sponsor date of birth")
    email = Column(verbose_name="Email address")
    identification_type = Column(verbose_name="Identification type")
    identification_number = Column(verbose_name="Identification number")
    residential_postcode = Column(verbose_name="Postcode")
    ltla_name = Column(verbose_name="Local authority")
    reference = Column(verbose_name="Sponsorship certification application number")
    created_at = CustomDateTimeColumn(verbose_name="Created at")

    def render_sponsor_full_name(self, record: SponsorshipCertificationForm, value):
        return format_html(
            '<a class="govuk-body-s govuk-link" href="{url}">{value}</a>',
            url=reverse("uams:detail-overview", args=[record.pk]),
            value=value,
        )

    class Meta:
        model = SponsorshipCertificationForm
        template_name = "webapp/components/tables/table.html"
        order_by = "-created_at"
        fields = (
            "sponsor_full_name",
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

    sponsor_date_of_birth = CustomDateFromToRangeFilter(
        label="Sponsor date of birth",
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

    created_at = CustomDateFromToRangeFilter(
        label="Created at",
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

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, UAMS_SEARCH_FIELDS)

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
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
            "sponsor_date_of_birth",
            "created_at",
        ]


class UamsListView(PermissionsMixin, SingleTableMixin, FilterView):
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
    paginator_class = LazyPaginator
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
        ]
        return super().get_queryset().only(*fields_needed)


class UamsDetailOverviewView(PIISafeRecordNameMixin, PermissionsMixin, SummaryListView):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    model = SponsorshipCertificationForm
    template_name = "uams/detail_view/detail_view_overview.html"

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


class UamsDetailPropertiesView(PIISafeRecordNameMixin, PermissionsMixin, DetailView):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "uams/detail_view/detail_view_properties.html"
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


class UamsDetailLinkedRecordsView(PIISafeRecordNameMixin, PermissionsMixin, DetailView):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "uams/detail_view/detail_view_linked_records.html"
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


class UamsFilesView(PIISafeRecordNameMixin, PermissionsMixin, DetailView):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.MHCLG,
        GroupType.HOME_OFFICE,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "uams/detail_view/detail_view_files.html"
    model = SponsorshipCertificationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        uam = self.object

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
