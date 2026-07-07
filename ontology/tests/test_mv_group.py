from django.test import TestCase

from ontology.tests.factories import MvGroupFactory, MvPersonFactory


class MvGroupTest(TestCase):
    def test_group_with_correct_foreign_key_works(self):
        MvGroupFactory(id="Group-123")
        group = MvGroupFactory(
            old_split_group_id="Group-123",
            merged_group_id="Group-123",
        )

        # Doesn't raise error
        self.assertEqual(group.old_split_group_id, "Group-123")

    def test_old_group_id_with_nonexistent_value_doesnt_raise_error(self):
        # Won't raise Key constraint exception
        group = MvGroupFactory(old_split_group_id="inexistent_old_group_id")

        self.assertEqual(group.old_split_group_id, "inexistent_old_group_id")

    def test_merged_group_id_with_nonexistent_value_doesnt_raise_error(self):
        # Won't raise Key constraint exception
        group = MvGroupFactory(merged_group_id="inexistent_merged_group_id")

        self.assertEqual(group.merged_group_id, "inexistent_merged_group_id")


class MvGroupSplitMethodsTest(TestCase):
    def test_min_age_with_empty_list(self):
        group = MvGroupFactory()

        result = group._min_age([])

        self.assertIsNone(result)

    def test_min_age_with_guests(self):
        group = MvGroupFactory()
        person_1 = MvPersonFactory(age=25, group=group)
        person_2 = MvPersonFactory(age=30, group=group)

        result = group._min_age([person_1, person_2])

        self.assertEqual(result, 25)

    def test_max_age_with_empty_list(self):
        group = MvGroupFactory()

        result = group._max_age([])

        self.assertIsNone(result)

    def test_max_age_with_guests(self):
        group = MvGroupFactory()
        person_1 = MvPersonFactory(age=25, group=group)
        person_2 = MvPersonFactory(age=30, group=group)
        person_3 = MvPersonFactory(age=45, group=group)

        result = group._max_age([person_1, person_2, person_3])

        self.assertEqual(result, 45)

    def test_primary_contact_with_empty_list(self):
        group = MvGroupFactory()

        result = group._primary_contact([])

        self.assertIsNone(result)

    def test_primary_contact_returns_guest(self):
        group = MvGroupFactory()
        person_1 = MvPersonFactory(age=25, group=group)
        person_2 = MvPersonFactory(age=30, group=group)
        person_3 = MvPersonFactory(age=45, group=group)

        result = group._primary_contact([person_1, person_2, person_3])

        self.assertEqual(result, person_3)

    def test_primary_name_with_both_names(self):
        group = MvGroupFactory(
            primary_contact_first_name="John",
            primary_contact_last_name="Doe",
        )

        result = group._primary_name()

        self.assertEqual(result, "John Doe")

    def test_primary_name_with_only_first_name(self):
        group = MvGroupFactory(
            primary_contact_first_name="John",
            primary_contact_last_name=None,
        )

        result = group._primary_name()

        self.assertEqual(result, "John")

    def test_primary_name_with_only_last_name(self):
        group = MvGroupFactory(
            primary_contact_first_name=None,
            primary_contact_last_name="Doe",
        )

        result = group._primary_name()

        self.assertEqual(result, "Doe")

    def test_primary_name_with_none(self):
        group = MvGroupFactory()

        result = group._primary_name()

        self.assertEqual(result, "Unknown")

    def test_build_title_single_person(self):
        group = MvGroupFactory(
            primary_contact_first_name="John",
            primary_contact_last_name="Doe",
            number_of_people_in_group=1,
        )

        result = group._build_title()

        self.assertEqual(result, "John Doe")

    def test_build_title_two_people(self):
        group = MvGroupFactory(
            primary_contact_first_name="John",
            primary_contact_last_name="Doe",
            number_of_people_in_group=2,
        )

        MvPersonFactory(first_name="John", last_name="Doe", group=group)
        MvPersonFactory(first_name="Jane", last_name="Smith", group=group)

        result = group._build_title()

        self.assertEqual(result, "John Doe and 1 other")

    def test_build_title_multiple_people(self):
        group = MvGroupFactory(
            primary_contact_first_name="John",
            primary_contact_last_name="Doe",
            number_of_people_in_group=3,
        )

        MvPersonFactory(first_name="John", last_name="Doe", group=group)
        MvPersonFactory(first_name="Jane", last_name="Smith", group=group)
        MvPersonFactory(first_name="Alice", last_name="Johnson", group=group)

        result = group._build_title()

        self.assertEqual(result, "John Doe and 2 others")

    def test_build_title_with_no_names(self):
        group = MvGroupFactory(
            primary_contact_first_name=None,
            primary_contact_last_name=None,
            number_of_people_in_group=3,
        )
        MvPersonFactory(first_name=None, last_name=None, group=group)
        MvPersonFactory(first_name="Jane", last_name="Smith", group=group)
        MvPersonFactory(first_name="Alice", last_name="Johnson", group=group)

        result = group._build_title()

        self.assertEqual(result, "Unknown and 2 others")

    def test_refresh_data_updates_group_fields(self):
        group = MvGroupFactory(id="test-group-123")

        MvPersonFactory(
            id="person-1",
            group=group,
            age=25,
            first_name="John",
            last_name="Doe",
            application_number=["APP001"],
            phone=["123-456-7890"],
            email=["john@example.com"],
            email_for_questions=["john.questions@example.com"],
            email_for_decision=["john.decision@example.com"],
            email_after_decision=["john.after@example.com"],
        )

        MvPersonFactory(
            id="person-2",
            group=group,
            age=30,
            first_name="Jane",
            last_name="Smith",
            application_number=["APP002"],
            phone=["098-765-4321"],
            email=["jane@example.com"],
        )

        MvPersonFactory(
            id="person-3",
            group=group,
            age=45,
            first_name="Alice",
            last_name="Johnson",
            application_number=["APP003"],
            phone=["555-123-4567"],
            email=["alice@example.com"],
            email_for_questions=["alice.questions@example.com"],
            email_for_decision=["alice.decision@example.com"],
            email_after_decision=["alice.after@example.com"],
            can_be_contacted_by_phone="No",
        )

        group.refresh_data()

        group.refresh_from_db()

        # Assert application numbers are collected
        expected_app_numbers = ["APP001", "APP002", "APP003"]
        self.assertEqual(sorted(group.application_number), sorted(expected_app_numbers))

        # Assert group size
        self.assertEqual(group.number_of_people_in_group, 3)

        # Assert min and max ages
        self.assertEqual(group.min_age, 25)
        self.assertEqual(group.max_age, 45)

        # Assert primary contact is the oldest person (Alice)
        self.assertEqual(group.primary_contact_first_name, "Alice")
        self.assertEqual(group.primary_contact_last_name, "Johnson")
        self.assertEqual(group.primary_contact_phone, ["555-123-4567"])
        self.assertEqual(group.primary_contact_email, ["alice@example.com"])
        self.assertEqual(
            group.primary_contact_email_for_questions, ["alice.questions@example.com"]
        )
        self.assertEqual(
            group.primary_contact_email_for_decision, ["alice.decision@example.com"]
        )
        self.assertEqual(
            group.primary_contact_email_after_decision, ["alice.after@example.com"]
        )
        self.assertEqual(group.primary_contact_can_be_contacted_by_phone, "No")

        # Assert title is correctly built
        self.assertEqual(group.title, "Alice Johnson and 2 others")

    def test_refresh_data_with_no_persons(self):
        group = MvGroupFactory(id="empty-group")

        group.refresh_data()

        group.refresh_from_db()

        # Assert fields are set to appropriate defaults
        self.assertEqual(group.application_number, [])
        self.assertEqual(group.number_of_people_in_group, 0)
        self.assertIsNone(group.min_age)
        self.assertIsNone(group.max_age)

        # Assert primary contact fields are None
        self.assertIsNone(group.primary_contact_first_name)
        self.assertIsNone(group.primary_contact_last_name)
        self.assertIsNone(group.primary_contact_phone)
        self.assertIsNone(group.primary_contact_email)
        self.assertIsNone(group.primary_contact_email_for_questions)
        self.assertIsNone(group.primary_contact_email_for_decision)
        self.assertIsNone(group.primary_contact_email_after_decision)
        self.assertIsNone(group.primary_contact_can_be_contacted_by_phone)

        # Assert title is built correctly with no primary contact
        self.assertEqual(group.title, "Unknown")

    def test_split_group_creates_new_group_and_moves_persons(self):
        original_group = MvGroupFactory(id="original-group")

        person_1 = MvPersonFactory(
            id="person-1",
            group=original_group,
            age=25,
            first_name="John",
            last_name="Doe",
            application_number=["APP001"],
        )
        person_2 = MvPersonFactory(
            id="person-2",
            group=original_group,
            age=30,
            first_name="Jane",
            last_name="Smith",
            application_number=["APP002"],
        )
        person_3 = MvPersonFactory(
            id="person-3",
            group=original_group,
            age=45,
            first_name="Alice",
            last_name="Johnson",
            application_number=["APP003"],
        )

        original_group.refresh_data()
        original_group.refresh_from_db()

        self.assertEqual(original_group.number_of_people_in_group, 3)
        self.assertEqual(
            sorted(original_group.application_number), ["APP001", "APP002", "APP003"]
        )
        self.assertEqual(original_group.primary_contact_first_name, "Alice")

        new_group = original_group.split_group(["person-1", "person-2"])

        original_group.refresh_from_db()
        new_group.refresh_from_db()

        # Assert new group properties
        self.assertIsNotNone(new_group.id)
        self.assertNotEqual(new_group.id, original_group.id)
        self.assertEqual(new_group.old_split_group_id, original_group.id)

        # Assert new group has correct persons and data
        self.assertEqual(new_group.number_of_people_in_group, 2)
        self.assertEqual(sorted(new_group.application_number), ["APP001", "APP002"])
        self.assertEqual(new_group.min_age, 25)
        self.assertEqual(new_group.max_age, 30)
        # Primary contact should be Jane (oldest in new group)
        self.assertEqual(new_group.primary_contact_first_name, "Jane")
        self.assertEqual(new_group.primary_contact_last_name, "Smith")
        self.assertEqual(new_group.title, "Jane Smith and 1 other")

        # Assert original group has remaining person and updated data
        self.assertEqual(original_group.number_of_people_in_group, 1)
        self.assertEqual(original_group.application_number, ["APP003"])
        self.assertEqual(original_group.min_age, 45)
        self.assertEqual(original_group.max_age, 45)
        # Primary contact should be Alice (only person left)
        self.assertEqual(original_group.primary_contact_first_name, "Alice")
        self.assertEqual(original_group.primary_contact_last_name, "Johnson")
        self.assertEqual(original_group.title, "Alice Johnson")

        # Verify persons are in correct groups
        person_1.refresh_from_db()
        person_2.refresh_from_db()
        person_3.refresh_from_db()

        self.assertEqual(person_1.group_id, new_group.id)
        self.assertEqual(person_2.group_id, new_group.id)
        self.assertEqual(person_3.group_id, original_group.id)
