from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.views import UndoDeduplicationRecordsStep
from ontology.tests.base import MvAccommodationTestCase
from ontology.tests.factories import (
    MvAccommodationFactory,
)
from user_management.tests.base import get_admin_user
from webapp.mixins import SummaryListTestCaseMixin


class UndoDeduplicationSponsorDeduplicatedRecordsRestoredViewTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, MvAccommodationTestCase
):
    def setUp(self):
        super().setUp()

        self.new_principal_accommodation = MvAccommodationFactory(
            full_address="123 Street",
            is_principal=True,
        )

    def test_undo_deduplication_accommodation_records_displays_correct_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        session = self.client.session
        session["wizard_UndoDeduplicationRecordsFormWizard"] = {
            "step": UndoDeduplicationRecordsStep.DEDUPLICATED_RECORDS_RESTORED,
            "step_data": {},
            "step_files": {},
            "extra_data": {
                "deduplication_data": {
                    "principal_name": self.new_principal_accommodation.full_address,
                    "deduplicated_accommodation_data": [
                        {
                            "url": reverse(
                                "accommodations:detail-overview",
                                args=[self.ltla_one_a_accommodation.pk],
                            ),
                            "name": self.ltla_one_a_accommodation.full_address,
                        },
                        {
                            "url": reverse(
                                "accommodations:detail-overview",
                                args=[self.ltla_one_b_accommodation.pk],
                            ),
                            "name": self.ltla_one_b_accommodation.full_address,
                        },
                    ],
                    "formatted_deduplicated_accommodations": f"{self.ltla_one_a_accommodation.full_address}"  # noqa: E501
                    f" and "
                    f"{self.ltla_one_b_accommodation.full_address}",
                }
            },
        }
        session.save()

        response = self.client.get(
            reverse(
                "deduplication:accommodations:complete-undo-deduplication-records-manual-step",
                kwargs={
                    "step": UndoDeduplicationRecordsStep.DEDUPLICATED_RECORDS_RESTORED,
                },
            ),
            {
                "UndoDeduplicationRecordsFormWizard-current_step": (
                    UndoDeduplicationRecordsStep.VIEW_DUPLICATE_RECORDS,
                )
            },
        )

        self.assertContains(response, "Success")

        self.assertContains(response, "You have restored 2 accommodation records")

        self.assertContains(
            response,
            f"{self.ltla_one_a_accommodation.full_address} and "
            f"{self.ltla_one_b_accommodation.full_address} "
            f"have been restored and the principal record "
            f"{self.new_principal_accommodation.full_address} was deleted.",
        )

        self.assertContains(response, "Deduplicated records restored")

        self.assertContains(response, "Review restored records")

        self.assertContains(
            response,
            "Review the restored accommodation records and linked accommodation"
            " requests.",
        )

        self.assertContains(
            response,
            '<a class="govuk-button govuk-button--secondary" '
            'href="/accommodations/">Back to list of accommodation</a>',
            html=True,
        )
