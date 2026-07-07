from django.test import TestCase

from ontology.models import EoiHost, MvAccommodation, MvGroup, MvVolunteer
from ontology.tests.factories import (
    EoiHostFactory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvGroupFactory,
    MvVolunteerFactory,
)


class MvAccommodationRequestForeignKeysTestCase(TestCase):
    def test_get_group_fetches_related_group(self):
        group = MvGroupFactory()
        accommodation_request = MvAccommodationRequestFactory(group=group)

        retrieved_group = accommodation_request.get_group()
        self.assertEqual(group, retrieved_group)

    def test_get_group_handles_related_group_being_none(self):
        accommodation_request = MvAccommodationRequestFactory(group=None)

        retrieved_group = accommodation_request.get_group()
        self.assertEqual(None, retrieved_group)

    def test_get_group_handles_related_group_not_existing(self):
        # Intentionally not using the MvGroupFactory here so that we don't save to
        # the DB. This is testing a scenario we saw in prod where an accommodation
        # request had a FK to a group, but no group with that key could be found
        # in the MvGroup table
        group = MvGroup(id="1234")
        accommodation_request = MvAccommodationRequestFactory(group=group)

        retrieved_group = accommodation_request.get_group()

        self.assertFalse(MvGroup.objects.filter(id=group.id).exists())
        self.assertEqual(None, retrieved_group)

    def test_get_active_host_fetches_related_active_host(self):
        active_host = MvVolunteerFactory()
        accommodation_request = MvAccommodationRequestFactory(active_host=active_host)

        retrieved_active_host = accommodation_request.get_active_host()
        self.assertEqual(active_host, retrieved_active_host)

    def test_get_active_host_handles_related_active_host_being_none(self):
        accommodation_request = MvAccommodationRequestFactory(active_host=None)

        retrieved_active_host = accommodation_request.get_active_host()
        self.assertEqual(None, retrieved_active_host)

    def test_get_active_host_handles_related_active_host_not_existing(self):
        # Intentionally not using the MvVolunteerFactory here so that we don't save to
        # the DB. This is testing a scenario we saw in prod where an accommodation
        # request had a FK to a active_host, but no active_host with that key could
        # be found in the MvVolunteer table
        active_host = MvVolunteer(id="1234")
        accommodation_request = MvAccommodationRequestFactory(active_host=active_host)

        retrieved_active_host = accommodation_request.get_active_host()

        self.assertFalse(MvVolunteer.objects.filter(id=active_host.id).exists())
        self.assertEqual(None, retrieved_active_host)

    def test_get_active_eoi_host_fetches_related_active_eoi_host(self):
        active_eoi_host = EoiHostFactory()
        accommodation_request = MvAccommodationRequestFactory(
            active_eoi_host=active_eoi_host
        )

        retrieved_active_eoi_host = accommodation_request.get_active_eoi_host()
        self.assertEqual(active_eoi_host, retrieved_active_eoi_host)

    def test_get_active_eoi_host_handles_related_active_eoi_host_being_none(self):
        accommodation_request = MvAccommodationRequestFactory(active_eoi_host=None)

        retrieved_active_eoi_host = accommodation_request.get_active_eoi_host()
        self.assertEqual(None, retrieved_active_eoi_host)

    def test_get_active_eoi_host_handles_related_active_eoi_host_not_existing(self):
        # Intentionally not using the EoiHostFactory here so that we don't save to
        # the DB. This is testing a scenario we saw in prod where an accommodation
        # request had a FK to a active_eoi_host, but no active_eoi_host with that key
        # could be found in the EoiHost table
        active_eoi_host = EoiHost(host_id="1234")
        accommodation_request = MvAccommodationRequestFactory(
            active_eoi_host=active_eoi_host
        )

        retrieved_active_eoi_host = accommodation_request.get_active_eoi_host()

        self.assertFalse(
            EoiHost.objects.filter(host_id=active_eoi_host.host_id).exists()
        )
        self.assertEqual(None, retrieved_active_eoi_host)

    def test_get_primary_sponsor_fetches_related_primary_sponsor(self):
        primary_sponsor = MvVolunteerFactory()
        accommodation_request = MvAccommodationRequestFactory(
            primary_sponsor=primary_sponsor
        )

        retrieved_primary_sponsor = accommodation_request.get_primary_sponsor()
        self.assertEqual(primary_sponsor, retrieved_primary_sponsor)

    def test_get_primary_sponsor_handles_related_primary_sponsor_being_none(self):
        accommodation_request = MvAccommodationRequestFactory(primary_sponsor=None)

        retrieved_primary_sponsor = accommodation_request.get_primary_sponsor()
        self.assertEqual(None, retrieved_primary_sponsor)

    def test_get_primary_sponsor_handles_related_primary_sponsor_not_existing(self):
        # Intentionally not using the MvVolunteerFactory here so that we don't save to
        # the DB. This is testing a scenario we saw in prod where an accommodation
        # request had a FK to a primary_sponsor, but no primary_sponsor with that key
        # could be found in the MvVolunteer table
        primary_sponsor = MvVolunteer(id="1234")
        accommodation_request = MvAccommodationRequestFactory(
            primary_sponsor=primary_sponsor
        )

        retrieved_primary_sponsor = accommodation_request.get_primary_sponsor()

        self.assertFalse(MvVolunteer.objects.filter(id=primary_sponsor.id).exists())
        self.assertEqual(None, retrieved_primary_sponsor)

    def test_get_primary_accommodation_fetches_related_primary_accommodation(self):
        primary_accommodation = MvAccommodationFactory()
        accommodation_request = MvAccommodationRequestFactory(
            primary_accommodation=primary_accommodation
        )

        retrieved_primary_accommodation = (
            accommodation_request.get_primary_accommodation()
        )
        self.assertEqual(primary_accommodation, retrieved_primary_accommodation)

    def test_get_primary_accommodation_handles_related_primary_accommodation_being_none(
        self,
    ):
        accommodation_request = MvAccommodationRequestFactory(
            primary_accommodation=None
        )

        retrieved_primary_accommodation = (
            accommodation_request.get_primary_accommodation()
        )
        self.assertEqual(None, retrieved_primary_accommodation)

    def test_get_primary_accommodation_handles_related_primary_accomm_not_existing(
        self,
    ):
        # Intentionally not using the MvAccommodationFactory here so that we don't
        # save to the DB. This is testing a scenario we saw in prod where an AR had a
        # FK to a primary_accommodation, but no primary_accommodation with that key
        # could be found in the MvAccommodation table
        primary_accommodation = MvAccommodation(id="1234")
        accommodation_request = MvAccommodationRequestFactory(
            primary_accommodation=primary_accommodation
        )

        retrieved_primary_accommodation = (
            accommodation_request.get_primary_accommodation()
        )

        self.assertFalse(
            MvAccommodation.objects.filter(id=primary_accommodation.id).exists()
        )
        self.assertEqual(None, retrieved_primary_accommodation)
