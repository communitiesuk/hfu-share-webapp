from django.urls import path

from .views import (
    VIRCloseConfirmView,
    VIRListView,
    VIRReopenConfirmView,
    VisaApplicationLinkedRecordsView,
    VisaApplicationListView,
    VisaApplicationOverviewView,
    VisaApplicationPropertiesView,
    VisaApplicationVIRView,
)

app_name = "visa-applications"
urlpatterns = [
    path(
        "",
        VisaApplicationListView.as_view(),
        name="visa-applications",
    ),
    path(
        "visa-information-requests",
        VIRListView.as_view(),
        name="visa-information-requests",
    ),
    path(
        "<str:pk>/overview",
        VisaApplicationOverviewView.as_view(),
        name="detail-overview",
    ),
    path(
        "<str:pk>/properties",
        VisaApplicationPropertiesView.as_view(),
        name="detail-properties",
    ),
    path(
        "<str:pk>/linked-records",
        VisaApplicationLinkedRecordsView.as_view(),
        name="detail-linked-records",
    ),
    path(
        "<str:pk>/vir",
        VisaApplicationVIRView.as_view(),
        name="detail-vir",
    ),
    path(
        "<str:pk>/vir/close/confirm",
        VIRCloseConfirmView.as_view(),
        name="close-vir-confirm",
    ),
    path(
        "<str:pk>/vir/reopen/confirm",
        VIRReopenConfirmView.as_view(),
        name="reopen-vir-confirm",
    ),
]
