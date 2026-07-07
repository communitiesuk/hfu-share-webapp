from django.test import TestCase

from ontology.tests.factories import MvPersonFactory


class MvPersonGetFullNameTestCase(TestCase):
    def test_get_full_name_concats_first_and_last_name_if_both_exist(self):
        person = MvPersonFactory(first_name="First", last_name="Last")

        full_name = person.get_full_name()
        self.assertEqual(full_name, "First Last")

    def test_get_full_name_handles_nonexistant_last_name(self):
        person = MvPersonFactory(first_name="First", last_name=None)

        full_name = person.get_full_name()
        self.assertEqual(full_name, "First")

    def test_get_full_name_handles_nonexistant_first_name(self):
        person = MvPersonFactory(first_name=None, last_name="Last")

        full_name = person.get_full_name()
        self.assertEqual(full_name, "Last")

    def test_get_full_name_handles_both_nonexistant_first_and_last_names(self):
        person = MvPersonFactory(first_name=None, last_name=None)

        full_name = person.get_full_name()
        self.assertEqual(full_name, None)
