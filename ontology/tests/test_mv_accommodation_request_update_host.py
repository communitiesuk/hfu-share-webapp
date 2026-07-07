from django.test import TestCase

from accounts.tests.factories import UserFactory
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvVolunteerFactory,
)


class MvAccommodationRequestUpdateHostTest(TestCase):
    def setUp(self):
        self.user = UserFactory(first_name="John", last_name="Doe")

    def test_update_host_with_volunteer_id(self):
        volunteer = MvVolunteerFactory(
            id="volunteer123",
            is_sponsor=True,
        )
        accommodation = MvAccommodationFactory(
            volunteer=volunteer,
        )
        accommodation_request = MvAccommodationRequestFactory(
            active_host=None,
            active_eoi_host=None,
            primary_sponsor=None,
            sponsor_id=None,
        )

        accommodation_request.update_host(accommodation, self.user)

        self.assertEqual(accommodation_request.active_host.id, volunteer.id)
        self.assertEqual(accommodation_request.active_eoi_host, None)
        self.assertEqual(accommodation_request.primary_sponsor.id, volunteer.id)
        self.assertEqual(accommodation_request.sponsor_id, [volunteer.id])
        self.assertEqual(accommodation_request.last_modified_by, "John Doe")
        self.assertIsNotNone(accommodation_request.last_modified_at)

    def test_update_host_with_existing_sponsor_ids(self):
        existing_volunteer = MvVolunteerFactory()
        new_volunteer = MvVolunteerFactory(is_sponsor=True)
        accommodation = MvAccommodationFactory(volunteer=new_volunteer)
        accommodation_request = MvAccommodationRequestFactory(
            sponsor_id=[existing_volunteer.id],
            primary_sponsor=existing_volunteer,
        )

        accommodation_request.update_host(accommodation, self.user)

        self.assertEqual(accommodation_request.active_host, new_volunteer)
        self.assertEqual(accommodation_request.primary_sponsor, new_volunteer)
        self.assertEqual(
            accommodation_request.sponsor_id, [existing_volunteer.id, new_volunteer.id]
        )

    def test_update_host_with_accommodation_no_volunteer_id_with_host(self):
        principal_host = MvVolunteerFactory(is_principal=True)
        accommodation = MvAccommodationFactory(
            volunteer=None,
        )
        accommodation.hosts.add(principal_host)
        accommodation_request = MvAccommodationRequestFactory()

        accommodation_request.update_host(accommodation, self.user)

        self.assertEqual(accommodation_request.active_host.id, principal_host.id)
        self.assertEqual(accommodation_request.primary_sponsor, principal_host)

    def test_update_host_with_accommodation_no_volunteer_no_principal_host(self):
        current_volunteer = MvVolunteerFactory(is_sponsor=True)
        accommodation = MvAccommodationFactory(
            volunteer=None,
        )
        accommodation_request = MvAccommodationRequestFactory(
            primary_sponsor=current_volunteer,
            sponsor_id=[current_volunteer.id],
        )

        accommodation_request.update_host(accommodation, self.user)

        # Should not change anything if no host is available
        self.assertIsNone(accommodation_request.active_host)
        self.assertEqual(accommodation_request.primary_sponsor, current_volunteer)
        self.assertEqual(accommodation_request.sponsor_id, [current_volunteer.id])

    def test_it_wont_add_volunteer_if_is_sponsor_false(self):
        volunteer = MvVolunteerFactory(
            id="volunteer123",
            is_sponsor=False,
        )
        accommodation = MvAccommodationFactory(
            volunteer=volunteer,
        )
        accommodation_request = MvAccommodationRequestFactory(
            active_host=None,
            active_eoi_host=None,
            primary_sponsor=None,
            sponsor_id=None,
        )

        accommodation_request.update_host(accommodation, self.user)

        self.assertEqual(accommodation_request.primary_sponsor_id, volunteer.id)
        self.assertIsNone(accommodation_request.sponsor_id)
