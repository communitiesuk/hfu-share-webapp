from django.urls import include, path

from deduplication.views import (
    SELECT_AND_REVIEW_RECORDS_FORMS,
    UNDO_DEDUPLICATION_RECORDS_FORMS,
    SelectAndReviewAccommodationRecordsFormWizard,
    SelectAndReviewGuestRecordsFormWizard,
    SelectAndReviewSponsorRecordsFormWizard,
    SelectRecordTypeView,
    UndoDeduplicationAccommodationRecordsFormWizard,
    UndoDeduplicationGuestRecordsFormWizard,
    UndoDeduplicationSponsorRecordsFormWizard,
)

app_name = "deduplication"

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

select_and_review_accommodation_records_form_wizard = (
    SelectAndReviewAccommodationRecordsFormWizard.as_view(
        SELECT_AND_REVIEW_RECORDS_FORMS,
        url_name="deduplication:accommodations:select-and-review-records-manual-step",  # type: ignore[call-arg]
    )
)

undo_deduplication_accommodation_records_form_wizard = (
    UndoDeduplicationAccommodationRecordsFormWizard.as_view(
        UNDO_DEDUPLICATION_RECORDS_FORMS,
        url_name="deduplication:accommodations:undo-deduplication-records-manual-step",  # type: ignore[call-arg]
    )
)


def manual_deduplication_patterns(select_records_wizard, undo_deduplication_wizard):
    return [
        path(
            "<str:step>/",
            select_records_wizard,
            name="select-and-review-records-manual-step",
        ),
        path(
            "",
            select_records_wizard,
            name="select-and-review-records-manual",
        ),
        path(
            "<str:step>/<str:id>/",
            undo_deduplication_wizard,
            name="undo-deduplication-records-manual-step",
        ),
        path(
            "<str:step>/complete/",
            undo_deduplication_wizard,
            name="complete-undo-deduplication-records-manual-step",
        ),
    ]


urlpatterns = [
    path(
        "",
        SelectRecordTypeView.as_view(),
        name="select-record-type",
    ),
    path(
        "sponsors/",
        include(
            (
                manual_deduplication_patterns(
                    select_and_review_sponsor_records_form_wizard,
                    undo_deduplication_sponsor_records_form_wizard,
                ),
                "sponsors",
            )
        ),
    ),
    path(
        "guests/",
        include(
            (
                manual_deduplication_patterns(
                    select_and_review_guest_records_form_wizard,
                    undo_deduplication_guest_records_form_wizard,
                ),
                "guests",
            )
        ),
    ),
    path(
        "accommodations/",
        include(
            (
                manual_deduplication_patterns(
                    select_and_review_accommodation_records_form_wizard,
                    undo_deduplication_accommodation_records_form_wizard,
                ),
                "accommodations",
            )
        ),
    ),
]
