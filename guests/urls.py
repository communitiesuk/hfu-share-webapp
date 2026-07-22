from django.urls import path

from .views import (
    GuestDetailActionsView,
    GuestDetailHistoryView,
    GuestDetailLinkedRecordsView,
    GuestDetailOverviewView,
    GuestDetailPropertiesView,
    GuestEditView,
    GuestsListView,
    GuestVisaApplicationsListView,
)

app_name = "guests"
urlpatterns = [
    path(
        "",
        GuestsListView.as_view(),
        name="guests",
    ),
    path(
        "<str:pk>/overview",
        GuestDetailOverviewView.as_view(),
        name="detail-overview",
    ),
    path(
        "<str:pk>/actions",
        GuestDetailActionsView.as_view(),
        name="detail-actions",
    ),
    path(
        "<str:pk>/linked-records",
        GuestDetailLinkedRecordsView.as_view(),
        name="detail-linked-records",
    ),
    path(
        "<str:pk>/linked-records/visa-applications",
        GuestVisaApplicationsListView.as_view(),
        name="detail-linked-records-visa-applications",
    ),
    path(
        "<str:pk>/properties",
        GuestDetailPropertiesView.as_view(),
        name="detail-properties",
    ),
    path(
        "<str:pk>/history",
        GuestDetailHistoryView.as_view(),
        name="detail-history",
    ),
    path(
        "<str:pk>/edit/",
        GuestEditView.as_view(),
        name="detail-edit",
    ),
]
