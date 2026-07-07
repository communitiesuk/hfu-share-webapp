from django.test import TestCase

from ontology.models import MvUkPostcode, MvVolunteer
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvUkPostcodeFactory,
    MvVolunteerFactory,
)


class MvAccommodationForeignKeysTestCase(TestCase):
    def test_get_postcode_fetches_related_postcode(self):
        postcode = MvUkPostcodeFactory()
        accommodation = MvAccommodationFactory(postcode=postcode)

        retrieved_postcode = accommodation.get_postcode()
        self.assertEqual(postcode, retrieved_postcode)

    def test_get_postcode_handles_related_postcode_being_none(self):
        accommodation = MvAccommodationFactory(postcode=None)

        retrieved_postcode = accommodation.get_postcode()
        self.assertEqual(None, retrieved_postcode)

    def test_get_postcode_handles_related_postcode_not_existing(self):
        # Intentionally not using the MvUkPostcodeFactory here so that we don't save to
        # the DB. This is testing a scenario we saw in prod where an accommodation had
        # a FK to a postcode, but no postcode with that key could be found in the
        # MvUkPostcode table
        postcode = MvUkPostcode(id="1234")
        accommodation = MvAccommodationFactory(postcode=postcode)

        retrieved_postcode = accommodation.get_postcode()

        self.assertFalse(MvUkPostcode.objects.filter(id=postcode.id).exists())
        self.assertEqual(None, retrieved_postcode)

    def test_get_volunteer_fetches_related_volunteer(self):
        volunteer = MvVolunteerFactory()
        accommodation = MvAccommodationFactory(volunteer=volunteer)

        retrieved_volunteer = accommodation.get_volunteer()
        self.assertEqual(volunteer, retrieved_volunteer)

    def test_get_volunteer_handles_related_volunteer_being_none(self):
        accommodation = MvAccommodationFactory(volunteer=None)

        retrieved_volunteer = accommodation.get_volunteer()
        self.assertEqual(None, retrieved_volunteer)

    def test_get_volunteer_handles_related_volunteer_not_existing(self):
        # Intentionally not using the MvVolunteerFactory here so that we don't save to
        # the DB. This is testing a scenario we saw in prod where an accommodation had
        # a FK to a volunteer, but no volunteer with that key could be found in the
        # MvVolunteer table
        volunteer = MvVolunteer(id="1234")
        accommodation = MvAccommodationFactory(volunteer=volunteer)

        retrieved_volunteer = accommodation.get_volunteer()

        self.assertFalse(MvVolunteer.objects.filter(id=volunteer.id).exists())
        self.assertEqual(None, retrieved_volunteer)
