from datetime import date, datetime, time, timezone
from typing import TypedDict

from django.contrib.admin import FieldListFilter, SimpleListFilter
from django.db.models import CharField, DateTimeField, F, Q, QuerySet, Value
from django.db.models.functions import Concat, Trim
from django.utils import timezone as django_timezone
from django.utils.safestring import SafeString

from ontology.admin_forms import DateRangeForm
from ontology.models import (
    CheckType,
)

GO_LIVE_DATE = datetime(2025, 9, 15, tzinfo=timezone.utc)


class ChecksSinceShareGoLiveFilter(SimpleListFilter):
    title = "Non-principal checks since 'Go live'"
    parameter_name = "since_share_go_live"

    def lookups(self, request, model_admin):
        return (
            ("sponsors", "Sponsors"),
            ("accommodations", "Accommodations"),
        )

    def queryset(self, request, queryset):
        if self.value() == "sponsors":
            return queryset.filter(
                Q(check_type_id=CheckType.Id.SPONSOR_DBS)
                & Q(create_at__gte=GO_LIVE_DATE)
                & Q(sponsor__is_principal=False)
            )
        elif self.value() == "accommodations":
            return queryset.filter(
                Q(
                    check_type_id__in=[
                        CheckType.Id.ACCOMM_SUITABLE,
                        CheckType.Id.ACCOMM_EXISTS,
                    ]
                )
                & Q(create_at__gte=GO_LIVE_DATE)
                & Q(accommodation__is_principal=False)
            )


class ARsCreatedOrModifiedSinceShareGoLiveFilter(SimpleListFilter):
    title = "Created or modified ARs since 'Go live'"
    parameter_name = "created_or_modified_ars_since_share_go_live"

    def lookups(self, request, model_admin):
        return (
            (
                "created_or_modified_ars_since_share_go_live",
                "Created or modified since Go-live",
            ),
        )

    def queryset(self, request, queryset):
        if self.value() == "created_or_modified_ars_since_share_go_live":
            return queryset.filter(
                Q(last_modified_at__gte=GO_LIVE_DATE) | Q(created_at__gte=GO_LIVE_DATE)
            )


class GuestsWithIncorrectTitlesExcludingDuplicatesFilter(SimpleListFilter):
    title = "Incorrect titles"
    parameter_name = "incorrect_titles"

    def lookups(self, request, model_admin):
        return (
            ("exclude_duplicates", "Yes (Exclude Duplicates)"),
            ("include_duplicates", "Yes (Include Duplicates)"),
        )

    def queryset(self, request, queryset):
        if self.value() in ["exclude_duplicates", "include_duplicates"]:
            qs = queryset.annotate(
                expected_title=Trim(
                    Concat(
                        "first_name", Value(" "), "last_name", output_field=CharField()
                    )
                )
            ).exclude(title=F("expected_title"))

            if self.value() == "exclude_duplicates":
                qs = qs.exclude(title__contains="[Duplicate]")

            return qs

        return None


class ListFilterChoices(TypedDict):
    selected: bool
    query_string: str
    display: SafeString


class DateRangeFilter(FieldListFilter):
    template = "admin/date_range_filter.html"

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field_path = field_path
        self.lookup_kwarg_gte, self.lookup_kwarg_lte = self._get_param_names()
        super().__init__(field, request, params, model, model_admin, field_path)
        self.title = self._get_title(field)
        self.form = self._get_form(request)

    def _is_datetime_field(self) -> bool:
        return isinstance(self.field, DateTimeField)

    @staticmethod
    def _start_of_day(d: date) -> datetime:
        dt = datetime.combine(d, time.min)
        return django_timezone.make_aware(dt) if django_timezone.is_naive(dt) else dt

    @staticmethod
    def _end_of_day(d: date) -> datetime:
        dt = datetime.combine(d, time.max)
        return django_timezone.make_aware(dt) if django_timezone.is_naive(dt) else dt

    def _get_title(self, field) -> str:
        return (
            field.verbose_name.capitalize()
            if getattr(field, "verbose_name", None)
            else field.name
        )

    def _get_param_names(self) -> tuple[str, str]:
        return f"{self.field_path}__gte", f"{self.field_path}__lte"

    def _get_initial_values(self, request) -> dict[str, str]:
        return {
            "start": request.GET.get(self.lookup_kwarg_gte, ""),
            "end": request.GET.get(self.lookup_kwarg_lte, ""),
        }

    def _get_form(self, request) -> DateRangeForm:
        initial = self._get_initial_values(request)
        if initial["start"] or initial["end"]:
            return DateRangeForm(initial)
        return DateRangeForm()

    def expected_parameters(self) -> list[str | None]:
        return [self.lookup_kwarg_gte, self.lookup_kwarg_lte]

    def _get_filter_values(self, request) -> dict[str, date] | None:
        form = self._get_form(request)
        if form.is_valid():
            return form.cleaned_data
        return None

    def _get_query_filter(self, values: dict[str, date]) -> dict[str, date | datetime]:
        filters = {}
        if values.get("start"):
            filters[f"{self.field_path}__gte"] = (
                self._start_of_day(values["start"])
                if self._is_datetime_field()
                else values["start"]
            )
        if values.get("end"):
            filters[f"{self.field_path}__lte"] = (
                self._end_of_day(values["end"])
                if self._is_datetime_field()
                else values["end"]
            )
        return filters

    def _get_context(self, request) -> dict:
        return {
            "spec": self,
            "request": request,
            "form": self.form,
        }

    def choices(self, changelist):
        remove_query_string = changelist.get_query_string(
            remove=self.expected_parameters()
        )
        self.remove_query_string = remove_query_string
        yield {
            "selected": False,
            "system_name": self.field_path.replace("__", "-"),
            "query_string": remove_query_string,
        }

    def queryset(self, request, queryset) -> "QuerySet":
        values = self._get_filter_values(request)
        if values:
            filters = self._get_query_filter(values)
            if filters:
                return queryset.filter(**filters)
        return queryset
