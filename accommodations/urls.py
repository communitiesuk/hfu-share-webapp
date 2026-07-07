from django.urls import path

from deduplication.views import (
    SELECT_AND_REVIEW_RECORDS_FORMS,
    UNDO_DEDUPLICATION_RECORDS_FORMS,
    SelectAndReviewAccommodationRecordsFormWizard,
    UndoDeduplicationAccommodationRecordsFormWizard,
)

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

select_and_review_accommodation_records_form_wizard = (
    SelectAndReviewAccommodationRecordsFormWizard.as_view(
        SELECT_AND_REVIEW_RECORDS_FORMS,
        url_name="deduplication:accommodations:select-and-review-records-manual-step",  # type: ignore[call-arg]
    )
)

undo_deduplication_accommodations_records_form_wizard = (
    UndoDeduplicationAccommodationRecordsFormWizard.as_view(
        UNDO_DEDUPLICATION_RECORDS_FORMS,
        url_name="deduplication:accommodations:undo-deduplication-records-manual-step",  # type: ignore[call-arg]
    )
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
    path(
        "deduplicate/<str:step>/",
        select_and_review_accommodation_records_form_wizard,
        name="select-and-review-records-manual-step",
    ),
    path(
        "deduplicate/",
        select_and_review_accommodation_records_form_wizard,
        name="select-and-review-records-manual",
    ),
    path(
        "undo-deduplication/<str:step>/<str:id>/",
        undo_deduplication_accommodations_records_form_wizard,
        name="undo-deduplication-records-manual-step",
    ),
    path(
        "undo-deduplication/<str:step>/complete/",
        undo_deduplication_accommodations_records_form_wizard,
        name="complete-undo-deduplication-records-manual-step",
    ),
]
