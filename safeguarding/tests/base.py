from django.test import TestCase

from ontology.models import CheckType
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvPersonFactory,
)


class SafeguardingBaseTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.person = MvPersonFactory()
        self.accommodation = MvAccommodationFactory()
        self.accommodation_request = self.person.accommodation_request
        self.accommodation_request.primary_accommodation = self.accommodation
        self.accommodation_request.save()

        self.accommodation_suitable_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            AR=[self.accommodation_request],
            person=[self.person],
        )
        self.accommodation_suitable_check.accommodation.set([self.accommodation])
        self.accommodation_exists_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            AR=[self.accommodation_request],
            person=[self.person],
        )
        self.accommodation_exists_check.accommodation.set([self.accommodation])
        self.sponsor_dbs_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
            AR=[self.accommodation_request],
            person=[self.person],
        )
        self.guest_has_arrived_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.GROUP_ARRIVED),
            AR=[self.accommodation_request],
            person=[self.person],
        )
