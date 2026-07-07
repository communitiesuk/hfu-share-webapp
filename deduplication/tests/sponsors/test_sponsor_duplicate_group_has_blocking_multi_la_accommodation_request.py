from django.test import TestCase

from deduplication.tests.factories import (
    SponsorDuplicateGroupFactory,
)
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvVolunteerFactory,
)


class SponsorDuplicateGroupHasBlockingMultiLaAccommodationRequestTestCase(TestCase):
    def setUp(self):
        self.first_sponsor = MvVolunteerFactory(is_principal=True)
        self.second_sponsor = MvVolunteerFactory(is_principal=True)

        self.ar = MvAccommodationRequestFactory(
            ltla_name=["Barking and Dagenham"],
        )
        self.principal_sponsor = MvVolunteerFactory(
            is_principal=True,
        )
        self.ar.primary_sponsor = self.principal_sponsor
        self.ar.save()

        self.dup_group = SponsorDuplicateGroupFactory.create(
            principal_record=self.principal_sponsor,
        )
        self.dup_group.sponsors.set([self.first_sponsor, self.second_sponsor])
        self.dup_group.save()

    def test_should_not_block_when_accommodation_request_is_single_la(self):
        self.assertFalse(
            self.dup_group.has_blocking_multi_la_accommodation_request(
                self.principal_sponsor
            )
        )

    def test_should_block_when_accommodation_request_becomes_multi_la(self):
        self.ar.ltla_name = ["Barking and Dagenham", "Camden"]
        self.ar.save()

        self.assertTrue(
            self.dup_group.has_blocking_multi_la_accommodation_request(
                self.principal_sponsor
            )
        )

    def test_can_undo_returns_true_when_accommodation_request_is_single_la(self):
        self.assertTrue(self.dup_group.can_undo_deduplication(self.principal_sponsor))

    def test_can_undo_returns_false_when_accommodation_request_becomes_multi_la(self):
        self.ar.ltla_name = ["Barking and Dagenham", "Camden"]
        self.ar.save()

        self.assertFalse(self.dup_group.can_undo_deduplication(self.principal_sponsor))
