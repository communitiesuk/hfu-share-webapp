from deduplication.views import ManualGuestDeduplicationFilter
from ontology.models import MvPerson as Guest
from ontology.tests.factories import MvPersonFactory as GuestFactory
from test_utils.base import BaseTestCase


class GuestFilterSexTestCase(BaseTestCase):
    def setUp(self):
        self.male_guest = GuestFactory(
            gender="Male",
            is_principal=True,
        )

        self.female_guest = GuestFactory(
            gender="Female",
            is_principal=True,
        )

        self.no_data_sex_guest = GuestFactory(
            gender=None,
            is_principal=True,
        )

        self.unspecified_sex_guest = GuestFactory(
            gender="Unspecified",
            is_principal=True,
        )

    def test_filter_to_male_guests(self):
        filter_set = ManualGuestDeduplicationFilter(
            queryset=Guest.objects.all(),
            data={"sex": ["Male"]},
        )

        results = filter_set.qs
        guest_ids = results.values_list("id", flat=True)

        self.assertIn(self.male_guest.id, guest_ids)
        self.assertNotIn(self.female_guest.id, guest_ids)
        self.assertNotIn(self.no_data_sex_guest.id, guest_ids)
        self.assertNotIn(self.unspecified_sex_guest.id, guest_ids)

    def test_filter_to_female_guests(self):
        filter_set = ManualGuestDeduplicationFilter(
            queryset=Guest.objects.all(),
            data={"sex": ["Female"]},
        )

        results = filter_set.qs
        guest_ids = results.values_list("id", flat=True)

        self.assertNotIn(self.male_guest.id, guest_ids)
        self.assertIn(self.female_guest.id, guest_ids)
        self.assertNotIn(self.no_data_sex_guest.id, guest_ids)
        self.assertNotIn(self.unspecified_sex_guest.id, guest_ids)

    def test_filter_to_no_data_guests(self):
        filter_set = ManualGuestDeduplicationFilter(
            queryset=Guest.objects.all(),
            data={"sex": ["null"]},
        )

        results = filter_set.qs
        guest_ids = results.values_list("id", flat=True)

        self.assertNotIn(self.male_guest.id, guest_ids)
        self.assertNotIn(self.female_guest.id, guest_ids)
        self.assertIn(self.no_data_sex_guest.id, guest_ids)
        self.assertIn(self.unspecified_sex_guest.id, guest_ids)


class GuestFilterDateOfBirthTestCase(BaseTestCase):
    def setUp(self):
        self.guest_1 = GuestFactory(
            date_of_birth="2025-10-01",
            is_principal=True,
        )

        self.guest_2 = GuestFactory(
            date_of_birth="2025-10-05",
            is_principal=True,
        )

        self.guest_3 = GuestFactory(
            date_of_birth=None,
            is_principal=True,
        )

    def test_date_of_birth_filter(self):
        filter_set = ManualGuestDeduplicationFilter(
            queryset=Guest.objects.all(),
            data={
                "date_of_birth": "2025-09-30",
                "date_of_birth_1": "2025-10-02",
            },
        )

        results = filter_set.qs
        guest_ids = results.values_list("id", flat=True)

        self.assertEqual(len(results), 1)
        self.assertIn(self.guest_1.id, guest_ids)
        self.assertNotIn(self.guest_2.id, guest_ids)

    def test_date_of_birth_filter_null(self):
        filter_set = ManualGuestDeduplicationFilter(
            queryset=Guest.objects.all(),
            data={
                "date_of_birth": "2025-09-29",
                "date_of_birth_1": "2025-09-30",
            },
        )

        results = filter_set.qs
        self.assertEqual(len(results), 0)

    def test_invalid_date_of_birth_range(self):
        filter_set = ManualGuestDeduplicationFilter(
            queryset=Guest.objects.all(),
            data={
                "date_of_birth": "2023-01-31",
                "date_of_birth_1": "2023-01-01",
            },
        )

        self.assertFalse(filter_set.is_valid())
        self.assertIn(
            "date_of_birth",
            filter_set.errors,
        )
        self.assertIn(
            "Date of birth from date must be before date to.",
            filter_set.errors["date_of_birth"],
        )


class GuestFilterFirstArrivalDateTestCase(BaseTestCase):
    def setUp(self):
        self.person1 = GuestFactory(
            arrival_date="2025-10-01",
            is_principal=True,
        )

        self.person2 = GuestFactory(
            arrival_date="2025-10-05",
            is_principal=True,
        )

        self.person3 = GuestFactory(
            arrival_date=None,
            is_principal=True,
        )

    def test_first_arrival_date_filter(self):
        filter_set = ManualGuestDeduplicationFilter(
            queryset=Guest.objects.all(),
            data={
                "first_arrival_date": "2025-09-30",
                "first_arrival_date_1": "2025-10-02",
            },
        )

        results = filter_set.qs
        guest_ids = results.values_list("id", flat=True)

        self.assertEqual(len(results), 1)
        self.assertIn(self.person1.id, guest_ids)
        self.assertNotIn(self.person2.id, guest_ids)

    def test_first_arrival_date_filter_null(self):
        filter_set = ManualGuestDeduplicationFilter(
            queryset=Guest.objects.all(),
            data={
                "first_arrival_date": "2025-09-29",
                "first_arrival_date_1": "2025-09-30",
            },
        )

        results = filter_set.qs
        self.assertEqual(len(results), 0)

    def test_invalid_first_arrival_date_range(self):
        filter_set = ManualGuestDeduplicationFilter(
            queryset=Guest.objects.all(),
            data={
                "first_arrival_date": "2023-01-31",
                "first_arrival_date_1": "2023-01-01",
            },
        )

        self.assertFalse(filter_set.is_valid())
        self.assertIn(
            "first_arrival_date",
            filter_set.errors,
        )
        self.assertIn(
            "First arrival from date must be before date to.",
            filter_set.errors["first_arrival_date"],
        )


class GuestFilterVisaApplicationDateMaximumTestCase(BaseTestCase):
    def setUp(self):
        self.person1 = GuestFactory(
            visa_application_date_maximum="2025-10-01",
            is_principal=True,
        )

        self.person2 = GuestFactory(
            visa_application_date_maximum="2025-10-05",
            is_principal=True,
        )

        self.person3 = GuestFactory(
            visa_application_date_maximum=None,
            is_principal=True,
        )

    def test_visa_application_date_maximum_filter(self):
        filter_set = ManualGuestDeduplicationFilter(
            queryset=Guest.objects.all(),
            data={
                "visa_application_date_maximum": "2025-09-30",
                "visa_application_date_maximum_1": "2025-10-02",
            },
        )

        results = filter_set.qs
        guest_ids = results.values_list("id", flat=True)

        self.assertEqual(len(results), 1)
        self.assertIn(self.person1.id, guest_ids)
        self.assertNotIn(self.person2.id, guest_ids)

    def test_visa_application_date_maximum_filter_null(self):
        filter_set = ManualGuestDeduplicationFilter(
            queryset=Guest.objects.all(),
            data={
                "visa_application_date_maximum": "2025-09-29",
                "visa_application_date_maximum_1": "2025-09-30",
            },
        )

        results = filter_set.qs
        self.assertEqual(len(results), 0)

    def test_invalid_visa_application_date_maximum_range(self):
        filter_set = ManualGuestDeduplicationFilter(
            queryset=Guest.objects.all(),
            data={
                "visa_application_date_maximum": "2023-01-31",
                "visa_application_date_maximum_1": "2023-01-01",
            },
        )

        self.assertFalse(filter_set.is_valid())
        self.assertIn(
            "visa_application_date_maximum",
            filter_set.errors,
        )
        self.assertIn(
            "Latest visa application from date must be before date to.",
            filter_set.errors["visa_application_date_maximum"],
        )
