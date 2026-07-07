from django.test import TestCase

from ontology.models import CheckType, DevCheckV2, MvAccommodationRequest
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvGroupFactory,
    MvVolunteerFactory,
)


class MvAccommodationRequestWithChecksTest(TestCase):
    """Test the with_checks method from MvAccommodationQueryset."""

    def setUp(self):
        self.accommodation = MvAccommodationFactory()
        self.group = MvGroupFactory()
        self.sponsor = MvVolunteerFactory()
        self.host = MvVolunteerFactory()
        self.accommodation_request = MvAccommodationRequestFactory(
            accommodation_id=[self.accommodation.id],
            primary_accommodation=self.accommodation,
            group=self.group,
            sponsor_id=[self.sponsor.id],
            primary_sponsor=self.sponsor,
            active_host=self.host,
        )

    def test_with_checks_returns_queryset_with_check_ids_annotation(self):
        accommodation_request = (
            MvAccommodationRequest.objects.filter(
                id=self.accommodation_request.id,
            )
            .with_checks()
            .first()
        )

        self.assertTrue(hasattr(accommodation_request, "check_ids"))
        self.assertEqual(accommodation_request.check_ids, [])

    def test_with_checks_returns_accommodation_exists_check_ids(self):
        accommodation_exists_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
        )
        accommodation_exists_check.accommodation.set([self.accommodation])

        accommodation_request = (
            MvAccommodationRequest.objects.filter(
                id=self.accommodation_request.id,
            )
            .with_checks()
            .first()
        )

        self.assertEqual(len(accommodation_request.check_ids), 1)
        self.assertIn(
            str(accommodation_exists_check.id), accommodation_request.check_ids
        )

    def test_with_checks_returns_accommodation_suitable_check_ids(self):
        accommodation_suitable_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            AR=[self.accommodation_request],
        )
        accommodation_suitable_check.accommodation.set([self.accommodation])

        accommodation_request = (
            MvAccommodationRequest.objects.filter(
                id=self.accommodation_request.id,
            )
            .with_checks()
            .first()
        )

        self.assertEqual(len(accommodation_request.check_ids), 1)
        self.assertIn(
            str(accommodation_suitable_check.id), accommodation_request.check_ids
        )

    def test_with_checks_excludes_accommodation_suitable_check_for_different_ar(
        self,
    ):
        other_ar = MvAccommodationRequestFactory()
        accommodation_suitable_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            AR=[other_ar],  # Different AR
        )
        accommodation_suitable_check.accommodation.set([self.accommodation])

        accommodation_request = (
            MvAccommodationRequest.objects.filter(
                id=self.accommodation_request.id,
            )
            .with_checks()
            .first()
        )

        self.assertEqual(accommodation_request.check_ids, [])

    def test_with_checks_returns_sponsor_check_ids(self):
        sponsor_dbs_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
        )
        sponsor_dbs_check.sponsor.set([self.sponsor])

        accommodation_request = (
            MvAccommodationRequest.objects.filter(
                id=self.accommodation_request.id,
            )
            .with_checks()
            .first()
        )

        self.assertEqual(len(accommodation_request.check_ids), 1)
        self.assertIn(str(sponsor_dbs_check.id), accommodation_request.check_ids)

    def test_with_checks_excludes_withdrawn_sponsor_checks(self):
        withdrawn_sponsor = MvVolunteerFactory()
        ar_with_withdrawn = MvAccommodationRequestFactory(
            sponsor_id=[withdrawn_sponsor.id],
            sponsor_withdrawn=[withdrawn_sponsor.id],  # Sponsor is withdrawn
        )

        sponsor_dbs_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
        )
        sponsor_dbs_check.sponsor.set([withdrawn_sponsor])

        accommodation_request = (
            MvAccommodationRequest.objects.filter(
                id=ar_with_withdrawn.id,
            )
            .with_checks()
            .first()
        )

        self.assertEqual(accommodation_request.check_ids, [])

    def test_with_checks_returns_primary_sponsor_check_ids(self):
        primary_sponsor_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
        )
        primary_sponsor_check.sponsor.set([self.sponsor])

        accommodation_request = (
            MvAccommodationRequest.objects.filter(
                id=self.accommodation_request.id,
            )
            .with_checks()
            .first()
        )

        self.assertEqual(len(accommodation_request.check_ids), 1)
        self.assertIn(str(primary_sponsor_check.id), accommodation_request.check_ids)

    def test_with_checks_returns_host_check_ids(self):
        host_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS),
        )
        host_check.sponsor.set([self.host])

        accommodation_request = (
            MvAccommodationRequest.objects.filter(
                id=self.accommodation_request.id,
            )
            .with_checks()
            .first()
        )

        self.assertEqual(len(accommodation_request.check_ids), 1)
        self.assertIn(str(host_check.id), accommodation_request.check_ids)

    def test_with_checks_returns_group_check_ids(self):
        group_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.GROUP_ARRIVED),
        )
        group_check.group.set([self.group])

        accommodation_request = (
            MvAccommodationRequest.objects.filter(
                id=self.accommodation_request.id,
            )
            .with_checks()
            .first()
        )

        self.assertEqual(len(accommodation_request.check_ids), 1)
        self.assertIn(str(group_check.id), accommodation_request.check_ids)

    def test_with_checks_returns_group_arrived_check_specific_to_ar(self):
        group_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.GROUP_ARRIVED),
            AR=[self.accommodation_request],
        )

        accommodation_request = (
            MvAccommodationRequest.objects.filter(
                id=self.accommodation_request.id,
            )
            .with_checks()
            .first()
        )

        self.assertEqual(len(accommodation_request.check_ids), 1)
        self.assertIn(str(group_check.id), accommodation_request.check_ids)

    def test_with_checks_returns_bridging_accommodation_check_ids(self):
        bridging_accommodation = MvAccommodationFactory()
        ar_with_bridging = MvAccommodationRequestFactory(
            bridging_accommodation_id=bridging_accommodation.id,
        )

        bridging_exists_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
        )
        bridging_exists_check.accommodation.set([bridging_accommodation])

        bridging_suitable_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            AR=[ar_with_bridging],
        )
        bridging_suitable_check.accommodation.set([bridging_accommodation])

        accommodation_request = MvAccommodationRequest.objects.with_checks().get(
            id=ar_with_bridging.id
        )

        self.assertEqual(len(accommodation_request.check_ids), 2)
        self.assertIn(str(bridging_exists_check.id), accommodation_request.check_ids)
        self.assertIn(str(bridging_suitable_check.id), accommodation_request.check_ids)

    def test_with_checks_returns_temporary_accommodation_check_ids(self):
        temporary_accommodation = MvAccommodationFactory()
        ar_with_temporary = MvAccommodationRequestFactory(
            temporary_accommodation_id=temporary_accommodation.id,
        )

        temporary_exists_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
        )
        temporary_exists_check.accommodation.set([temporary_accommodation])

        accommodation_request = MvAccommodationRequest.objects.with_checks().get(
            id=ar_with_temporary.id
        )

        self.assertEqual(len(accommodation_request.check_ids), 1)
        self.assertIn(str(temporary_exists_check.id), accommodation_request.check_ids)

    def test_with_checks_handles_multiple_accommodation_ids(self):
        accommodation2 = MvAccommodationFactory()
        ar_with_multiple = MvAccommodationRequestFactory(
            accommodation_id=[self.accommodation.id, accommodation2.id],
        )

        check1 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
        )
        check1.accommodation.set([self.accommodation])

        check2 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
        )
        check2.accommodation.set([accommodation2])

        accommodation_request = MvAccommodationRequest.objects.with_checks().get(
            id=ar_with_multiple.id
        )

        self.assertEqual(len(accommodation_request.check_ids), 2)
        self.assertIn(str(check1.id), accommodation_request.check_ids)
        self.assertIn(str(check2.id), accommodation_request.check_ids)

    def test_with_checks_query_efficiency(self):
        ars = []
        for _ in range(5):
            accommodation = MvAccommodationFactory()
            ar = MvAccommodationRequestFactory(
                accommodation_id=[accommodation.id],
                primary_accommodation=accommodation,
            )
            ars.append(ar)

            # Create a check for each
            check = DevCheckV2Factory(
                check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            )
            check.accommodation.set([accommodation])

        with self.assertNumQueries(1):
            list(MvAccommodationRequest.objects.with_checks().all())

    def test_with_checks_returns_queryset_with_check_subtypes_annotation(self):
        accommodation_request = (
            MvAccommodationRequest.objects.filter(
                id=self.accommodation_request.id,
            )
            .with_checks()
            .first()
        )

        self.assertTrue(hasattr(accommodation_request, "check_subtypes"))
        self.assertEqual(accommodation_request.check_ids, [])

    def test_with_checks_returns_accommodation_exists_check_subtypes(self):
        accommodation_exists_check = DevCheckV2Factory(
            check_status=DevCheckV2.CheckStatus.FAILED,
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            check_subtype=(DevCheckV2.AccommExistsFailureReason.DOES_NOT_EXIST),
        )
        accommodation_exists_check.accommodation.set([self.accommodation])

        accommodation_request = (
            MvAccommodationRequest.objects.filter(
                id=self.accommodation_request.id,
            )
            .with_checks()
            .first()
        )

        self.assertEqual(len(accommodation_request.check_subtypes), 1)
        self.assertIn(
            str(accommodation_exists_check.check_subtype),
            accommodation_request.check_subtypes,
        )
