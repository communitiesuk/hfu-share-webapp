from datetime import datetime, timedelta

from django.test import TestCase

from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvGroupFactory,
    MvPersonFactory,
    MvUkPostcodeFactory,
)


class MvAccommodationRequestSplitGuestsTest(TestCase):
    def test_split_guests(self):
        postcode = MvUkPostcodeFactory(postcode="", postcode_formatted="SW1A 2AA")
        accommodation = MvAccommodationFactory(
            full_address="123 Test Street", postcode=postcode
        )
        guest1 = MvPersonFactory(
            first_name="Guest1",
            last_name="Surname1",
            date_of_birth=datetime.now() - timedelta(days=10 * 365),
        )
        guest2 = MvPersonFactory(
            first_name="Guest2",
            last_name="Surname2",
            date_of_birth=datetime.now() - timedelta(days=20 * 365),
        )
        guest3 = MvPersonFactory(
            first_name="Guest3",
            last_name="Surname3",
            date_of_birth=datetime.now() - timedelta(days=30 * 365),
        )
        accommodation_request = MvAccommodationRequestFactory(
            person_id=[guest1.id, guest2.id, guest3.id],
            primary_accommodation=accommodation,
        )

        new_request = accommodation_request.split_guests([guest2.id])

        # check new request is created
        self.assertNotEqual(new_request.id, accommodation_request.id)

        # check number of people is updated
        self.assertEqual(1, new_request.number_of_people)
        self.assertEqual(2, accommodation_request.number_of_people)

        # check primary accommodation is set
        self.assertEqual(guest2.first_name, new_request.primary_contact_first_name)
        self.assertEqual(guest2.last_name, new_request.primary_contact_last_name)
        self.assertEqual(
            guest3.first_name,
            accommodation_request.primary_contact_first_name,
        )
        self.assertEqual(
            guest3.last_name, accommodation_request.primary_contact_last_name
        )

        # test title is updated
        self.assertEqual(
            "Guest2 Surname2 to 123 Test Stree, SW1A 2AA", new_request.title
        )
        self.assertEqual(
            "Guest3 Surname3 and 1 other to 123 Test Stree, SW1A 2AA",
            accommodation_request.title,
        )

        # check guests are linked to new request
        guest2.refresh_from_db()
        self.assertEqual(guest2.accommodation_request.id, str(new_request.id))

    def test_split_guests_with_nonexistent_group_id(self):
        guest1 = MvPersonFactory(
            first_name="Guest1",
            last_name="Surname1",
        )
        guest2 = MvPersonFactory(
            first_name="Guest2",
            last_name="Surname2",
        )
        guest3 = MvPersonFactory(
            first_name="Guest3",
            last_name="Surname3",
        )

        accommodation_request = MvAccommodationRequestFactory(
            person_id=[guest1.id, guest2.id, guest3.id],
            group_id="nonexistent-group-id",
            number_of_people=3,
        )

        # Split ar guests
        new_request = accommodation_request.split_guests([guest3.id])
        accommodation_request.refresh_from_db()

        self.assertNotEqual(new_request.id, accommodation_request.id)

        # Check new request details
        self.assertEqual(new_request.number_of_people, 1)
        self.assertEqual(new_request.person_id, [guest3.id])
        self.assertEqual(new_request.group_id, None)

        # Original request details
        self.assertEqual(accommodation_request.number_of_people, 2)
        self.assertEqual(accommodation_request.person_id, [guest1.id, guest2.id])
        self.assertEqual(accommodation_request.group_id, "nonexistent-group-id")

    def test_split_guests_with_group(self):
        group = MvGroupFactory(id="original-group")
        guest1 = MvPersonFactory(
            first_name="John", last_name="Doe", age=25, group=group
        )
        guest2 = MvPersonFactory(
            first_name="Jane", last_name="Smith", age=30, group=group
        )
        guest3 = MvPersonFactory(
            first_name="Alice", last_name="Johnson", age=35, group=group
        )

        accommodation_request = MvAccommodationRequestFactory(
            person_id=[guest1.id, guest2.id, guest3.id],
            group=group,
        )

        # Split guests
        new_request = accommodation_request.split_guests([guest2.id])

        accommodation_request.refresh_from_db()
        guest1.refresh_from_db()
        guest2.refresh_from_db()
        guest3.refresh_from_db()

        # Verify new request was created
        self.assertNotEqual(new_request.id, accommodation_request.id)

        # Check new request details
        self.assertEqual(new_request.number_of_people, 1)
        self.assertEqual(str(new_request.group_id), guest2.group_id)
        self.assertEqual(new_request.person_id, [guest2.id])

        # Original request details
        self.assertEqual(accommodation_request.number_of_people, 2)
        self.assertTrue(guest1.id in accommodation_request.person_id)
        self.assertTrue(guest3.id in accommodation_request.person_id)
        self.assertEqual(accommodation_request.group_id, "original-group")

        # Verify primary contacts
        self.assertEqual(new_request.primary_contact_first_name, "Jane")
        self.assertEqual(new_request.primary_contact_last_name, "Smith")
        self.assertEqual(new_request.group.primary_contact_first_name, "Jane")
        self.assertEqual(new_request.group.primary_contact_last_name, "Smith")
        self.assertEqual(accommodation_request.primary_contact_first_name, "Alice")
        self.assertEqual(accommodation_request.primary_contact_last_name, "Johnson")
        self.assertEqual(
            accommodation_request.group.primary_contact_first_name, "Alice"
        )
        self.assertEqual(
            accommodation_request.group.primary_contact_last_name, "Johnson"
        )
