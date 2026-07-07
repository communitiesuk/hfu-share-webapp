from django.urls import path

from .views import (
    CancelReassignmentRequestView,
    ReassignmentRequestDetailView,
    ReassignmentRequestsMadePageView,
    ReassignmentRequestsReceivedPageView,
)

app_name = "reassignment-requests"
urlpatterns = [
    path(
        "made/",
        ReassignmentRequestsMadePageView.as_view(),
        name="made",
    ),
    path(
        "received/",
        ReassignmentRequestsReceivedPageView.as_view(),
        name="received",
    ),
    path(
        "made/<str:pk>/",
        ReassignmentRequestDetailView.as_view(),
        name="detail-made",
    ),
    path(
        "received/<str:pk>/",
        ReassignmentRequestDetailView.as_view(),
        name="detail-received",
    ),
    path(
        "made/<str:pk>/cancel",
        CancelReassignmentRequestView.as_view(),
        name="cancel-made",
    ),
    path(
        "received/<str:pk>/cancel",
        CancelReassignmentRequestView.as_view(),
        name="cancel-received",
    ),
]
