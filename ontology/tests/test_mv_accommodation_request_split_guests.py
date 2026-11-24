from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

from django.utils import timezone

from accounts.tests.factories import UserFactory
from ontology.models import MvPerson
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvGroupFactory,
    MvPersonFactory,
    MvUkPostcodeFactory,
)
from test_utils.base import BaseTestCase


class MvAccommodationRequestSplitGuestsTest(BaseTestCase):
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

        new_request = accommodation_request.split_guests(
            [guest2.id], author=UserFactory()
        )

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
        new_request = accommodation_request.split_guests(
            [guest3.id], author=UserFactory()
        )
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
        new_request = accommodation_request.split_guests(
            [guest2.id], author=UserFactory()
        )

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

    def test_split_guests_flags_moved_guests_as_edited_in_app(self):
        guest1 = MvPersonFactory(first_name="Guest1")
        guest2 = MvPersonFactory(first_name="Guest2")

        accommodation_request = MvAccommodationRequestFactory(
            person_id=[guest1.id, guest2.id],
        )

        MvPerson.objects.filter(id__in=[guest1.id, guest2.id]).update(
            edited_in_app=False
        )

        accommodation_request.split_guests([guest2.id], author=UserFactory())

        guest2.refresh_from_db()
        guest1.refresh_from_db()

        self.assertTrue(guest2.edited_in_app)
        self.assertFalse(guest1.edited_in_app)

    def test_split_guests_sets_created_at_and_created_by_on_new_ar(self):
        guest1 = MvPersonFactory(first_name="Guest1")
        guest2 = MvPersonFactory(first_name="Guest2")
        original_created_at = datetime(2022, 3, 1, tzinfo=dt_timezone.utc)
        accommodation_request = MvAccommodationRequestFactory(
            person_id=[guest1.id, guest2.id],
            created_at=original_created_at,
            created_by="test",
        )
        author = UserFactory()

        before_split = timezone.now()
        new_request = accommodation_request.split_guests([guest2.id], author=author)

        new_request.refresh_from_db()
        accommodation_request.refresh_from_db()
        self.assertGreaterEqual(new_request.created_at, before_split)
        self.assertEqual(new_request.created_by, author.email)
        self.assertEqual(accommodation_request.created_at, original_created_at)
        self.assertEqual(accommodation_request.created_by, "test")


class MvAccommodationRequestSplitGuestsIsUamTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.child = MvPersonFactory(first_name="Child", is_uam=True)
        self.sibling = MvPersonFactory(first_name="Sibling", is_uam=False)
        self.accommodation_request = MvAccommodationRequestFactory(
            person_id=[self.child.id, self.sibling.id],
            is_uam=True,
            is_uam_edited_time=None,
        )

    def test_moving_non_uam_guest_unflags_new_ar(self):
        new_request = self.accommodation_request.split_guests(
            [self.sibling.id], author=UserFactory()
        )

        new_request.refresh_from_db()
        self.accommodation_request.refresh_from_db()
        self.assertFalse(new_request.is_uam)
        self.assertIsNotNone(new_request.is_uam_edited_time)
        self.assertTrue(self.accommodation_request.is_uam)
        self.assertIsNone(self.accommodation_request.is_uam_edited_time)

    def test_moving_uam_guest_unflags_original_ar(self):
        new_request = self.accommodation_request.split_guests(
            [self.child.id], author=UserFactory()
        )

        new_request.refresh_from_db()
        self.accommodation_request.refresh_from_db()
        self.assertTrue(new_request.is_uam)
        self.assertFalse(self.accommodation_request.is_uam)
        self.assertIsNotNone(self.accommodation_request.is_uam_edited_time)

    def test_moving_uam_guest_flags_new_ar_when_original_was_not_flagged(self):
        self.accommodation_request.is_uam = None
        self.accommodation_request.save()

        new_request = self.accommodation_request.split_guests(
            [self.child.id], author=UserFactory()
        )

        new_request.refresh_from_db()
        self.accommodation_request.refresh_from_db()
        self.assertTrue(new_request.is_uam)
        self.assertIsNotNone(new_request.is_uam_edited_time)
        self.assertFalse(self.accommodation_request.is_uam)
        self.assertIsNotNone(self.accommodation_request.is_uam_edited_time)
