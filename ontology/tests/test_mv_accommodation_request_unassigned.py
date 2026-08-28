from ontology.models import MvAccommodationRequest
from ontology.tests.factories import (
    HiddenUnassignedAccommodationRequestFactory as HiddenUnassignedAccReqFactory,
)
from ontology.tests.factories import MvAccommodationRequestFactory as AccReqFactory
from ontology.tests.factories import MvVolunteerFactory
from test_utils.base import BaseTestCase


class MvAccommodationRequestUnassignedTest(BaseTestCase):
    def titles(self, queryset):
        return sorted(queryset.values_list("title", flat=True))

    def test_unassigned_includes_requests_with_no_local_authority(self):
        AccReqFactory(title="No local authority")

        self.assertEqual(
            self.titles(MvAccommodationRequest.objects.unassigned()),
            ["No local authority"],
        )

    def test_unassigned_includes_requests_with_empty_local_authority_arrays(self):
        AccReqFactory(title="Empty arrays", ltla_name=[], utla_name=[])

        self.assertEqual(
            self.titles(MvAccommodationRequest.objects.unassigned()),
            ["Empty arrays"],
        )

    def test_unassigned_excludes_requests_with_a_lower_tier_local_authority(self):
        AccReqFactory(title="Has lower tier", ltla_name=["some_ltla"])

        self.assertEqual(MvAccommodationRequest.objects.unassigned().count(), 0)

    def test_unassigned_excludes_requests_with_an_upper_tier_local_authority(self):
        AccReqFactory(title="Has upper tier", utla_name=["some_utla"])

        self.assertEqual(MvAccommodationRequest.objects.unassigned().count(), 0)

    def test_unassigned_excludes_super_sponsor_requests(self):
        sponsor = MvVolunteerFactory(first_name="Scottish Government")
        sponsor.save()
        sponsor.refresh_from_db()
        AccReqFactory(title="Super sponsored", sponsor_id=[sponsor.id])

        self.assertEqual(MvAccommodationRequest.objects.unassigned().count(), 0)

    def test_unassigned_excludes_super_sponsor_requests_by_primary_sponsor(self):
        sponsor = MvVolunteerFactory(first_name="the WALES Government")
        sponsor.save()
        sponsor.refresh_from_db()
        AccReqFactory(title="Super sponsored", primary_sponsor_id=sponsor.id)

        self.assertEqual(MvAccommodationRequest.objects.unassigned().count(), 0)

    def test_unassigned_includes_requests_sponsored_by_an_individual(self):
        sponsor = MvVolunteerFactory(first_name="Scottish", last_name="Person")
        sponsor.save()
        sponsor.refresh_from_db()
        AccReqFactory(title="Individually sponsored", sponsor_id=[sponsor.id])

        self.assertEqual(
            self.titles(MvAccommodationRequest.objects.unassigned()),
            ["Individually sponsored"],
        )

    def test_not_hidden_excludes_hidden_requests(self):
        AccReqFactory(title="Visible")
        hidden = AccReqFactory(title="Hidden")
        HiddenUnassignedAccReqFactory(accommodation_request=hidden)

        self.assertEqual(
            self.titles(MvAccommodationRequest.objects.not_hidden()),
            ["Visible"],
        )

    def test_unassigned_and_not_hidden_compose(self):
        AccReqFactory(title="Visible and unassigned")
        AccReqFactory(title="Assigned", ltla_name=["some_ltla"])
        hidden = AccReqFactory(title="Hidden and unassigned")
        HiddenUnassignedAccReqFactory(accommodation_request=hidden)

        self.assertEqual(
            self.titles(MvAccommodationRequest.objects.unassigned().not_hidden()),
            ["Visible and unassigned"],
        )
