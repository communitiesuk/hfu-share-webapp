from django.test import TestCase

from guests.views import GuestsFilter
from ontology.models import MvPerson
from ontology.tests.factories import MvPersonFactory


class GuestFilterSexTestCase(TestCase):
    def setUp(self):
        self.male_guest = MvPersonFactory(
            gender="Male",
            is_principal=True,
        )

        self.female_guest = MvPersonFactory(
            gender="Female",
            is_principal=True,
        )

        self.no_data_sex_guest = MvPersonFactory(
            gender=None,
            is_principal=True,
        )

        self.unspecified_sex_guest = MvPersonFactory(
            gender="Unspecified",
            is_principal=True,
        )

    def test_filter_to_male_guests(self):
        filter_set = GuestsFilter(
            queryset=MvPerson.objects.all(),
            data={"sex": ["Male"]},
        )

        results = filter_set.qs
        guest_ids = results.values_list("id", flat=True)

        self.assertIn(self.male_guest.id, guest_ids)
        self.assertNotIn(self.female_guest.id, guest_ids)
        self.assertNotIn(self.no_data_sex_guest.id, guest_ids)
        self.assertNotIn(self.unspecified_sex_guest.id, guest_ids)

    def test_filter_to_female_guests(self):
        filter_set = GuestsFilter(
            queryset=MvPerson.objects.all(),
            data={"sex": ["Female"]},
        )

        results = filter_set.qs
        guest_ids = results.values_list("id", flat=True)

        self.assertNotIn(self.male_guest.id, guest_ids)
        self.assertIn(self.female_guest.id, guest_ids)
        self.assertNotIn(self.no_data_sex_guest.id, guest_ids)
        self.assertNotIn(self.unspecified_sex_guest.id, guest_ids)

    def test_filter_to_no_data_guests(self):
        filter_set = GuestsFilter(
            queryset=MvPerson.objects.all(),
            data={"sex": ["null"]},
        )

        results = filter_set.qs
        guest_ids = results.values_list("id", flat=True)

        self.assertNotIn(self.male_guest.id, guest_ids)
        self.assertNotIn(self.female_guest.id, guest_ids)
        self.assertIn(self.no_data_sex_guest.id, guest_ids)
        self.assertIn(self.unspecified_sex_guest.id, guest_ids)


class GuestFilterFirstArrivalDateTestCase(TestCase):
    def setUp(self):
        self.person1 = MvPersonFactory(
            arrival_date="2025-10-01",
            is_principal=True,
        )

        self.person2 = MvPersonFactory(
            arrival_date="2025-10-05",
            is_principal=True,
        )

        self.person3 = MvPersonFactory(
            arrival_date=None,
            is_principal=True,
        )

    def test_first_arrival_date_filter(self):
        filter_set = GuestsFilter(
            queryset=MvPerson.objects.all(),
            data={
                "first_arrival_date_0": "2025-09-30",
                "first_arrival_date_1": "2025-10-02",
            },
        )

        results = filter_set.qs
        guest_ids = results.values_list("id", flat=True)

        self.assertEqual(len(results), 1)
        self.assertIn(self.person1.id, guest_ids)
        self.assertNotIn(self.person2.id, guest_ids)

    def test_first_arrival_date_filter_null(self):
        filter_set = GuestsFilter(
            queryset=MvPerson.objects.all(),
            data={
                "first_arrival_date_0": "2025-09-29",
                "first_arrival_date_1": "2025-09-30",
            },
        )

        results = filter_set.qs
        self.assertEqual(len(results), 0)


class GuestFilterIncludeDuplicatesTestCase(TestCase):
    def setUp(self):
        self.record_1 = MvPersonFactory(is_principal=True)
        self.record_2 = MvPersonFactory(is_principal=False)
        self.record_3 = MvPersonFactory(is_principal=None)

    def test_filter_duplicates(self):
        filter_set = GuestsFilter(
            queryset=MvPerson.objects.all(),
            data={},
        )

        results = filter_set.qs
        guest_ids = results.values_list("id", flat=True)

        self.assertIn(self.record_1.id, guest_ids)
        self.assertNotIn(self.record_2.id, guest_ids)
        self.assertNotIn(self.record_3.id, guest_ids)

        filter_set = GuestsFilter(
            queryset=MvPerson.objects.all(),
            data={"include_duplicates": "Yes"},
        )

        results = filter_set.qs
        guest_ids = results.values_list("id", flat=True)

        self.assertIn(self.record_1.id, guest_ids)
        self.assertIn(self.record_2.id, guest_ids)
        self.assertIn(self.record_3.id, guest_ids)
