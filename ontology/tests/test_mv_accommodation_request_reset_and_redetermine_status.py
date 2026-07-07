from django.test import TestCase

from ontology.models import (
    MvAccommodationRequest,
)
from ontology.tests.factories import MvAccommodationRequestFactory
from user_management.tests.base import get_admin_user


class MvAccommodationRequestResetAndRedetermineStatus(TestCase):
    def test_reset_and_redetermine_status_changes_status_for_closed_ar(self):
        user = get_admin_user()

        accommodation_request = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
        )

        accommodation_request.reset_and_redetermine_status(author=user.username)

        self.assertEqual(
            accommodation_request.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )
