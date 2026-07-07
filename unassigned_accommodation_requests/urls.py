from django.urls import path

from .views import UnassignedAccommodationRequestsListView

app_name = "unassigned-accommodation-requests"
urlpatterns = [
    path(
        "",
        UnassignedAccommodationRequestsListView.as_view(),
        name="unassigned-accommodation-requests",
    )
]
