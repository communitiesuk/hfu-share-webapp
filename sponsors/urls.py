from django.urls import path

from deduplication.views import (
    SELECT_AND_REVIEW_RECORDS_FORMS,
    UNDO_DEDUPLICATION_RECORDS_FORMS,
    SelectAndReviewSponsorRecordsFormWizard,
    UndoDeduplicationSponsorRecordsFormWizard,
)

from .views import (
    SponsorDetailActionsView,
    SponsorDetailHistoryView,
    SponsorDetailLinkedRecordsView,
    SponsorDetailOverviewView,
    SponsorDetailPropertiesView,
    SponsorEditView,
    SponsorsListView,
)

select_and_review_sponsor_records_form_wizard = (
    SelectAndReviewSponsorRecordsFormWizard.as_view(
        SELECT_AND_REVIEW_RECORDS_FORMS,
        url_name="deduplication:sponsors:select-and-review-records-manual-step",  # type: ignore[call-arg]
    )
)

undo_deduplication_sponsor_records_form_wizard = (
    UndoDeduplicationSponsorRecordsFormWizard.as_view(
        UNDO_DEDUPLICATION_RECORDS_FORMS,
        url_name="deduplication:sponsors:undo-deduplication-records-manual-step",  # type: ignore[call-arg]
    )
)

app_name = "sponsors"
urlpatterns = [
    path(
        "",
        SponsorsListView.as_view(),
        name="sponsors",
    ),
    path(
        "<str:pk>/overview",
        SponsorDetailOverviewView.as_view(),
        name="detail-overview",
    ),
    path(
        "<str:pk>/actions",
        SponsorDetailActionsView.as_view(),
        name="detail-actions",
    ),
    path(
        "<str:pk>/linked-records",
        SponsorDetailLinkedRecordsView.as_view(),
        name="detail-linked-records",
    ),
    path(
        "<str:pk>/properties",
        SponsorDetailPropertiesView.as_view(),
        name="detail-properties",
    ),
    path(
        "<str:pk>/history",
        SponsorDetailHistoryView.as_view(),
        name="detail-history",
    ),
    path(
        "<str:pk>/edit/",
        SponsorEditView.as_view(),
        name="detail-edit",
    ),
    path(
        "deduplicate/<str:step>/",
        select_and_review_sponsor_records_form_wizard,
        name="select-and-review-records-manual-step",
    ),
    path(
        "deduplicate/",
        select_and_review_sponsor_records_form_wizard,
        name="select-and-review-records-manual",
    ),
    path(
        "undo-deduplication/<str:step>/<str:id>/",
        undo_deduplication_sponsor_records_form_wizard,
        name="undo-deduplication-records-manual-step",
    ),
    path(
        "undo-deduplication/<str:step>/complete/",
        undo_deduplication_sponsor_records_form_wizard,
        name="complete-undo-deduplication-records-manual-step",
    ),
]
