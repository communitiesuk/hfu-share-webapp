from datetime import date

from django.test import TestCase

from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvUkPostcodeFactory,
)


class MvAccommodationRequestUpdateTitleTest(TestCase):
    def setUp(self):
        self.postcode = MvUkPostcodeFactory(
            postcode="SW1A2AA", postcode_formatted="SW1A 2AA"
        )
        self.accommodation = MvAccommodationFactory(
            full_address="18 Test Street", postcode=self.postcode
        )
        self.accommodation_request = MvAccommodationRequestFactory(
            primary_contact_first_name="Alice",
            primary_contact_last_name="Smith",
            primary_accommodation=self.accommodation,
            number_of_people=1,
        )
        self.accommodation_request.save = lambda: None  # prevent DB write during tests

    def test_combine_names(self):
        ar = self.accommodation_request
        self.assertEqual("Alice", ar._combine_names("Alice", None))
        self.assertEqual("Alice", ar._combine_names("Alice", ""))
        self.assertEqual("Smith", ar._combine_names(None, "Smith"))
        self.assertEqual("Smith", ar._combine_names("", "Smith"))
        self.assertEqual("Alice Smith", ar._combine_names("Alice", "Smith"))
        self.assertEqual("Unknown", ar._combine_names("", ""))
        self.assertEqual("Unknown", ar._combine_names(None, None))

    def test_title_with_no_primary_accommodation(self):
        self.accommodation_request.primary_accommodation = None
        new_title = self.accommodation_request._build_title()
        self.assertEqual("Alice Smith", new_title)

    def test_title_with_no_address(self):
        self.accommodation_request.primary_accommodation = MvAccommodationFactory(
            full_address=None, postcode=None
        )
        new_title = self.accommodation_request._build_title()
        self.assertEqual("Alice Smith to unknown address", new_title)

    def test_title_with_no_postcode(self):
        self.accommodation_request.primary_accommodation = MvAccommodationFactory(
            full_address="18 Test Str", postcode=None
        )
        new_title = self.accommodation_request._build_title()
        self.assertEqual("Alice Smith to 18 Test Str", new_title)

    def test_title_with_no_full_address(self):
        self.accommodation_request.primary_accommodation = MvAccommodationFactory(
            full_address=None, postcode=self.postcode
        )
        new_title = self.accommodation_request._build_title()
        self.assertEqual("Alice Smith to unknown address, SW1A 2AA", new_title)

    def test_title_with_address(self):
        self.accommodation_request.primary_accommodation = self.accommodation
        new_title = self.accommodation_request._build_title()
        self.assertEqual("Alice Smith to 18 Test Street, SW1A 2AA", new_title)

    def test_title_with_short_address(self):
        self.accommodation_request.primary_accommodation = MvAccommodationFactory(
            full_address="18DS", postcode=self.postcode
        )
        new_title = self.accommodation_request._build_title()
        self.assertEqual("Alice Smith to 18DS, SW1A 2AA", new_title)

    def test_title_with_two_people(self):
        self.accommodation_request.number_of_people = 2
        new_title = self.accommodation_request._build_title()
        self.assertEqual(
            "Alice Smith and 1 other to 18 Test Street, SW1A 2AA", new_title
        )

    def test_title_with_three_people(self):
        self.accommodation_request.number_of_people = 3
        new_title = self.accommodation_request._build_title()
        self.assertEqual(
            "Alice Smith and 2 others to 18 Test Street, SW1A 2AA", new_title
        )

    def test_update_for_person(self):
        person = MvPersonFactory(
            first_name="Alison",
            last_name="Jones",
            email=["a.jones@example.com"],
            email_for_questions=["a.jones+questions@example.com"],
            email_for_decision=["a.jones+decision@example.com"],
            email_after_decision=["a.jones+after+decision@example.com"],
            phone=["+44 7700 900 000"],
            can_be_contacted_by_phone=True,
        )

        ar = self.accommodation_request
        result = ar.update_primary_contact(person)

        self.assertTrue(result)
        self.assertEqual("Alison", ar.primary_contact_first_name)
        self.assertEqual("Jones", ar.primary_contact_last_name)
        self.assertEqual(["a.jones@example.com"], ar.primary_contact_email)
        self.assertEqual(
            ["a.jones+questions@example.com"], ar.primary_contact_email_for_questions
        )
        self.assertEqual(
            ["a.jones+decision@example.com"], ar.primary_contact_email_for_decision
        )
        self.assertEqual(
            ["a.jones+after+decision@example.com"],
            ar.primary_contact_email_after_decision,
        )
        self.assertEqual(["+44 7700 900 000"], ar.primary_contact_phone)
        self.assertTrue(ar.primary_contact_can_be_contacted_by_phone)

        result2 = ar.update_primary_contact(person)
        self.assertFalse(result2)

    def test_is_primary_contact(self):
        alison = MvPersonFactory(
            first_name="Alison",
            last_name="Jones",
            date_of_birth=date(1990, 1, 1),
            age=35,
        )
        bob = MvPersonFactory(
            first_name="Bob", last_name="Smith", date_of_birth=date(2000, 1, 1), age=25
        )
        charlie = MvPersonFactory(
            first_name="Charlie", last_name="Roberts", date_of_birth=None, age=5
        )

        ar = self.accommodation_request

        ar.person_id = [charlie.id, bob.id, alison.id]
        self.assertTrue(ar.is_primary_contact(alison))
        self.assertFalse(ar.is_primary_contact(bob))
        self.assertFalse(ar.is_primary_contact(charlie))

        ar.person_id = [charlie.id, bob.id]
        self.assertFalse(ar.is_primary_contact(alison))
        self.assertTrue(ar.is_primary_contact(bob))
        self.assertFalse(ar.is_primary_contact(charlie))

        ar.person_id = [charlie.id]
        self.assertFalse(ar.is_primary_contact(alison))
        self.assertFalse(ar.is_primary_contact(bob))
        self.assertTrue(ar.is_primary_contact(charlie))

        ar.person_id = []
        self.assertFalse(ar.is_primary_contact(alison))
        self.assertFalse(ar.is_primary_contact(bob))
        self.assertFalse(ar.is_primary_contact(charlie))

    def test_empty_group_title_with_no_accommodation(self):
        self.accommodation_request.person_id = []
        self.accommodation_request.primary_accommodation = None
        new_title = self.accommodation_request._build_title()
        self.assertEqual("Empty group", new_title)

    def test_empty_group_title_with_accommodation(self):
        self.accommodation_request.person_id = []
        self.accommodation_request.primary_accommodation = self.accommodation
        new_title = self.accommodation_request._build_title()
        self.assertEqual("Empty group to 18 Test Street, SW1A 2AA", new_title)
