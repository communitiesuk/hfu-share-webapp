from django.urls import path

from .views import (
    ASSIGN_LOCAL_AUTHORITY_FORMS,
    AssignLocalAuthorityFormWizard,
    UnassignedAccommodationRequestsListView,
)

assign_local_authority_wizard = AssignLocalAuthorityFormWizard.as_view(
    ASSIGN_LOCAL_AUTHORITY_FORMS,
    url_name="unassigned-accommodation-requests:assign-local-authority-step",
)

app_name = "unassigned-accommodation-requests"
urlpatterns = [
    path(
        "",
        UnassignedAccommodationRequestsListView.as_view(),
        name="unassigned-accommodation-requests",
    ),
    path(
        "<str:pk>/assign-local-authority/<str:step>/",
        assign_local_authority_wizard,
        name="assign-local-authority-step",
    ),
    path(
        "<str:pk>/assign-local-authority",
        assign_local_authority_wizard,
        name="assign-local-authority",
    ),
]
