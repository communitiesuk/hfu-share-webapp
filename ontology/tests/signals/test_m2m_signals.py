from django.test import TestCase

from accounts.tests.factories import UserFactory
from ontology.models import (
    CheckType,
    DevCheckV2,
    MvAccommodation,
    MvAccommodationRequest,
)
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvVolunteerFactory,
)


class DevCheckV2M2MSignalTests(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_ar_checks_status_updates_on_sponsor_m2m_change(self):
        sponsor = MvVolunteerFactory()
        ar = MvAccommodationRequestFactory(sponsor_id=[sponsor.id])
        check_type = CheckType.objects.filter(id=CheckType.Id.SPONSOR_DBS).first()
        devcheck = DevCheckV2Factory(
            create_by=self.user.id,
            check_type=check_type,
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        devcheck.sponsor.add(sponsor)
        devcheck.save()

        ar.refresh_from_db()
        self.assertEqual(devcheck.check_type, check_type)
        self.assertEqual(devcheck.check_status, DevCheckV2.CheckStatus.FAILED)
        self.assertEqual(
            ar.checks_status,
            ar.ChecksStatus.SOME_CHECKS_FAILED,
        )
        self.assertTrue(ar.edited_in_app)

    def test_ar_checks_status_updates_on_accommodation_exists_m2m_change(self):
        accommodation = MvAccommodationFactory()
        ar = MvAccommodationRequestFactory(primary_accommodation=accommodation)
        check_type = CheckType.objects.filter(id=CheckType.Id.ACCOMM_EXISTS).first()
        devcheck = DevCheckV2Factory(
            create_by=self.user.id,
            check_type=check_type,
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        devcheck.accommodation.add(accommodation)
        devcheck.save()

        ar.refresh_from_db()
        self.assertEqual(devcheck.check_type, check_type)
        self.assertEqual(devcheck.check_status, DevCheckV2.CheckStatus.FAILED)
        self.assertEqual(
            ar.checks_status,
            ar.ChecksStatus.SOME_CHECKS_FAILED,
        )
        self.assertTrue(ar.edited_in_app)

    def test_ar_checks_status_updates_on_temporary_accommodation_exists_m2m_change(
        self,
    ):
        temp_accom_type = MvAccommodation.AccommodationType.TEMPORARY_ACCOMMODATION
        accommodation = MvAccommodationFactory(accommodation_type=temp_accom_type)
        ar = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            primary_accommodation_id=accommodation.id,
        )
        check_type = CheckType.objects.filter(id=CheckType.Id.ACCOMM_EXISTS).first()
        devcheck = DevCheckV2Factory(
            create_by=self.user.id,
            check_type=check_type,
            check_status=DevCheckV2.CheckStatus.PASSED,
        )
        devcheck.accommodation.add(accommodation)
        devcheck.save()

        ar.refresh_from_db()
        self.assertEqual(devcheck.check_type, check_type)
        self.assertEqual(devcheck.check_status, DevCheckV2.CheckStatus.PASSED)
        self.assertEqual(
            ar.checks_status,
            MvAccommodationRequest.ChecksStatus.IN_TEMPORARY_ACCOMMODATION,
        )
        self.assertTrue(ar.edited_in_app)

    def test_ar_checks_status_not_updated_on_previous_accommodations_exists_m2m_change(
        self,
    ):
        accommodation = MvAccommodationFactory()
        ar = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            previous_accommodation_id=[accommodation.id],
        )

        check_type = CheckType.objects.filter(id=CheckType.Id.ACCOMM_EXISTS).first()
        devcheck = DevCheckV2Factory(
            create_by=self.user.id,
            check_type=check_type,
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        devcheck.accommodation.add(accommodation)
        devcheck.save()

        ar.refresh_from_db()
        self.assertEqual(devcheck.check_type, check_type)
        self.assertEqual(devcheck.check_status, DevCheckV2.CheckStatus.FAILED)
        self.assertEqual(
            ar.checks_status,
            MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )
        self.assertTrue(ar.edited_in_app)

    def test_accommodation_exists_m2m_updates_all_ars_linked_to_the_accom(self):
        accommodation = MvAccommodationFactory()
        related_ars = [
            MvAccommodationRequestFactory(
                primary_accommodation=accommodation,
                checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            ),
            MvAccommodationRequestFactory(
                primary_accommodation=accommodation,
                checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            ),
        ]

        check_type = CheckType.objects.filter(id=CheckType.Id.ACCOMM_EXISTS).first()
        devcheck = DevCheckV2Factory(
            create_by=self.user.id,
            check_type=check_type,
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        devcheck.accommodation.add(accommodation)
        devcheck.save()

        self.assertEqual(devcheck.check_type, check_type)
        self.assertEqual(devcheck.check_status, DevCheckV2.CheckStatus.FAILED)
        for ar in related_ars:
            ar.refresh_from_db()
            self.assertEqual(
                ar.checks_status,
                ar.ChecksStatus.SOME_CHECKS_FAILED,
            )
            self.assertTrue(ar.edited_in_app)

    def test_accommodation_suitable_m2m_only_affects_linked_ar(self):
        accommodation = MvAccommodationFactory()
        ar1 = MvAccommodationRequestFactory(
            primary_accommodation=accommodation,
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )
        ar2 = MvAccommodationRequestFactory(
            primary_accommodation=accommodation,
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

        check_type = CheckType.objects.filter(id=CheckType.Id.ACCOMM_SUITABLE).first()
        devcheck = DevCheckV2Factory(
            create_by=self.user.id,
            check_type=check_type,
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        devcheck.AR.add(ar1)
        devcheck.accommodation.add(accommodation)
        devcheck.save()

        ar1.refresh_from_db()
        self.assertEqual(ar1.checks_status, ar1.ChecksStatus.SOME_CHECKS_FAILED)

        ar2.refresh_from_db()
        self.assertEqual(ar2.checks_status, ar2.ChecksStatus.CHECKS_REQUIRED)

    def test_updating_accommodation_m2m_affects_all_linked_ar_from_either_accom(self):
        accom1 = MvAccommodationFactory()
        accom2 = MvAccommodationFactory()
        ar1 = MvAccommodationRequestFactory(
            accommodation_id=[accom1.id, accom2.id],
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )
        ar2 = MvAccommodationRequestFactory(
            accommodation_id=[accom1.id],
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

        check_type = CheckType.objects.filter(id=CheckType.Id.ACCOMM_EXISTS).first()
        devcheck = DevCheckV2Factory(
            create_by=self.user.id,
            check_type=check_type,
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        devcheck.accommodation.add(accom1)
        devcheck.save()

        ar1.refresh_from_db()
        self.assertEqual(ar1.checks_status, ar1.ChecksStatus.SOME_CHECKS_FAILED)
        ar2.refresh_from_db()
        self.assertEqual(ar2.checks_status, ar2.ChecksStatus.SOME_CHECKS_FAILED)

        devcheck.accommodation.remove(accom1)
        devcheck.accommodation.add(accom2)
        devcheck.save()

        ar1.refresh_from_db()
        self.assertEqual(ar1.checks_status, ar1.ChecksStatus.SOME_CHECKS_FAILED)
        ar2.refresh_from_db()
        self.assertEqual(ar2.checks_status, ar2.ChecksStatus.CHECKS_REQUIRED)

    def test_updating_sponsor_m2m_affects_all_linked_ar_from_either_sponsor(self):
        sponsor1 = MvVolunteerFactory()
        sponsor2 = MvVolunteerFactory()
        ar1 = MvAccommodationRequestFactory(
            sponsor_id=[sponsor1.id, sponsor2.id],
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )
        ar2 = MvAccommodationRequestFactory(
            sponsor_id=[sponsor1.id],
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

        check_type = CheckType.objects.filter(id=CheckType.Id.SPONSOR_DBS).first()
        devcheck = DevCheckV2Factory(
            create_by=self.user.id,
            check_type=check_type,
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        devcheck.sponsor.add(sponsor1)
        devcheck.save()

        ar1.refresh_from_db()
        self.assertEqual(ar1.checks_status, ar1.ChecksStatus.SOME_CHECKS_FAILED)
        ar2.refresh_from_db()
        self.assertEqual(ar2.checks_status, ar2.ChecksStatus.SOME_CHECKS_FAILED)

        devcheck.sponsor.remove(sponsor1)
        devcheck.sponsor.add(sponsor2)
        devcheck.save()

        ar1.refresh_from_db()
        self.assertEqual(ar1.checks_status, ar1.ChecksStatus.SOME_CHECKS_FAILED)
        ar2.refresh_from_db()
        self.assertEqual(ar2.checks_status, ar2.ChecksStatus.CHECKS_REQUIRED)

    def test_sponsor_check_affects_all_linked_ar_related_to_the_sponsor(self):
        sponsor1 = MvVolunteerFactory()
        ar1 = MvAccommodationRequestFactory(
            sponsor_id=[sponsor1.id],
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )
        ar2 = MvAccommodationRequestFactory(
            primary_sponsor=sponsor1,
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )
        ar3 = MvAccommodationRequestFactory(
            active_host=sponsor1,
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
        )

        check_type = CheckType.objects.filter(id=CheckType.Id.SPONSOR_DBS).first()
        devcheck = DevCheckV2Factory(
            create_by=self.user.id,
            check_type=check_type,
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        devcheck.sponsor.add(sponsor1)
        devcheck.save()

        ar1.refresh_from_db()
        self.assertEqual(ar1.checks_status, ar1.ChecksStatus.SOME_CHECKS_FAILED)
        ar2.refresh_from_db()
        self.assertEqual(ar2.checks_status, ar2.ChecksStatus.SOME_CHECKS_FAILED)
        ar3.refresh_from_db()
        self.assertEqual(ar3.checks_status, ar3.ChecksStatus.SOME_CHECKS_FAILED)
