from django.urls import path

from .views import (
    SponsorDetailActionsView,
    SponsorDetailHistoryView,
    SponsorDetailLinkedRecordsView,
    SponsorDetailOverviewView,
    SponsorDetailPropertiesView,
    SponsorEditView,
    SponsorsListView,
)

app_name = "sponsors"
urlpatterns = [
    path(
        "",
        SponsorsListView.as_view(),
        name="sponsors",
    ),
    path(
        "<str:pk>/overview",
        SponsorDetailOverviewView.as_view(),
        name="detail-overview",
    ),
    path(
        "<str:pk>/actions",
        SponsorDetailActionsView.as_view(),
        name="detail-actions",
    ),
    path(
        "<str:pk>/linked-records",
        SponsorDetailLinkedRecordsView.as_view(),
        name="detail-linked-records",
    ),
    path(
        "<str:pk>/properties",
        SponsorDetailPropertiesView.as_view(),
        name="detail-properties",
    ),
    path(
        "<str:pk>/history",
        SponsorDetailHistoryView.as_view(),
        name="detail-history",
    ),
    path(
        "<str:pk>/edit/",
        SponsorEditView.as_view(),
        name="detail-edit",
    ),
]
