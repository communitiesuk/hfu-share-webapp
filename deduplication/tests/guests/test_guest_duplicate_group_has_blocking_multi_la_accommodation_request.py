from django.test import TestCase

from deduplication.tests.factories import GuestDuplicateGroupFactory
from ontology.tests.factories import MvAccommodationRequestFactory, MvPersonFactory


class GuestDuplicateGroupHasBlockingMultiLaAccommodationRequestTestCase(TestCase):
    def setUp(self):
        self.first_guest = MvPersonFactory(is_principal=True)
        self.second_guest = MvPersonFactory(is_principal=True)

        self.ar = MvAccommodationRequestFactory(
            ltla_name=["Barking and Dagenham"],
        )
        self.principal_guest = MvPersonFactory(
            is_principal=True,
            accommodation_request=self.ar,
        )

        self.dup_group = GuestDuplicateGroupFactory.create(
            principal_record=self.principal_guest,
        )
        self.dup_group.guests.set([self.first_guest, self.second_guest])
        self.dup_group.save()

    def test_should_not_block_when_accommodation_request_is_single_la(self):
        self.assertFalse(
            self.dup_group.has_blocking_multi_la_accommodation_request(
                self.principal_guest.pk
            )
        )

    def test_should_block_when_accommodation_request_becomes_multi_la(self):
        self.ar.ltla_name = ["Barking and Dagenham", "Camden"]
        self.ar.save()

        self.assertTrue(
            self.dup_group.has_blocking_multi_la_accommodation_request(
                self.principal_guest.pk
            )
        )

    def test_can_undo_returns_true_when_accommodation_request_is_single_la(self):
        self.assertTrue(self.dup_group.can_undo_deduplication(self.principal_guest.pk))

    def test_can_undo_returns_false_when_accommodation_request_becomes_multi_la(self):
        self.ar.ltla_name = ["Barking and Dagenham", "Camden"]
        self.ar.save()

        self.assertFalse(self.dup_group.can_undo_deduplication(self.principal_guest.pk))
