from django.urls import path

from .views import (
    AccommodationDetailActionsView,
    AccommodationDetailHistoryView,
    AccommodationDetailLinkedRecordsView,
    AccommodationDetailOverviewView,
    AccommodationDetailPropertiesView,
    AccommodationEditView,
    AccommodationsListView,
    PostcodeSearchView,
)

app_name = "accommodations"
urlpatterns = [
    path(
        "",
        AccommodationsListView.as_view(),
        name="accommodations",
    ),
    path(
        "<str:pk>/edit",
        AccommodationEditView.as_view(),
        name="edit",
    ),
    path(
        "<str:pk>/overview",
        AccommodationDetailOverviewView.as_view(),
        name="detail-overview",
    ),
    path(
        "<str:pk>/actions",
        AccommodationDetailActionsView.as_view(),
        name="detail-actions",
    ),
    path(
        "<str:pk>/linked-records",
        AccommodationDetailLinkedRecordsView.as_view(),
        name="detail-linked-records",
    ),
    path(
        "<str:pk>/properties",
        AccommodationDetailPropertiesView.as_view(),
        name="detail-properties",
    ),
    path(
        "<str:pk>/history",
        AccommodationDetailHistoryView.as_view(),
        name="detail-history",
    ),
    path(
        "postcode-search",
        PostcodeSearchView.as_view(),
        name="postcode-search",
    ),
]
