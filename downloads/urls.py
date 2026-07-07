from django.urls import path

from .views import DownloadsPage

app_name = "downloads"
urlpatterns = [
    path(
        "",
        DownloadsPage.as_view(),
        name="download-page",
    ),
]
