import csv
import io
import os
from datetime import datetime, timedelta

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Layout
from crispy_forms_gds.layout.constants import Size
from django.contrib import messages
from django.db.models import (
    Case,
    DateTimeField,
    F,
    Max,
    OuterRef,
    Q,
    Subquery,
    TextField,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Concat
from django.http import HttpRequest, StreamingHttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.html import format_html
from django.views import View
from django.views.generic import DetailView, FormView
from django_filters import CharFilter, FilterSet, MultipleChoiceFilter
from django_filters.views import FilterView
from django_tables2 import (
    Column,
    LazyPaginator,
    SingleTableMixin,
    tables,
)

from accounts.enums import GroupType
from accounts.models import User
from ontology.models import (
    CheckType,
    DevCheckV2,
    MvAccommodationRequest,
    MvPerson,
    MvVolunteer,
    SafeguardingNotification,
    SafeguardingReferral,
    VisaApplication,
)
from safeguarding.forms import CentralSafeguardingAlertedStatusForm
from visa_applications.templatetags.visa_application_extras import (
    visa_status_to_tag_colour,
)
from webapp.constants import (
    ESCALATED_CHECKS_SEARCH_FIELDS,
    visa_status_list_ordered,
)
from webapp.mixins import (
    FilterPanelMixin,
    GroupRequiredMixin,
    PermissionsMixin,
    PIISafeRecordNameMixin,
    UserActionsMixin,
)
from webapp.search import perform_search
from webapp.templatetags.alerted_status_extras import alerted_status_to_tag_colour
from webapp.utils import (
    CustomDateColumn,
    CustomDateFromToRangeFilter,
    CustomDateTimeColumn,
)
from webapp.views import SummaryListRow, SummaryListView, TwoColumnSummaryListView
from webapp.widgets import CheckboxSelectMultipleWithTags, DatePicker, StackedRangeInput

BATCH_SIZE = 500


class DownloadEscalatedChecksCSVView(PermissionsMixin, View):
    group_type = [GroupType.HOME_OFFICE, GroupType.DEV]
    visa_applications_address_lookup: dict[str, str] = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        visa_applications = VisaApplication.objects.exclude(
            Q(application_unique_application_number__isnull=True)
            | Q(application_unique_application_number="")
        ).values_list(
            "application_unique_application_number", "applicant_final_address"
        )

        DownloadEscalatedChecksCSVView.visa_applications_address_lookup = dict(
            visa_applications
        )

    def get(self, request, *_args, **_kwargs):
        columns = [
            "Applicant Full Name",
            "Applicant Date Of Birth",
            "Applicant Passport Number",
            "Applicant GWF(s)",
            "Applicant UAN(s)",
            "Visa Status",
            "Sponsor Name",
            "Sponsor DOB",
            "Sponsor Full Address",
            "Sponsor Passport",
            "UTLA",
        ]

        qs = SafeguardingReferral.objects.all()
        latest_alert_date_subquery = (
            SafeguardingNotification.objects.filter(
                ar=OuterRef("person__accommodation_request")
            )
            .order_by()
            .values("ar")
            .annotate(max_date=Max("created_at"))
            .values("max_date")[:1]
        )
        qs = qs.annotate(
            latest_alert_date=Coalesce(
                Subquery(latest_alert_date_subquery, output_field=DateTimeField()),
                F("created_at"),
            )
        )
        filterset = EscalatedChecksTableFilter(request.GET, queryset=qs)
        filtered_qs = (
            filterset.qs.select_related(
                "person",
                "person__accommodation_request",
                "person__accommodation_request__primary_sponsor",
            )
            .only(
                # Fields from SafeguardingReferral
                "id",
                "created_at",
                "modified_at",
                # Fields from MvPerson
                "person__first_name",
                "person__last_name",
                "person__is_principal",
                "person__visa_status",
                "person__date_of_birth",
                "person__gwf",
                "person__application_number",
                "person__passport_id",
                # Fields from MvAccommodationRequest
                "person__accommodation_request__utla_name",
                # Fields from MvVolunteer
                "person__accommodation_request__primary_sponsor__full_name",
                "person__accommodation_request__primary_sponsor__first_name",
                "person__accommodation_request__primary_sponsor__last_name",
                "person__accommodation_request__primary_sponsor__date_of_birth",
                "person__accommodation_request__primary_sponsor__application_unique_application_number",
                "person__accommodation_request__primary_sponsor__passport_details",
            )
            .annotate(
                ar_utla_name=F("person__accommodation_request__utla_name"),
                sponsor_date_of_birth=F(
                    "person__accommodation_request__primary_sponsor__date_of_birth"
                ),
                sponsor_passport_details=F(
                    "person__accommodation_request__primary_sponsor__passport_details"
                ),
                sponsor_full_name=F(
                    "person__accommodation_request__primary_sponsor__full_name"
                ),
                sponsor_first_name=F(
                    "person__accommodation_request__primary_sponsor__first_name"
                ),
                sponsor_last_name=F(
                    "person__accommodation_request__primary_sponsor__last_name"
                ),
                sort_date=Case(
                    When(modified_at__isnull=False, then=F("modified_at")),
                    default=F("created_at"),
                    output_field=DateTimeField(),
                ),
                latest_alert_date=Coalesce(
                    Subquery(latest_alert_date_subquery, output_field=DateTimeField()),
                    F("created_at"),
                ),
            )
            .order_by("-latest_alert_date", "person__first_name", "person__last_name")
        )

        def stream_csv_with_iterator():
            # Prepare the CSV writer
            buffer = io.StringIO()
            writer = csv.writer(buffer)

            # Yield header
            writer.writerow(columns)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

            referrals = filtered_qs.iterator(chunk_size=BATCH_SIZE)

            batch_count = 0
            for model_object in referrals:
                row = self.build_csv_row(model_object)
                writer.writerow(row)
                batch_count += 1

                # Yield rows in batches
                if batch_count >= BATCH_SIZE:
                    yield buffer.getvalue()
                    buffer.seek(0)
                    buffer.truncate(0)
                    batch_count = 0

            # Yield any remaining rows
            if buffer.tell() > 0:
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

        filename = (
            f"escalated_checks-{date_format(timezone.localtime(), 'y-m-d_H-i')}.csv"
        )

        response = StreamingHttpResponse(
            stream_csv_with_iterator(), content_type="text/csv"
        )

        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

    @staticmethod
    def csv_value(value):
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            filtered = [item for item in value if item not in (None, "", '""')]
            if not filtered:
                return None
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(filtered)
            return buffer.getvalue().strip("\r\n")
        if isinstance(value, datetime):
            value = value.replace(microsecond=0)
            if value.tzinfo:
                value = value.astimezone(timezone.get_default_timezone()).replace(
                    tzinfo=None
                )
            return value.isoformat(sep=" ")
        return str(value)

    @classmethod
    def build_csv_row(cls, referral):
        person = referral.person
        return [
            cls.csv_value(person.get_full_name() if person else None),
            cls.csv_value(person.date_of_birth if person else None),
            cls.csv_value(person.passport_id if person else None),
            cls.csv_value(person.gwf if person else None),
            cls.csv_value(person.application_number if person else None),
            cls.csv_value(person.visa_status if person else None),
            cls.csv_value(
                referral.sponsor_full_name
                if referral.sponsor_full_name
                else (
                    f"{referral.sponsor_first_name or ''} "
                    f"{referral.sponsor_last_name or ''}"
                ).strip()
            ),
            cls.csv_value(referral.sponsor_date_of_birth),
            cls.csv_value(cls.get_sponsor_address(referral)),
            cls.csv_value(referral.sponsor_passport_details),
            cls.csv_value(referral.ar_utla_name),
        ]

    @classmethod
    def get_sponsor_address(cls, referral):
        person = referral.person
        if not person:
            return None

        accommodation_request = person.accommodation_request
        if not accommodation_request:
            return None

        primary_sponsor = accommodation_request.primary_sponsor
        if not primary_sponsor:
            return None

        primary_sponsor_uans = (
            primary_sponsor.application_unique_application_number or []
        )
        person_uans = person.application_number or []
        uans_intersection = set(primary_sponsor_uans) & set(person_uans)

        if uans_intersection:
            list_of_addresses = []
            for uan in uans_intersection:
                uan_address = cls.visa_applications_address_lookup.get(uan) or ""
                if uan_address:
                    list_of_addresses.append(uan_address)

            return list_of_addresses

        return None


class EscalatedChecksTable(tables.Table):
    latest_alert_date = CustomDateTimeColumn(verbose_name="Latest alert date")
    person_id = Column(verbose_name="Person")
    created_at = CustomDateTimeColumn(verbose_name="First shared to UKVI date")
    date_of_birth = CustomDateColumn(
        verbose_name="Date of birth",
        accessor="person__date_of_birth",
    )
    passport_id = Column(
        verbose_name="Passport number",
        accessor="person__passport_id",
    )
    gwf = Column(
        verbose_name="All linked GWFs",
        accessor="person__gwf",
    )
    application_number = Column(
        verbose_name="All linked UANs",
        accessor="person__application_number",
    )
    visa_status = Column(
        verbose_name="Visa status",
        accessor="person__visa_status",
    )

    def render_person_id(self, record: SafeguardingReferral):
        person = record.person
        if not person:
            return ""

        return format_html(
            '<a class="govuk-body-s govuk-link" href="{url}">{value}</a>',
            url=reverse("safeguarding:detail-overview", args=[person.id, record.id]),
            value=person.get_full_name(),
        )

    def render_passport_id(self, record: SafeguardingReferral):
        person = record.person
        if not person:
            return ""

        return person.passport_id[0] if person.passport_id else ""

    def render_gwf(self, record: SafeguardingReferral):
        person = record.person
        if not person:
            return ""

        gwfs = getattr(person, "gwf", None)
        if gwfs:
            if isinstance(gwfs, (list, tuple)):
                return format_html("<br>".join(str(g) for g in gwfs if g))
            return str(gwfs)
        return ""

    def render_application_number(self, record: SafeguardingReferral):
        person = record.person
        if not person:
            return ""

        application_numbers = getattr(person, "application_number", None)
        if application_numbers:
            if isinstance(application_numbers, (list, tuple)):
                return format_html(
                    "<br>".join(str(a) for a in application_numbers if a)
                )
            return str(application_numbers)
        return ""

    def render_visa_status(self, record: SafeguardingReferral):
        person = record.person
        if not person:
            return ""

        return render_to_string(
            "webapp/components/visa_status_tag/visa_status_tag.html",
            {"visa_status": person.visa_status},
        )

    def render_alerted_status(self, record: SafeguardingReferral):
        return render_to_string(
            "webapp/components/alerted_status_tag/alerted_status_tag.html",
            {"alerted_status": record.alerted_status},
        )

    class Meta:
        model = SafeguardingReferral
        template_name = "webapp/components/tables/table.html"
        fields = (
            "person_id",
            "visa_status",
            "alerted_status",
            "latest_alert_date",
            "created_at",
            "date_of_birth",
            "gwf",
            "application_number",
            "passport_id",
        )


class EscalatedChecksTableFilter(FilterPanelMixin, FilterSet):
    search = CharFilter(
        label="Search",
        method="search_filter",  # will be implemented by the Search PR
        help_text="Search the data in the table",
    )

    alerted_status = MultipleChoiceFilter(
        choices=SafeguardingReferral.AlertedStatus.choices,
        field_name="alerted_status",
        label="Alerted status",
        lookup_expr="exact",
        widget=CheckboxSelectMultipleWithTags(
            label_to_tag_colour=alerted_status_to_tag_colour
        ),
    )

    visa_status = MultipleChoiceFilter(
        choices=[(value.name, value.name) for value in visa_status_list_ordered],
        field_name="person__visa_status",
        label="Visa status",
        lookup_expr="exact",
        widget=CheckboxSelectMultipleWithTags(
            label_to_tag_colour=visa_status_to_tag_colour
        ),
    )

    created_at = CustomDateFromToRangeFilter(
        label="First shared to UKVI date",
        field_name="created_at",
        widget=StackedRangeInput(
            sub_widget=DatePicker,
            attrs={
                "from_hint": f"For example "
                f"{(datetime.today() - timedelta(days=50)).strftime('%d/%m/%Y')}",
                "to_hint": f"For example "
                f"{(datetime.today() - timedelta(days=20)).strftime('%d/%m/%Y')}",
                "from_label": "Date from",
                "to_label": "Date to",
            },
        ),
        error_messages={
            "invalid_range": "'Date from' must be before 'Date to'.",
        },
    )

    latest_alert_date = CustomDateFromToRangeFilter(
        label="Latest alert date",
        method="filter_latest_alert_date",
        widget=StackedRangeInput(
            sub_widget=DatePicker,
            attrs={
                "from_hint": f"For example "
                f"{(datetime.today() - timedelta(days=50)).strftime('%d/%m/%Y')}",
                "to_hint": f"For example "
                f"{(datetime.today() - timedelta(days=20)).strftime('%d/%m/%Y')}",
                "from_label": "Date from",
                "to_label": "Date to",
            },
        ),
        error_messages={
            "invalid_range": "'Date from' must be before 'Date to'.",
        },
    )

    date_of_birth = CustomDateFromToRangeFilter(
        label="Date of birth",
        field_name="person__date_of_birth",
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
        error_messages={
            "invalid_range": "'Date from' must be before 'Date to'.",
        },
    )

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, ESCALATED_CHECKS_SEARCH_FIELDS)

    def filter_latest_alert_date(self, queryset, _, value):
        if isinstance(value, slice):
            date_from = value.start
            date_to = value.stop
        else:
            return queryset
        if date_from and not isinstance(date_from, datetime):
            date_from = datetime.combine(date_from, datetime.min.time())
        if date_to and not isinstance(date_to, datetime):
            date_to = datetime.combine(date_to, datetime.max.time())
        queryset = queryset.exclude(latest_alert_date__isnull=True)
        if date_from:
            queryset = queryset.filter(latest_alert_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(latest_alert_date__lte=date_to)
        return queryset

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
            Field(
                "alerted_status", context={"label_size": "govuk-fieldset__legend--m"}
            ),
            Field("visa_status", context={"label_size": "govuk-fieldset__legend--m"}),
            Field(
                "latest_alert_date",
                context={
                    "legend_size": "govuk-fieldset__legend--m",
                },
            ),
            Field(
                "created_at",
                context={
                    "legend_size": "govuk-fieldset__legend--m",
                },
            ),
            Field(
                "date_of_birth",
                context={
                    "legend_size": "govuk-fieldset__legend--m",
                },
            ),
        )

        return form

    class Meta:
        model = SafeguardingReferral
        fields: list[str] = [
            "search",
            "alerted_status",
            "visa_status",
            "latest_alert_date",
            "created_at",
            "date_of_birth",
        ]


class EscalatedChecksView(
    UserActionsMixin, GroupRequiredMixin, SingleTableMixin, FilterView
):
    group_type = [GroupType.HOME_OFFICE, GroupType.MHCLG, GroupType.DEV]
    model = SafeguardingReferral
    table_class = EscalatedChecksTable
    filterset_class = EscalatedChecksTableFilter
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    paginator_class = LazyPaginator
    template_name = "safeguarding/escalated_checks_list.html"

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("person")
            .only(
                "created_at",
                "modified_at",
                "person_id",
                "alerted_status",
                "person__first_name",
                "person__last_name",
                "person__is_principal",
                "person__date_of_birth",
                "person__passport_id",
                "person__gwf",
                "person__application_number",
                "person__visa_status",
                "person__accommodation_request",
            )
        )
        latest_alert_date_subquery = (
            SafeguardingNotification.objects.filter(
                ar=OuterRef("person__accommodation_request")
            )
            .values("ar")
            .annotate(max_date=Max("created_at"))
            .values("max_date")[:1]
        )
        missing_first_name = Q(person__first_name__isnull=True) | Q(
            person__first_name__exact=""
        )
        missing_last_name = Q(person__last_name__isnull=True) | Q(
            person__last_name__exact=""
        )

        return qs.annotate(
            latest_alert_date=Coalesce(
                Subquery(latest_alert_date_subquery, output_field=DateTimeField()),
                F("created_at"),
            ),
            person_full_name=Case(
                When(
                    missing_first_name & missing_last_name,
                    then=Value(None, output_field=TextField()),
                ),
                default=Concat(
                    F("person__first_name"),
                    Value(" "),
                    F("person__last_name"),
                    output_field=TextField(),
                ),
                output_field=TextField(),
            ),
        ).order_by("-latest_alert_date", "person__first_name", "person__last_name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["referral_id"] = self.kwargs.get("referral_id")
        ctx["user_can_download"] = self.user_can_download(
            group_types=[GroupType.DEV, GroupType.HOME_OFFICE]
        )
        return ctx


class SafeguardingDetailOverviewView(
    PIISafeRecordNameMixin, PermissionsMixin, SummaryListView
):
    group_type = [
        GroupType.HOME_OFFICE,
        GroupType.MHCLG,
        GroupType.DEV,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "safeguarding/detail_view/detail_view_overview.html"
    model = MvPerson

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["referral_id"] = self.kwargs.get("referral_id")
        fields = []
        ar = getattr(self.object, "accommodation_request", None)
        user = self.request.user

        if ar:
            fields.append(
                (
                    "Host",
                    (host := ar.get_host_restrict_for_user(user))
                    and host.get_full_name(),
                )
            )
            fields.append(
                (
                    "Sponsor",
                    (sponsor := ar.get_primary_sponsor_restrict_for_user(user))
                    and sponsor.get_full_name(),
                )
            )
            for label, attr in [
                ("Lower tier local authority", "ltla_name"),
                ("Upper tier local authority", "utla_name"),
            ]:
                value = getattr(ar, attr, "") or None
                fields.append((label, value))

        ctx["fields"] = fields
        return ctx


def get_safeguarding_checks_summary_list_items(
    accommodation_request: MvAccommodationRequest,
    user: User,
    user_can_add_update: bool = False,
):
    if not accommodation_request:
        return []
    relevant_checks = accommodation_request.safeguarding_checks_restrict_for_user(user)
    accommodation_suitable_checks = relevant_checks.filter(
        check_type__id=CheckType.Id.ACCOMM_SUITABLE
    )
    accommodation_exists_checks = relevant_checks.filter(
        check_type__id=CheckType.Id.ACCOMM_EXISTS
    )
    sponsor_dbs_checks = relevant_checks.filter(check_type__id=CheckType.Id.SPONSOR_DBS)
    guest_arrived_checks = relevant_checks.filter(
        check_type__id=CheckType.Id.GROUP_ARRIVED
    )

    rendered_accommodation_suitable_checks: list = []
    rendered_accommodation_exists_checks: list = []
    rendered_sponsor_dbs_checks: list = []
    rendered_guest_arrived_checks: list = []

    for accommodation_suitable_check in accommodation_suitable_checks:
        rendered_accommodation_suitable_checks.append(
            (
                render_safeguarding_check_status(
                    accommodation_suitable_check.accommodation.filter(
                        is_principal=True
                    ).first(),
                    accommodation_suitable_check,
                    accommodation_request,
                    user_can_add_update=user_can_add_update,
                ),
            )
        )
    if not rendered_accommodation_suitable_checks:
        rendered_accommodation_suitable_checks = ["Checks not started"]

    for accommodation_exists_check in accommodation_exists_checks:
        rendered_accommodation_exists_checks.append(
            (
                render_safeguarding_check_status(
                    accommodation_exists_check.accommodation.filter(
                        is_principal=True
                    ).first(),
                    accommodation_exists_check,
                    accommodation_request,
                    user_can_add_update=user_can_add_update,
                ),
            )
        )
    if not rendered_accommodation_exists_checks:
        rendered_accommodation_exists_checks = ["Checks not started"]

    for sponsor_dbs_check in sponsor_dbs_checks:
        rendered_sponsor_dbs_checks.append(
            (
                render_safeguarding_check_status(
                    sponsor_dbs_check.sponsor.filter(is_principal=True).first(),
                    sponsor_dbs_check,
                    accommodation_request,
                    user_can_add_update=user_can_add_update,
                ),
            )
        )
    if not rendered_sponsor_dbs_checks:
        rendered_sponsor_dbs_checks = ["Checks not started"]

    for guest_arrived_check in guest_arrived_checks:
        rendered_guest_arrived_checks.append(
            (
                render_safeguarding_check_status(
                    guest_arrived_check.group.first(),
                    guest_arrived_check,
                    accommodation_request,
                    user_can_add_update=user_can_add_update,
                ),
            )
        )
    if not rendered_guest_arrived_checks:
        rendered_guest_arrived_checks = ["Checks not started"]

    return (
        [
            "Accommodation suitable",
            [rendered_accommodation_suitable_checks],
        ],
        ["Accommodation exists", [rendered_accommodation_exists_checks]],
        ["DBS check and Sponsor suitable", [rendered_sponsor_dbs_checks]],
        ["Guests have arrived in their accommodation", [rendered_guest_arrived_checks]],
    )


def render_safeguarding_check_status(
    associated_entity: str | None,
    check: DevCheckV2 | None = None,
    ar: MvAccommodationRequest | None = None,
    user_can_add_update: bool = False,
):
    context = {
        "associated_entity": associated_entity,
        "safeguarding_check_status": DevCheckV2.CheckStatus.NOT_STARTED,
        "user_can_add_update": user_can_add_update,
    }
    if check:
        context.update(
            {
                "safeguarding_check_status": check.check_status
                or DevCheckV2.CheckStatus.NOT_STARTED,
                "check_subtype": check.get_check_subtype_label(),
                "display_check_subtype_as_tag": check.check_type.id
                == CheckType.Id.SPONSOR_DBS
                and check.check_status != DevCheckV2.CheckStatus.FAILED,
                "note": check.note,
                "last_updated_at": check.last_updated_at,
                "last_updated_by": check.last_updated_by,
            }
        )
    if check and ar:
        context.update({"check": check.id, "obj": ar.id})
    return render_to_string(
        "webapp/components/safeguarding_check_tag/safeguarding_check_tag.html", context
    )


class SafeguardingDetailSafeguardingChecksView(
    PIISafeRecordNameMixin, PermissionsMixin, DetailView
):
    group_type = [
        GroupType.HOME_OFFICE,
        GroupType.MHCLG,
        GroupType.DEV,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "safeguarding/detail_view/detail_view_safeguarding_checks.html"
    model = MvPerson

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["referral_id"] = self.kwargs.get("referral_id")
        accommodation_request: MvAccommodationRequest = (
            self.object.accommodation_request
        )
        ctx["fields"] = get_safeguarding_checks_summary_list_items(
            accommodation_request, self.request.user
        )
        ctx["user_can_add_update"] = self.user_can_edit(
            group_types=[
                GroupType.DEV,
            ]
        )
        return ctx


class SafeguardingDetailLinkedRecordsView(
    PIISafeRecordNameMixin, PermissionsMixin, SummaryListView
):
    group_type = [
        GroupType.HOME_OFFICE,
        GroupType.MHCLG,
        GroupType.DEV,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "safeguarding/detail_view/detail_view_linked_records.html"
    model = MvPerson

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["referral_id"] = self.kwargs.get("referral_id")
        accommodation_request: MvAccommodationRequest | None = getattr(
            self.object, "accommodation_request", None
        )
        linked_records = []
        user = self.request.user

        if not accommodation_request:
            ctx["fields"] = linked_records
            return ctx

        primary_accommodation = (
            accommodation_request.get_primary_accommodation_restrict_for_user(user)
        )
        if primary_accommodation:
            linked_records.append(("Accommodation", primary_accommodation))

        guests = accommodation_request.get_people_restrict_for_user(user)
        if guests.exists():
            linked_records.append(("Guests", guests))

        primary_sponsor = accommodation_request.get_primary_sponsor_restrict_for_user(
            user
        )
        if primary_sponsor:
            linked_records.append(("Sponsor", primary_sponsor))

        active_host = accommodation_request.get_host_restrict_for_user(user)
        if active_host:
            linked_records.append(("Host", active_host))

        visa_applications = (
            accommodation_request.get_visa_applications_restrict_for_user(user)
        )
        if visa_applications.exists():
            linked_records.append(("Visa applications", visa_applications))

        ctx["fields"] = linked_records
        return ctx


class SafeguardingDetailPropertiesView(
    PIISafeRecordNameMixin, PermissionsMixin, TwoColumnSummaryListView
):
    group_type = [
        GroupType.HOME_OFFICE,
        GroupType.MHCLG,
        GroupType.DEV,
        GroupType.SERVICE_SUPPORT,
    ]
    template_name = "safeguarding/detail_view/detail_view_properties.html"
    model = MvPerson

    accommodation_request__accommodation_details_confirmed = SummaryListRow(
        verbose_name="Accommodation details confirmed"
    )
    accommodation_request__accommodation_id = SummaryListRow(
        verbose_name="Accommodation ID"
    )
    accommodation_request__old_split_accommodation_request = SummaryListRow(
        verbose_name="Accommodation request that was ungrouped"
    )
    accommodation_request__status = SummaryListRow(verbose_name="Accommodation Status")
    accommodation_request__active_eoi_host = SummaryListRow(
        verbose_name="Active EOI host"
    )
    accommodation_request__active_host = SummaryListRow(verbose_name="Active host")
    accommodation_request__linked_adverse_rematch = SummaryListRow(
        verbose_name="Adverse hit rematch required"
    )
    accommodation_request__assignee = SummaryListRow(verbose_name="Assignee")
    accommodation_request__bridging_accommodation_id = SummaryListRow(
        verbose_name="Bridging accommodation ID"
    )
    accommodation_request__bridging_accommodation_needed = SummaryListRow(
        verbose_name="Bridging accommodation needed"
    )
    accommodation_request__cancellation_reason = SummaryListRow(
        verbose_name="Cancellation reason"
    )
    accommodation_request__central_case_flag = SummaryListRow(
        verbose_name="Central case flag"
    )
    accommodation_request__checks_required = SummaryListRow(
        verbose_name="Checks required"
    )
    accommodation_request__comment = SummaryListRow(verbose_name="Comment")
    accommodation_request__confirmed_arrival_date = SummaryListRow(
        verbose_name="Confirmed arrival date"
    )
    accommodation_request__created_by = SummaryListRow(verbose_name="Created by")
    accommodation_request__date_from = SummaryListRow(verbose_name="Date from")
    accommodation_request__created_at = SummaryListRow(
        verbose_name="Date of application"
    )
    accommodation_request__edited_end_date_at = SummaryListRow(
        verbose_name="Edited end date at"
    )
    accommodation_request__is_uam = SummaryListRow(verbose_name="Eligible minor")
    accommodation_request__is_uam_edited_time = SummaryListRow(
        verbose_name="Eligible minor edited time"
    )
    accommodation_request__expected_check_in_date_confirmed = SummaryListRow(
        verbose_name="Expected check-in date confirmed"
    )
    accommodation_request__expected_end_date = SummaryListRow(
        verbose_name="Expected end date"
    )
    accommodation_request__expected_end_date_is_autogenerated = SummaryListRow(
        verbose_name="Expected end date is autogenerated"
    )
    accommodation_request__first_arrival_date = SummaryListRow(
        verbose_name="First arrival date"
    )
    accommodation_request__group_details_confirmed = SummaryListRow(
        verbose_name="Group details confirmed"
    )
    accommodation_request__group = SummaryListRow(verbose_name="Group ID")
    accommodation_request__have_notified_flag = SummaryListRow(
        verbose_name="Have notified flag"
    )
    accommodation_request__id = SummaryListRow(verbose_name="ID")
    accommodation_request__is_duplicate = SummaryListRow(verbose_name="Is duplicate")
    accommodation_request__is_eoi_host = SummaryListRow(verbose_name="Is EOI host")
    accommodation_request__is_principal = SummaryListRow(verbose_name="Is principal")
    accommodation_request__la_priority = SummaryListRow(verbose_name="LA priority")
    accommodation_request__la_priority_string = SummaryListRow(
        verbose_name="LA priority string"
    )
    accommodation_request__last_modified_by_org = SummaryListRow(
        verbose_name="Last comment by organisation"
    )
    accommodation_request__last_modified_at = SummaryListRow(
        verbose_name="Last modified at"
    )
    accommodation_request__last_modified_by = SummaryListRow(
        verbose_name="Last modified by"
    )
    accommodation_request__latest_application_date = SummaryListRow(
        verbose_name="Last application date"
    )
    accommodation_request__linked_adverse_hit = SummaryListRow(
        verbose_name="Linked adverse hit"
    )
    accommodation_request__ltla_name = SummaryListRow(
        verbose_name="Lower tier local authority"
    )
    accommodation_request__ltla_code = SummaryListRow(verbose_name="LTLA code")
    accommodation_request__match_id = SummaryListRow(verbose_name="Match ID")
    accommodation_request__max_age = SummaryListRow(verbose_name="Max age")
    accommodation_request__merged_accommodation_request = SummaryListRow(
        verbose_name="Merged accommodation request"
    )
    accommodation_request__min_age = SummaryListRow(verbose_name="Min age")
    accommodation_request__notional_data = SummaryListRow(verbose_name="Notional data")
    accommodation_request__number_of_people = SummaryListRow(
        verbose_name="Number of people"
    )
    accommodation_request__person_id = SummaryListRow(verbose_name="Person ID")
    accommodation_request__postcode = SummaryListRow(verbose_name="Postcode")
    accommodation_request__previous_accommodation = SummaryListRow(
        verbose_name="Previous accommodation"
    )
    accommodation_request__previous_eoi_hosts = SummaryListRow(
        verbose_name="Previous EOI hosts"
    )
    accommodation_request__previous_ids = SummaryListRow(verbose_name="Previous IDs")
    accommodation_request__primary_accommodation_id = SummaryListRow(
        verbose_name="Primary accommodation ID"
    )
    accommodation_request__primary_contact_can_be_contacted_by_phone = SummaryListRow(
        verbose_name="Primary contact can be contacted by phone"
    )
    accommodation_request__primary_contact_email = SummaryListRow(
        verbose_name="Primary contact email"
    )
    accommodation_request__primary_contact_email_after_decision = SummaryListRow(
        verbose_name="Primary contact email after decision"
    )
    accommodation_request__primary_contact_email_for_decision = SummaryListRow(
        verbose_name="Primary contact email for decision"
    )
    accommodation_request__primary_contact_email_for_questions = SummaryListRow(
        verbose_name="Primary contact email for questions"
    )
    accommodation_request__primary_contact_first_name = SummaryListRow(
        verbose_name="Primary contact first name"
    )
    accommodation_request__primary_contact_last_name = SummaryListRow(
        verbose_name="Primary contact last name"
    )
    accommodation_request__primary_contact_phone = SummaryListRow(
        verbose_name="Primary contact phone"
    )
    accommodation_request__primary_sponsor_id = SummaryListRow(
        verbose_name="Primary sponsor ID"
    )
    accommodation_request__checks_status = SummaryListRow(verbose_name="Request status")
    accommodation_request__safeguarding_status = SummaryListRow(
        verbose_name="Safeguarding status"
    )
    accommodation_request__sponsor_background_check_confirmed = SummaryListRow(
        verbose_name="Sponsor background check confirmed"
    )
    accommodation_request__sponsor_id = SummaryListRow(verbose_name="Sponsor ID")
    accommodation_request__sponsorship_certification_number_id = SummaryListRow(
        verbose_name="Sponsorship certification number"
    )
    accommodation_request__temporary_accommodation_id = SummaryListRow(
        verbose_name="Temporary accommodation ID"
    )
    accommodation_request__title = SummaryListRow(verbose_name="Title")
    accommodation_request__unique_application_number = SummaryListRow(
        verbose_name="Unique application number"
    )
    accommodation_request__utla_name = SummaryListRow(
        verbose_name="Upper tier local authority"
    )
    accommodation_request__utla_code = SummaryListRow(verbose_name="UTLA code")
    accommodation_request__viewer_group_names = SummaryListRow(
        verbose_name="Viewer group names"
    )
    accommodation_request__will_notify_la_central_case_flag = SummaryListRow(
        verbose_name="Will be notified"
    )
    accommodation_request__sponsor_withdrawn = SummaryListRow(
        verbose_name="Sponsor withdrawn"
    )

    def render_accommodation_request__status(self, value):
        return render_to_string(
            "webapp/components/"
            "accommodation_request_status/accommodation_request_status.html",
            {"accommodation_request_status": value},
        )

    def render_accommodation_request__checks_status(self, value):
        return render_to_string(
            "webapp/components/checks_status_tag/accommodation_checks_status_tag.html",
            {"accommodation_checks_status": value},
        )

    def render_accommodation_request__safeguarding_status(self, value):
        return render_to_string(
            "webapp/components/safeguarding_status_tag/safeguarding_status_tag.html",
            {"accommodation_safeguarding_status": value},
        )

    def render_accommodation_request__linked_adverse_rematch(self, value):
        return render_to_string(
            "webapp/components/"
            "adverse_rematch_status_tag/adverse_rematch_status_tag.html",
            {"adverse_rematch_status": value},
        )

    def render_accommodation_request__central_case_flag(self, value):
        return render_to_string(
            "webapp/components/central_case_flag_tag/central_case_flag_tag.html",
            {"central_case_flag": value},
        )

    def render_accommodation_request__is_uam(self, value):
        return render_to_string(
            "webapp/components/is_uam_tag/is_uam_tag.html",
            {"is_uam": value},
        )

    def render_accommodation_request__is_principal(self, value):
        return render_to_string(
            "webapp/components/is_principal_tag/is_principal_tag.html",
            {"is_principal": value},
        )

    def render_accommodation_request__linked_adverse_hit(self, value):
        return render_to_string(
            "webapp/components/linked_adverse_hit_tag/linked_adverse_hit_tag.html",
            {"linked_adverse_hit": value},
        )

    def render_accommodation_request__will_notify_la_central_case_flag(self, value):
        return render_to_string(
            "webapp/components/"
            "will_notify_la_central_case_flag_tag/"
            "will_notify_la_central_case_flag_tag.html",
            {"will_notify_la_central_case_flag": value},
        )

    class Meta:
        fields = [
            "accommodation_request__accommodation_details_confirmed",
            "accommodation_request__accommodation_id",
            "accommodation_request__old_split_accommodation_request",
            "accommodation_request__status",
            "accommodation_request__active_eoi_host",
            "accommodation_request__active_host",
            "accommodation_request__linked_adverse_rematch",
            "accommodation_request__assignee",
            "accommodation_request__bridging_accommodation_id",
            "accommodation_request__bridging_accommodation_needed",
            "accommodation_request__cancellation_reason",
            "accommodation_request__central_case_flag",
            "accommodation_request__checks_required",
            "accommodation_request__comment",
            "accommodation_request__confirmed_arrival_date",
            "accommodation_request__created_by",
            "accommodation_request__date_from",
            "accommodation_request__created_at",
            "accommodation_request__edited_end_date_at",
            "accommodation_request__is_uam",
            "accommodation_request__is_uam_edited_time",
            "accommodation_request__expected_check_in_date_confirmed",
            "accommodation_request__expected_end_date",
            "accommodation_request__expected_end_date_is_autogenerated",
            "accommodation_request__first_arrival_date",
            "accommodation_request__group_details_confirmed",
            "accommodation_request__group",
            "accommodation_request__have_notified_flag",
            "accommodation_request__id",
            "accommodation_request__is_duplicate",
            "accommodation_request__is_eoi_host",
            "accommodation_request__is_principal",
            "accommodation_request__la_priority",
            "accommodation_request__la_priority_string",
            "accommodation_request__last_modified_by_org",
            "accommodation_request__last_modified_at",
            "accommodation_request__last_modified_by",
            "accommodation_request__latest_application_date",
            "accommodation_request__linked_adverse_hit",
            "accommodation_request__ltla_name",
            "accommodation_request__ltla_code",
            "accommodation_request__match_id",
            "accommodation_request__max_age",
            "accommodation_request__merged_accommodation_request",
            "accommodation_request__min_age",
            "accommodation_request__notional_data",
            "accommodation_request__number_of_people",
            "accommodation_request__person_id",
            "accommodation_request__postcode",
            "accommodation_request__previous_accommodation",
            "accommodation_request__previous_eoi_hosts",
            "accommodation_request__previous_ids",
            "accommodation_request__primary_accommodation_id",
            "accommodation_request__primary_contact_can_be_contacted_by_phone",
            "accommodation_request__primary_contact_email",
            "accommodation_request__primary_contact_email_after_decision",
            "accommodation_request__primary_contact_email_for_decision",
            "accommodation_request__primary_contact_email_for_questions",
            "accommodation_request__primary_contact_first_name",
            "accommodation_request__primary_contact_last_name",
            "accommodation_request__primary_contact_phone",
            "accommodation_request__primary_sponsor_id",
            "accommodation_request__checks_status",
            "accommodation_request__safeguarding_status",
            "accommodation_request__sponsor_background_check_confirmed",
            "accommodation_request__sponsor_id",
            "accommodation_request__sponsorship_certification_number_id",
            "accommodation_request__temporary_accommodation_id",
            "accommodation_request__title",
            "accommodation_request__unique_application_number",
            "accommodation_request__utla_name",
            "accommodation_request__utla_code",
            "accommodation_request__viewer_group_names",
            "accommodation_request__will_notify_la_central_case_flag",
            "accommodation_request__sponsor_withdrawn",
        ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["referral_id"] = self.kwargs.get("referral_id")
        return ctx


class CentralSafeguardingTable(tables.Table):
    request: HttpRequest
    created_at = CustomDateTimeColumn(verbose_name="Date alerted")
    sponsor_names = Column(verbose_name="Sponsor")
    full_addresses = Column(verbose_name="Accommodation")
    name = Column(verbose_name="Alert")
    description = Column(verbose_name="Reason")

    def render_name(self, record, value):
        name = value
        dev_check_v2 = record.dev_check_v2
        if name:
            display_value = name
        elif dev_check_v2:
            display_value = dev_check_v2.get_check_failed_title()
        else:
            display_value = None

        url = "#"
        person_id = self.request.resolver_match.kwargs.get("pk")
        referral_id = self.request.resolver_match.kwargs.get("referral_id")
        notification_id = getattr(record, "id", None)

        if person_id and referral_id and notification_id:
            url = reverse(
                "safeguarding:detail-central-safeguarding-check-detail",
                kwargs={
                    "pk": person_id,
                    "referral_id": referral_id,
                    "notification_id": notification_id,
                },
            )

        if display_value:
            return format_html(
                '<a class="govuk-body-s govuk-link" href="{}">{}</a>',
                url,
                display_value,
            )

        return "Unknown alert type"

    class Meta:
        model = SafeguardingNotification
        template_name = "webapp/components/tables/table.html"
        fields = (
            "name",
            "created_at",
            "sponsor_names",
            "full_addresses",
            "description",
        )


class SafeguardingDetailCentralSafeguardingView(
    PIISafeRecordNameMixin,
    UserActionsMixin,
    GroupRequiredMixin,
    DetailView,
    SingleTableMixin,
    FormView,
):
    group_type = [GroupType.HOME_OFFICE, GroupType.MHCLG, GroupType.DEV]
    template_name = "safeguarding/detail_view/detail_view_central_safeguarding.html"
    model = MvPerson
    table_class = CentralSafeguardingTable
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    form_class = CentralSafeguardingAlertedStatusForm

    def get_details(self):
        person = self.get_object()
        referral = (
            SafeguardingReferral.objects.filter(person=person).order_by("id").first()
        )
        notifications = []
        accommodation_request = getattr(person, "accommodation_request", None)
        if accommodation_request:
            notifications = list(
                SafeguardingNotification.objects.filter(
                    ar=accommodation_request,
                ).order_by("-created_at")
            )
        return person, referral, notifications

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        _, referral, _ = self.get_details()
        kwargs["alerted_status"] = referral.alerted_status
        kwargs["user_can_edit"] = self.user_can_edit(
            group_types=[GroupType.DEV, GroupType.HOME_OFFICE]
        )
        return kwargs

    def get_success_url(self):
        return reverse(
            "safeguarding:detail-central-safeguarding",
            kwargs={
                "pk": self.get_object().pk,
                "referral_id": self.kwargs.get("referral_id"),
            },
        )

    def get_cancel_url(self):
        return reverse(
            "safeguarding:detail-central-safeguarding",
            kwargs={
                "pk": self.get_object().pk,
                "referral_id": self.kwargs.get("referral_id"),
            },
        )

    def get_gwfs(self, person):
        gwf = getattr(person, "gwf", None)
        if isinstance(gwf, (list, tuple)):
            return ", ".join(str(x) for x in gwf if x)
        return gwf or None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object = None

    def get_context_data(self, **kwargs):
        if self.object is None:
            self.object = self.get_object()
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = self.get_cancel_url()
        ctx["referral_id"] = self.kwargs.get("referral_id")
        person, _, _ = self.get_details()
        ctx["gwfs"] = self.get_gwfs(person)
        ctx["user_can_edit"] = self.user_can_edit(
            group_types=[GroupType.DEV, GroupType.HOME_OFFICE]
        )
        return ctx

    def form_valid(self, form):
        _, referral, _ = self.get_details()
        referral.alerted_status = form.cleaned_data["alerted_status"]
        referral.save()
        messages.success(self.request, "You changed the Alerted status")
        return super().form_valid(form)

    def get_table_data(self):
        _, _, notifications = self.get_details()

        return notifications


class SafeguardingDetailCentralSafeguardingAlertDetailView(
    UserActionsMixin, GroupRequiredMixin, DetailView
):
    group_type = [GroupType.HOME_OFFICE, GroupType.MHCLG, GroupType.DEV]
    template_name = "safeguarding/detail_view/central_safeguarding/check_detail.html"
    model = SafeguardingNotification
    pk_url_kwarg = "notification_id"
    context_object_name = "notification"

    def get_visa_applications(self, person):
        gwfs = person.gwf or []
        uans = person.application_number or []
        base_q = Q(gwf__in=gwfs) | Q(application_unique_application_number__in=uans)
        notification = self.get_object()

        if dev_check := notification.dev_check_v2:
            if (
                dev_check.check_type.id == CheckType.Id.SPONSOR_DBS
                and notification.sponsor_ids
            ):
                sponsors_uans = MvVolunteer.objects.filter(
                    id__in=notification.sponsor_ids
                ).values_list("application_unique_application_number", flat=True)
                uans = [uan for sublist in sponsors_uans if sublist for uan in sublist]
                return VisaApplication.objects.filter(
                    application_unique_application_number__in=uans
                )

            if (
                dev_check.check_type.id == CheckType.Id.ACCOMM_EXISTS
                and dev_check.person
            ):
                guest_uans = dev_check.person.values_list(
                    "application_number", flat=True
                )
                uans = [uan for sublist in guest_uans if sublist for uan in sublist]
                return VisaApplication.objects.filter(
                    application_unique_application_number__in=uans
                )

        return VisaApplication.objects.filter(base_q)

    def build_check_fields(self, notification, dev_check):
        if (
            notification.alert_type
            != SafeguardingNotification.AlertType.SAFEGUARDING_CHECK
            or not dev_check
        ):
            return None
        fields = []

        sponsor_names = notification.sponsor_names
        if sponsor_names:
            fields.append(("Sponsor", sponsor_names))

        full_addresses = notification.full_addresses
        if full_addresses:
            fields.append(("Accommodation", full_addresses))

        fields.append(("Reason", dev_check.get_check_subtype_label()))
        fields.append(("Comment", dev_check.note))
        return fields if fields else None

    def build_sponsor_withdrawn_fields(self, notification):
        if (
            notification.alert_type
            != SafeguardingNotification.AlertType.SPONSOR_WITHDRAWN
        ):
            return None
        return [
            ("Sponsor", notification.sponsor_names),
            ("Reason", notification.description),
        ]

    def build_visa_application_context(self, visa_applications):
        result = []
        for va in visa_applications:
            context = {
                "fields": [
                    ("GWF", va.gwf),
                    ("Visa status", va.visa_status),
                    ("Visa decision date", va.visa_decision_date),
                    (
                        "Application date",
                        va.application_event_datetime,
                    ),
                ],
                "title": va.title,
            }
            result.append(context)
        return result

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        referral_id = self.kwargs.get("referral_id")
        ctx["referral_id"] = referral_id
        person_pk = self.kwargs.get("pk")
        person = MvPerson.objects.get(pk=person_pk)
        notification = self.get_object()
        dev_check = notification.dev_check_v2
        ctx["person"] = person
        ctx["central_safeguarding_url"] = reverse(
            "safeguarding:detail-central-safeguarding",
            kwargs={"pk": person.pk, "referral_id": referral_id},
        )
        ctx["notification"] = notification
        ctx["check"] = dev_check
        ctx["reason"] = dev_check.get_check_subtype_label() if dev_check else None
        ctx["visa_applications"] = self.build_visa_application_context(
            self.get_visa_applications(person)
        )
        ctx["check_fields"] = self.build_check_fields(notification, dev_check)
        ctx["sponsor_withdrawn_fields"] = self.build_sponsor_withdrawn_fields(
            notification
        )
        return ctx
