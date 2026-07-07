from django.urls import path

from deduplication.views import (
    SELECT_AND_REVIEW_RECORDS_FORMS,
    UNDO_DEDUPLICATION_RECORDS_FORMS,
    SelectAndReviewGuestRecordsFormWizard,
    UndoDeduplicationGuestRecordsFormWizard,
)

from .views import (
    GuestDetailActionsView,
    GuestDetailHistoryView,
    GuestDetailLinkedRecordsView,
    GuestDetailOverviewView,
    GuestDetailPropertiesView,
    GuestEditView,
    GuestsListView,
    GuestVisaApplicationsListView,
)

select_and_review_guest_records_form_wizard = (
    SelectAndReviewGuestRecordsFormWizard.as_view(
        SELECT_AND_REVIEW_RECORDS_FORMS,
        url_name="deduplication:guests:select-and-review-records-manual-step",  # type: ignore[call-arg]
    )
)

undo_deduplication_guest_records_form_wizard = (
    UndoDeduplicationGuestRecordsFormWizard.as_view(
        UNDO_DEDUPLICATION_RECORDS_FORMS,
        url_name="deduplication:guests:undo-deduplication-records-manual-step",  # type: ignore[call-arg]
    )
)

app_name = "guests"
urlpatterns = [
    path(
        "",
        GuestsListView.as_view(),
        name="guests",
    ),
    path(
        "<str:pk>/overview",
        GuestDetailOverviewView.as_view(),
        name="detail-overview",
    ),
    path(
        "<str:pk>/actions",
        GuestDetailActionsView.as_view(),
        name="detail-actions",
    ),
    path(
        "<str:pk>/linked-records",
        GuestDetailLinkedRecordsView.as_view(),
        name="detail-linked-records",
    ),
    path(
        "<str:pk>/linked-records/visa-applications",
        GuestVisaApplicationsListView.as_view(),
        name="detail-linked-records-visa-applications",
    ),
    path(
        "<str:pk>/properties",
        GuestDetailPropertiesView.as_view(),
        name="detail-properties",
    ),
    path(
        "<str:pk>/history",
        GuestDetailHistoryView.as_view(),
        name="detail-history",
    ),
    path(
        "<str:pk>/edit/",
        GuestEditView.as_view(),
        name="detail-edit",
    ),
    path(
        "deduplicate/<str:step>/",
        select_and_review_guest_records_form_wizard,
        name="select-and-review-records-manual-step",
    ),
    path(
        "deduplicate/",
        select_and_review_guest_records_form_wizard,
        name="select-and-review-records-manual",
    ),
    path(
        "undo-deduplication/<str:step>/<str:id>/",
        undo_deduplication_guest_records_form_wizard,
        name="undo-deduplication-records-manual-step",
    ),
    path(
        "undo-deduplication/<str:step>/complete/",
        undo_deduplication_guest_records_form_wizard,
        name="complete-undo-deduplication-records-manual-step",
    ),
]
