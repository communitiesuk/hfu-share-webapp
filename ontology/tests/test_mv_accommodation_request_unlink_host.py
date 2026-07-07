from django.test import TestCase

from accounts.tests.factories import UserFactory
from ontology.tests.factories import (
    EoiHostFactory,
    MvAccommodationRequestFactory,
    MvVolunteerFactory,
)


class MvAccommodationRequestUnlinkHostTest(TestCase):
    def setUp(self):
        self.user = UserFactory(first_name="John", last_name="Doe")

    def test_unlink_host_with_host_and_eoi_host(self):
        eoi_host = EoiHostFactory()
        active_host = MvVolunteerFactory()
        accommodation_request = MvAccommodationRequestFactory(
            is_eoi_host=True,
            active_eoi_host=eoi_host,
            active_host=active_host,
        )

        self.assertEqual(accommodation_request.previous_eoi_hosts.count(), 0)

        accommodation_request.unlink_host(self.user)

        self.assertIsNone(accommodation_request.active_eoi_host)
        self.assertIsNone(accommodation_request.is_eoi_host)
        self.assertEqual(accommodation_request.previous_eoi_hosts.count(), 1)
        self.assertEqual(accommodation_request.last_modified_by, "John Doe")
        self.assertIsNotNone(accommodation_request.last_modified_at)
