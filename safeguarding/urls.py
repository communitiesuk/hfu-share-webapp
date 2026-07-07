from django.urls import path

from .views import (
    DownloadEscalatedChecksCSVView,
    EscalatedChecksView,
    SafeguardingDetailCentralSafeguardingAlertDetailView,
    SafeguardingDetailCentralSafeguardingView,
    SafeguardingDetailLinkedRecordsView,
    SafeguardingDetailOverviewView,
    SafeguardingDetailPropertiesView,
    SafeguardingDetailSafeguardingChecksView,
)

app_name = "safeguarding"
urlpatterns = [
    path(
        "escalated_checks",
        EscalatedChecksView.as_view(),
        name="escalated_checks",
    ),
    path(
        "<str:pk>/overview/<str:referral_id>",
        SafeguardingDetailOverviewView.as_view(),
        name="detail-overview",
    ),
    path(
        "<str:pk>/safeguarding-checks/<str:referral_id>",
        SafeguardingDetailSafeguardingChecksView.as_view(),
        name="detail-safeguarding-checks",
    ),
    path(
        "<str:pk>/linked-records/<str:referral_id>",
        SafeguardingDetailLinkedRecordsView.as_view(),
        name="detail-linked-records",
    ),
    path(
        "<str:pk>/properties/<str:referral_id>",
        SafeguardingDetailPropertiesView.as_view(),
        name="detail-properties",
    ),
    path(
        "<str:pk>/central-safeguarding/<str:referral_id>",
        SafeguardingDetailCentralSafeguardingView.as_view(),
        name="detail-central-safeguarding",
    ),
    path(
        "<str:pk>/central-safeguarding/<str:referral_id>/alert/<str:notification_id>",
        SafeguardingDetailCentralSafeguardingAlertDetailView.as_view(),
        name="detail-central-safeguarding-check-detail",
    ),
    path(
        "escalated_checks/download",
        DownloadEscalatedChecksCSVView.as_view(),
        name="escalated_checks_download_csv",
    ),
]
