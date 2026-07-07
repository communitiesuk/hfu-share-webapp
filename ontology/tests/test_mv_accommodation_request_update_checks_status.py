from django.test import TestCase

from accounts.tests.factories import UserFactory
from ontology.models import MvAccommodationRequest
from ontology.tests.factories import MvAccommodationRequestFactory


class MvAccommodationRequestUpdateChecksStatusTest(TestCase):
    def setUp(self):
        self.user = UserFactory(first_name="John", last_name="Doe")

    def test_update_checks_status_updates_all_relevant_fields(self):
        # Using .build() to prevent save() running and setting edited_in_app True
        accommodation_request = MvAccommodationRequestFactory.build(
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            last_modified_by="Previous Author",
            last_modified_at=None,
            edited_in_app=False,
        )

        new_status = MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED
        accommodation_request.update_checks_status(new_status, self.user)

        self.assertEqual(accommodation_request.checks_status, new_status)
        self.assertTrue(accommodation_request.edited_in_app)
        self.assertEqual(
            accommodation_request.last_modified_by, self.user.get_full_name()
        )
        self.assertNotEqual(accommodation_request.last_modified_at, None)

    def test_update_checks_status_skips_if_given_preexisting_status(self):
        status = MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED

        # Using .build() to prevent save() running and setting edited_in_app True
        accommodation_request = MvAccommodationRequestFactory.build(
            checks_status=status,
            last_modified_by="Previous Author",
            last_modified_at=None,
            edited_in_app=False,
        )

        accommodation_request.update_checks_status(status, self.user)

        self.assertEqual(accommodation_request.checks_status, status)
        self.assertFalse(accommodation_request.edited_in_app)
        self.assertNotEqual(
            accommodation_request.last_modified_by, self.user.get_full_name()
        )
        self.assertEqual(accommodation_request.last_modified_by, "Previous Author")
        self.assertEqual(accommodation_request.last_modified_at, None)
