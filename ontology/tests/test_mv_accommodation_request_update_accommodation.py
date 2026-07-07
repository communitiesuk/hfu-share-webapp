from django.test import TestCase

from accounts.tests.factories import UserFactory
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
)


class MvAccommodationRequestUpdateAccommodationTest(TestCase):
    def setUp(self):
        self.user = UserFactory(first_name="John", last_name="Doe")

        self.old_accommodation = MvAccommodationFactory(full_address="17 Test Street")
        self.new_accommodation = MvAccommodationFactory(full_address="11 Test Street")

        self.ar = MvAccommodationRequestFactory(
            accommodation_id=[self.old_accommodation.id],
            primary_accommodation=self.old_accommodation,
            number_of_people=1,
        )

    def test_update_accommodation_with_new_accommodation(self):
        self.ar.update_accommodation(self.new_accommodation, self.user)

        self.assertEqual(self.ar.accommodation_id, [self.new_accommodation.pk])
        self.assertEqual(self.ar.primary_accommodation, self.new_accommodation)
        self.assertEqual(self.ar.last_modified_by, "John Doe")

    def test_update_accommodation_with_none(self):
        self.ar.update_accommodation(None, self.user)

        self.assertEqual(self.ar.accommodation_id, [])
        self.assertEqual(self.ar.primary_accommodation, None)
        self.assertEqual(self.ar.last_modified_by, "John Doe")
