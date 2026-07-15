from django.urls import path

from .views import (
    UamsDetailLinkedRecordsView,
    UamsDetailOverviewView,
    UamsDetailPropertiesView,
    UamsDownloadAttachmentView,
    UamsDownloadGOVUKFormsAttachmentView,
    UamsFilesView,
    UamsListView,
)

app_name = "uams"
urlpatterns = [
    path(
        "",
        UamsListView.as_view(),
        name="uams",
    ),
    path(
        "<str:pk>/overview",
        UamsDetailOverviewView.as_view(),
        name="detail-overview",
    ),
    path(
        "<str:pk>/properties",
        UamsDetailPropertiesView.as_view(),
        name="detail-properties",
    ),
    path(
        "<str:pk>/linked-records",
        UamsDetailLinkedRecordsView.as_view(),
        name="detail-linked-records",
    ),
    path(
        "<str:pk>/files",
        UamsFilesView.as_view(),
        name="detail-files",
    ),
    path(
        "<str:pk>/download-attachment/<str:metadata_id>",
        UamsDownloadAttachmentView.as_view(),
        name="download-attachment",
    ),
    path(
        "<str:pk>/download-forms-attachment/<str:consent_file_type>",
        UamsDownloadGOVUKFormsAttachmentView.as_view(),
        name="download-govuk-forms-attachment",
    ),
]
