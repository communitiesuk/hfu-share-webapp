from django.urls import include, path

from deduplication.views import SelectRecordTypeView

app_name = "deduplication"
urlpatterns = [
    path(
        "",
        SelectRecordTypeView.as_view(),
        name="select-record-type",
    ),
    path("sponsors/", include("sponsors.urls", namespace="sponsors")),
    path("guests/", include("guests.urls", namespace="guests")),
    path("accommodations/", include("accommodations.urls", namespace="accommodations")),
]
