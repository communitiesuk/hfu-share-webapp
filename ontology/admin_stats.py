from datetime import datetime, timedelta, timezone
from typing import Tuple

from auditlog.models import LogEntry

from accounts.models import User
from ontology.models import (
    DevCheckV2,
    MvAccommodation,
    MvAccommodationRequest,
    MvGroup,
    MvInteraction,
    MvPerson,
    MvVolunteer,
    ReassignmentRequest,
    SafeguardingReferral,
    VisaInformationRequest,
)

STATS_START_DATE = datetime(2026, 1, 1, tzinfo=timezone.utc)

RESOURCE_LIST = [
    MvAccommodation,
    MvAccommodationRequest,
    DevCheckV2,
    MvInteraction,
    MvGroup,
    MvPerson,
    MvVolunteer,
    ReassignmentRequest,
    SafeguardingReferral,
    VisaInformationRequest,
]


def get_next_month_and_year(source_date) -> Tuple[int, int]:
    month: int = source_date.month
    year: int = source_date.year + month // 12
    next_month: int = month % 12 + 1
    # Pick the first day of the next month
    next_month_dt = datetime(year, next_month, 1, tzinfo=timezone.utc)
    return next_month_dt.month, next_month_dt.year


def get_report_end_date() -> datetime:
    now = datetime.now(tz=timezone.utc)
    final_month, final_year = get_next_month_and_year(now)
    return datetime(final_year, final_month, 1, tzinfo=timezone.utc)


def generate_monthly_audit_stats(start_date=STATS_START_DATE) -> dict:
    """
    Generate stats for monthly audit events per model
    """
    stats = {}
    report_end_date = get_report_end_date()

    for resource in RESOURCE_LIST:
        # query count number of auditlog entries between now and start date
        log_entries_for_resource = LogEntry.objects.get_for_model(
            model=resource
        ).filter(timestamp__gte=start_date, timestamp__lte=report_end_date)
        stats[resource.__name__] = {"Total changes": log_entries_for_resource.count()}

        # Then add the stats breakdown by month
        reporting_month_start = start_date
        # Get the next month, making sure we handle Dec->Jan
        next_month, next_year = get_next_month_and_year(reporting_month_start)
        reporting_month_end = start_date.replace(month=next_month, year=next_year)

        while reporting_month_end <= report_end_date:
            log_entries_by_month = log_entries_for_resource.filter(
                timestamp__gte=reporting_month_start, timestamp__lt=reporting_month_end
            )
            month_key_name = reporting_month_start.strftime("%B %Y")
            stats[resource.__name__][month_key_name] = log_entries_by_month.count()

            # Increment the reporting month window
            reporting_month_start = reporting_month_end
            next_month, next_year = get_next_month_and_year(reporting_month_end)
            reporting_month_end = reporting_month_end.replace(
                month=next_month, year=next_year
            )

    return stats


def get_user_stats() -> dict:
    user_stats = {
        "total_users": 0,
        "users_active_in_last_90_days": 0,
        "new_users_in_last_90_days": 0,
    }
    now = datetime.now(tz=timezone.utc)
    ninety_days_ago = now - timedelta(days=90)

    count_users_active_in_last_90_days = User.objects.filter(
        last_login__gte=ninety_days_ago
    ).count()
    count_new_users_in_last_90_days = User.objects.filter(
        date_joined__gte=ninety_days_ago
    ).count()
    count_total_users = User.objects.count()

    user_stats["total_users"] = count_total_users
    user_stats["users_active_in_last_90_days"] = count_users_active_in_last_90_days
    user_stats["new_users_in_last_90_days"] = count_new_users_in_last_90_days

    return user_stats
