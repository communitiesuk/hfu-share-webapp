from datetime import datetime

from django.test import TestCase
from django.utils import timezone

from ontology.models import MvVolunteer
from ontology.tests.factories import MvVolunteerFactory
from sponsors.views import SponsorsFilter


class SponsorFilterSexTestCase(TestCase):
    def setUp(self):
        self.male_sponsor = MvVolunteerFactory(sex="Male", is_principal=True)
        self.female_sponsor = MvVolunteerFactory(sex="Female", is_principal=True)
        self.no_data_sex_sponsor = MvVolunteerFactory(sex=None, is_principal=True)

    def test_filter_to_male_sponsors(self):
        filter_set = SponsorsFilter(
            queryset=MvVolunteer.objects.all(),
            data={"sex": ["Male"]},
        )

        results = filter_set.qs
        sponsor_ids = results.values_list("id", flat=True)

        self.assertIn(self.male_sponsor.id, sponsor_ids)
        self.assertNotIn(self.female_sponsor.id, sponsor_ids)
        self.assertNotIn(self.no_data_sex_sponsor.id, sponsor_ids)

    def test_filter_to_female_sponsors(self):
        filter_set = SponsorsFilter(
            queryset=MvVolunteer.objects.all(),
            data={"sex": ["Female"]},
        )

        results = filter_set.qs
        sponsor_ids = results.values_list("id", flat=True)

        self.assertNotIn(self.male_sponsor.id, sponsor_ids)
        self.assertIn(self.female_sponsor.id, sponsor_ids)
        self.assertNotIn(self.no_data_sex_sponsor.id, sponsor_ids)

    def test_filter_to_no_data_sponsors(self):
        filter_set = SponsorsFilter(
            queryset=MvVolunteer.objects.all(),
            data={"sex": ["null"]},
        )

        results = filter_set.qs
        sponsor_ids = results.values_list("id", flat=True)

        self.assertNotIn(self.male_sponsor.id, sponsor_ids)
        self.assertNotIn(self.female_sponsor.id, sponsor_ids)
        self.assertIn(self.no_data_sex_sponsor.id, sponsor_ids)


class SponsorFilterDateOfBirthTestCase(TestCase):
    def setUp(self):
        self.sponsor_1 = MvVolunteerFactory(
            date_of_birth="2025-10-01",
            is_principal=True,
        )

        self.sponsor_2 = MvVolunteerFactory(
            date_of_birth="2025-10-05",
            is_principal=True,
        )

        self.sponsor_3 = MvVolunteerFactory(
            date_of_birth=None,
            is_principal=True,
        )

    def test_date_of_birth_filter(self):
        filter_set = SponsorsFilter(
            queryset=MvVolunteer.objects.all(),
            data={
                "date_of_birth_0": "2025-09-30",
                "date_of_birth_1": "2025-10-02",
            },
        )

        results = filter_set.qs
        sponsor_ids = results.values_list("id", flat=True)

        self.assertEqual(len(results), 1)
        self.assertIn(self.sponsor_1.id, sponsor_ids)
        self.assertNotIn(self.sponsor_2.id, sponsor_ids)

    def test_date_of_birth_filter_null(self):
        filter_set = SponsorsFilter(
            queryset=MvVolunteer.objects.all(),
            data={
                "date_of_birth_0": "2025-09-29",
                "date_of_birth_1": "2025-09-30",
            },
        )

        results = filter_set.qs
        self.assertEqual(len(results), 0)


class SponsorFilterCreatedDateTestCase(TestCase):
    def setUp(self):
        self.sponsor_1 = MvVolunteerFactory(
            created_date=timezone.make_aware(datetime(2025, 10, 1, 12, 0, 0)),
            is_principal=True,
        )

        self.sponsor_2 = MvVolunteerFactory(
            created_date=timezone.make_aware(datetime(2025, 10, 5, 12, 0, 0)),
            is_principal=True,
        )

        self.sponsor_3 = MvVolunteerFactory(
            created_date=None,
            is_principal=True,
        )

    def test_created_date_filter(self):
        filter_set = SponsorsFilter(
            queryset=MvVolunteer.objects.all(),
            data={
                "created_date_0": "2025-09-30",
                "created_date_1": "2025-10-02",
            },
        )

        results = filter_set.qs
        sponsor_ids = results.values_list("id", flat=True)

        self.assertEqual(len(results), 1)
        self.assertIn(self.sponsor_1.id, sponsor_ids)
        self.assertNotIn(self.sponsor_2.id, sponsor_ids)

    def test_created_date_filter_null(self):
        filter_set = SponsorsFilter(
            queryset=MvVolunteer.objects.all(),
            data={
                "created_date_0": "2025-09-29",
                "created_date_1": "2025-09-30",
            },
        )

        results = filter_set.qs
        self.assertEqual(len(results), 0)


class SponsorFilterIsEOITestCase(TestCase):
    def setUp(self):
        self.sponsor_1 = MvVolunteerFactory(is_eoi=True, is_principal=True)
        self.sponsor_2 = MvVolunteerFactory(is_eoi=False, is_principal=True)
        self.sponsor_3 = MvVolunteerFactory(is_eoi=None, is_principal=True)

    def test_filter_eoi_sponsors(self):
        filter_set = SponsorsFilter(
            queryset=MvVolunteer.objects.all(),
            data={"is_eoi": "Yes"},
        )

        results = filter_set.qs
        sponsor_ids = results.values_list("id", flat=True)

        self.assertIn(self.sponsor_1.id, sponsor_ids)
        self.assertNotIn(self.sponsor_2.id, sponsor_ids)
        self.assertNotIn(self.sponsor_3.id, sponsor_ids)


class SponsorFilterIncludeDuplicatesTestCase(TestCase):
    def setUp(self):
        self.sponsor_1 = MvVolunteerFactory(is_principal=True)
        self.sponsor_2 = MvVolunteerFactory(is_principal=False)
        self.sponsor_3 = MvVolunteerFactory(is_principal=None)

    def test_filter_eoi_sponsors(self):
        filter_set = SponsorsFilter(
            queryset=MvVolunteer.objects.all(),
            data={},
        )

        results = filter_set.qs
        sponsor_ids = results.values_list("id", flat=True)

        self.assertIn(self.sponsor_1.id, sponsor_ids)
        self.assertNotIn(self.sponsor_2.id, sponsor_ids)
        self.assertNotIn(self.sponsor_3.id, sponsor_ids)

        filter_set = SponsorsFilter(
            queryset=MvVolunteer.objects.all(),
            data={"include_duplicates": "Yes"},
        )

        results = filter_set.qs
        sponsor_ids = results.values_list("id", flat=True)

        self.assertIn(self.sponsor_1.id, sponsor_ids)
        self.assertIn(self.sponsor_2.id, sponsor_ids)
        self.assertIn(self.sponsor_3.id, sponsor_ids)
