from django.urls import path

from .views import (
    ASSIGN_TO_LOCAL_AUTHORITY_FORMS,
    AssignToLocalAuthorityFormWizard,
    UnassignedAccommodationRequestsListView,
)

assign_to_local_authority_wizard = AssignToLocalAuthorityFormWizard.as_view(
    ASSIGN_TO_LOCAL_AUTHORITY_FORMS,
    url_name="unassigned-accommodation-requests:assign-to-local-authority-step",
)

app_name = "unassigned-accommodation-requests"
urlpatterns = [
    path(
        "",
        UnassignedAccommodationRequestsListView.as_view(),
        name="unassigned-accommodation-requests",
    ),
    path(
        "<str:pk>/assign-to-local-authority/<str:step>/",
        assign_to_local_authority_wizard,
        name="assign-to-local-authority-step",
    ),
    path(
        "<str:pk>/assign-to-local-authority",
        assign_to_local_authority_wizard,
        name="assign-to-local-authority",
    ),
]
