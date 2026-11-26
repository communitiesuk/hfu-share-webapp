import csv
import io
import time
from collections import Counter

from django.http import StreamingHttpResponse
from django.utils import timezone
from django.utils.formats import date_format
from django.views.generic.edit import FormView
from sentry_sdk import logger as sentry_logger

from accounts.enums import GroupType
from case_management.settings import sentry_sdk
from downloads.forms import (
    DownloadsTypeForm,
    DownloadType,
)
from downloads.helpers import (
    build_csv_header,
    build_csv_row,
    build_csv_row_plan,
    determine_redacted_fields,
)
from downloads.utils import (
    get_duration_bucket,
    get_file_size_bucket,
    get_row_count_bucket,
)
from ontology.mixins import get_las_for_user
from ontology.models import (
    ExportToolObject,
    MvAccommodation,
    MvPerson,
    MvVolunteer,
    SponsorshipCertificationForm,
    VisaApplication,
)
from webapp.mixins import PermissionsMixin, SectionHeadingMixin

BATCH_SIZE = 1000


class DownloadsPage(SectionHeadingMixin, PermissionsMixin, FormView):
    group_type = [
        GroupType.DEV,
        GroupType.LOCAL_AUTHORITY,
        GroupType.DEVOLVED_ADMINISTRATION,
        GroupType.SERVICE_SUPPORT,
        GroupType.HOME_OFFICE,
        GroupType.MHCLG,
    ]
    export_model_mapping = {
        DownloadType.GUESTS: MvPerson,
        DownloadType.VISA_APPLICATIONS: VisaApplication,
        DownloadType.SPONSORS: MvVolunteer,
        DownloadType.ACCOMMODATION: MvAccommodation,
        DownloadType.UAMS: SponsorshipCertificationForm,
        DownloadType.ALL: ExportToolObject,
    }

    template_name = "downloads/download.html"
    form_class = DownloadsTypeForm

    def form_valid(self, form):  # noqa: C901
        download_type = form.cleaned_data["download_type"]

        user_group_types = self.request.user.get_group_types()
        unrestricted_user = bool(
            user_group_types.intersection(
                {
                    GroupType.DEV,
                    GroupType.SERVICE_SUPPORT,
                    GroupType.HOME_OFFICE,
                    GroupType.MHCLG,
                }
            )
        )

        user_la_only = (
            GroupType.LOCAL_AUTHORITY in user_group_types
        ) and not unrestricted_user

        ltla_names, utla_names = None, None

        if user_la_only:
            ltla_names, utla_names = get_las_for_user(self.request.user)
            ltla_names, utla_names = set(ltla_names), set(utla_names)

        export_model = self.export_model_mapping.get(download_type)
        if not export_model:
            form.add_error("download_type", "Invalid download type selected.")
            return self.form_invalid(form)

        timestamp = date_format(timezone.localtime(), "y-m-d_H-i")

        def stream_csv_with_iterator():
            counts = Counter(batch_count=0, row_count=0, file_size_bytes=0)
            start = time.perf_counter()

            # Prepare the CSV writer
            buffer = io.StringIO()
            writer = csv.writer(buffer)

            # Build the CSV header
            field_names = build_csv_header(export_model, download_type)

            # Build plan for rendering each row
            row_plan = build_csv_row_plan(export_model, field_names)

            # Yield header
            writer.writerow(field_names)
            chunk = buffer.getvalue().encode("utf-8")
            counts["file_size_bytes"] += len(chunk)
            yield chunk
            buffer.seek(0)
            buffer.truncate(0)

            # Fetch model objects in batches
            # Fetches next batch after current model_objects_iterator
            # were processed in for loop
            model_objects = export_model.objects.get_for_user(self.request.user)

            if download_type == DownloadType.ALL:
                if unrestricted_user:
                    model_objects = export_model.objects.exclude_browser_test_records(
                        export_model.objects.get_queryset_without_annotations()
                    )
                if form.cleaned_data["date_from"]:
                    model_objects = model_objects.filter(
                        latest_application_date__gte=form.cleaned_data["date_from"]
                    )
                if form.cleaned_data["date_to"]:
                    model_objects = model_objects.filter(
                        latest_application_date__lte=form.cleaned_data["date_to"]
                    )

            model_objects_iterator = model_objects.iterator(chunk_size=BATCH_SIZE)

            counts["batch_count"] = 0
            seen_rows = set()
            for model_object in model_objects_iterator:
                redacted_fields = {}

                if download_type == DownloadType.ALL and user_la_only:
                    redacted_fields = determine_redacted_fields(
                        model_object, ltla_names, utla_names
                    )

                row = build_csv_row(model_object, row_plan, redacted_fields)

                if download_type == DownloadType.ALL and user_la_only:
                    row_str = "".join(row)
                    if row_str in seen_rows:
                        continue

                    seen_rows.add(row_str)

                writer.writerow(row)
                counts["batch_count"] += 1
                counts["row_count"] += 1

                # Yield rows in batches
                if counts["batch_count"] >= BATCH_SIZE:
                    chunk = buffer.getvalue().encode("utf-8")
                    counts["file_size_bytes"] += len(chunk)
                    yield chunk
                    buffer.seek(0)
                    buffer.truncate(0)
                    counts["batch_count"] = 0

            # Yield any remaining rows
            if buffer.tell() > 0:
                chunk = buffer.getvalue().encode("utf-8")
                counts["file_size_bytes"] += len(chunk)
                yield chunk
                buffer.seek(0)
                buffer.truncate(0)

            duration = time.perf_counter() - start

            # Send metrics for completed download which helps us track timeouts
            sentry_sdk.metrics.count(
                "completed_csv_download",
                1,
                attributes={
                    "download_type": download_type,
                    "user_id": self.request.user.id,
                },
            )

            attributes = {
                "download_type": download_type,
                "duration_bucket": get_duration_bucket(duration),
                "row_count_bucket": get_row_count_bucket(counts["row_count"]),
                "file_size_bucket": get_file_size_bucket(counts["file_size_bytes"]),
            }

            sentry_sdk.metrics.distribution(
                "csv_download_duration",
                duration,
                unit="second",
                attributes=attributes,
            )

            sentry_sdk.metrics.distribution(
                "csv_download_size",
                counts["file_size_bytes"],
                unit="byte",
                attributes=attributes,
            )

            sentry_sdk.metrics.distribution(
                "csv_download_rows",
                counts["row_count"],
                unit="none",
                attributes=attributes,
            )

        response = StreamingHttpResponse(
            stream_csv_with_iterator(), content_type="text/csv; charset=utf-8"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{download_type}_{timestamp}.csv"'
        )

        # Send structured log info to Sentry so we can measure this metric
        sentry_logger.info(
            "METRIC: Download type {download_type} requested by user ID {user_id}",
            download_type=download_type,
            user_id=self.request.user.id,
        )
        # Send metric as well as the log
        sentry_sdk.metrics.count(
            "csv_download",
            1,
            attributes={
                "download_type": download_type,
                "user_id": self.request.user.id,
            },
        )

        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user_can_download"] = self.user_can_download(
            group_types=[
                GroupType.DEV,
                GroupType.LOCAL_AUTHORITY,
                GroupType.DEVOLVED_ADMINISTRATION,
                GroupType.MHCLG,
                GroupType.HOME_OFFICE,
            ]
        )
        return kwargs
