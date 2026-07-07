from django.test import TestCase

from accounts.tests.factories import UserFactory
from ontology.models import CheckType, DevCheckV2
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvUkPostcodeFactory,
)


class AccommodationRequestTitleSignalTests(TestCase):
    def setUp(self):
        super().setUp()

        self.postcode = MvUkPostcodeFactory(postcode_formatted="SW1A 2AA")
        self.person = MvPersonFactory(first_name="Alice", last_name="Smith")
        self.accommodation = MvAccommodationFactory(
            full_address="10 Downing Street", postcode=self.postcode
        )
        self.accommodation_request = MvAccommodationRequestFactory(
            primary_contact_first_name=self.person.first_name,
            primary_contact_last_name=self.person.last_name,
            person_id=[self.person.id],
            primary_accommodation=self.accommodation,
            number_of_people=1,
        )

    def test_title_updates_on_person_name_change(self):
        self.person.first_name = "Alison"
        self.person.last_name = "Jones"
        self.person.save()
        self.accommodation_request.refresh_from_db()
        self.assertIn("Alison Jones", self.accommodation_request.title)
        self.assertTrue(self.accommodation_request.edited_in_app)

    def test_title_updates_on_accommodation_address_change(self):
        self.accommodation.full_address = "11 Whitehall"
        self.accommodation.save()
        self.accommodation_request.refresh_from_db()
        self.assertIn("11 Whitehall", self.accommodation_request.title)
        self.assertTrue(self.accommodation_request.edited_in_app)

    def test_title_updates_on_accommodation_postcode_change(self):
        new_postcode = MvUkPostcodeFactory(postcode_formatted="NEW 2BB")

        self.accommodation.postcode = new_postcode
        self.accommodation.save()
        self.accommodation_request.refresh_from_db()
        self.assertIn("NEW 2BB", self.accommodation_request.title)
        self.assertTrue(self.accommodation_request.edited_in_app)


class DevCheckV2PostSaveSignalTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.accommodation = MvAccommodationFactory()
        self.accommodation_request = MvAccommodationRequestFactory(
            primary_accommodation=self.accommodation
        )
        self.devcheck = DevCheckV2Factory(create_by=self.user.id)
        self.devcheck.AR.add(self.accommodation_request)
        self.acc_exists_check_type = CheckType.objects.filter(
            id=CheckType.Id.ACCOMM_EXISTS
        ).first()

    def test_ar_checks_status_reflects_devcheck_status_change(self):
        devcheck = DevCheckV2Factory(
            check_type=self.acc_exists_check_type,
            check_status=DevCheckV2.CheckStatus.FAILED,
            create_by=self.user.id,
        )
        devcheck.accommodation.set([self.accommodation])
        devcheck.AR.add(self.accommodation_request)
        devcheck.save()

        self.accommodation_request.refresh_from_db()
        self.assertEqual(
            self.accommodation_request.checks_status,
            self.accommodation_request.ChecksStatus.SOME_CHECKS_FAILED,
        )

        devcheck.check_status = DevCheckV2.CheckStatus.PASSED
        devcheck.save()
        self.accommodation_request.refresh_from_db()

        self.assertEqual(
            self.accommodation_request.checks_status,
            self.accommodation_request.ChecksStatus.CHECKS_PARTIALLY_COMPLETED,
        )
        self.assertTrue(self.accommodation_request.edited_in_app)

    def test_ar_checks_status_works_with_author_uuid(self):
        self.accommodation_request.last_modified_by = (
            "550e8400-e29b-41d4-a716-446655440000"
        )
        self.accommodation_request.save()

        devcheck = DevCheckV2Factory(
            check_type=self.acc_exists_check_type,
            check_status=DevCheckV2.CheckStatus.FAILED,
            create_by="550e8400-e29b-41d4-a716-446655440000",
        )

        devcheck.accommodation.set([self.accommodation])
        devcheck.AR.add(self.accommodation_request)
        devcheck.save()

        self.accommodation_request.refresh_from_db()

        # last_modified_by is set to None if create_by is not an int
        self.assertIsNone(self.accommodation_request.last_modified_by)

        devcheck.create_by = self.user.id
        devcheck.check_status = DevCheckV2.CheckStatus.PASSED
        devcheck.save()

        self.accommodation_request.refresh_from_db()

        # last_modified_by is set to user full name if create_by is int
        self.assertEqual(
            self.accommodation_request.last_modified_by, self.user.get_full_name()
        )
