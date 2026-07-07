from django.test import TestCase

from ontology.tests.factories import MvVolunteerFactory


class MvVolunteerGetFullNameTestCase(TestCase):
    def test_get_full_name_returns_full_name_if_exists(self):
        volunteer = MvVolunteerFactory(
            full_name="Full Name", first_name="Full", last_name="Name"
        )

        full_name = volunteer.get_full_name()
        self.assertEqual(full_name, "Full Name")

    def test_get_full_name_fallsback_to_build_full_name_if_full_name_missing(self):
        volunteer = MvVolunteerFactory(
            full_name=None, first_name="First", last_name="Last"
        )

        full_name = volunteer.get_full_name()
        self.assertEqual(full_name, volunteer.build_full_name())


class MvVolunteerBuildFullNameTestCase(TestCase):
    def test_get_full_name_concats_first_and_last_name_both_exist(self):
        volunteer = MvVolunteerFactory(first_name="First", last_name="Last")

        full_name = volunteer.build_full_name()
        self.assertEqual(full_name, "First Last")

    def test_get_full_name_handles_nonexistant_last_name(self):
        volunteer = MvVolunteerFactory(first_name="First", last_name=None)

        full_name = volunteer.build_full_name()
        self.assertEqual(full_name, "First")

    def test_get_full_name_handles_nonexistant_first_name(self):
        volunteer = MvVolunteerFactory(first_name=None, last_name="Last")

        full_name = volunteer.build_full_name()
        self.assertEqual(full_name, "Last")

    def test_get_full_name_handles_both_nonexistant_first_and_last_names(self):
        volunteer = MvVolunteerFactory(first_name=None, last_name=None)

        full_name = volunteer.build_full_name()
        self.assertEqual(full_name, None)

    def test_get_full_name_appends_duplicate_prefix_if_required(self):
        volunteer = MvVolunteerFactory(
            first_name="First", last_name="Last", is_principal=False
        )

        full_name = volunteer.build_full_name()
        self.assertEqual(full_name, "First Last")
