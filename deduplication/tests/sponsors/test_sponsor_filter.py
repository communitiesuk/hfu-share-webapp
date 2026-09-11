from datetime import datetime

from django.utils import timezone

from deduplication.views import ManualSponsorDeduplicationFilter
from ontology.models import MvVolunteer as Sponsor
from ontology.tests.factories import MvVolunteerFactory as SponsorFactory
from test_utils.base import BaseTestCase


class SponsorFilterSexTestCase(BaseTestCase):
    def setUp(self):
        self.male_sponsor = SponsorFactory(sex="Male", is_principal=True)
        self.female_sponsor = SponsorFactory(sex="Female", is_principal=True)
        self.no_data_sex_sponsor = SponsorFactory(sex=None, is_principal=True)

    def test_filter_to_male_sponsors(self):
        filter_set = ManualSponsorDeduplicationFilter(
            queryset=Sponsor.objects.all(),
            data={"sex": ["Male"]},
        )

        results = filter_set.qs
        sponsor_ids = results.values_list("id", flat=True)

        self.assertIn(self.male_sponsor.id, sponsor_ids)
        self.assertNotIn(self.female_sponsor.id, sponsor_ids)
        self.assertNotIn(self.no_data_sex_sponsor.id, sponsor_ids)

    def test_filter_to_female_sponsors(self):
        filter_set = ManualSponsorDeduplicationFilter(
            queryset=Sponsor.objects.all(),
            data={"sex": ["Female"]},
        )

        results = filter_set.qs
        sponsor_ids = results.values_list("id", flat=True)

        self.assertNotIn(self.male_sponsor.id, sponsor_ids)
        self.assertIn(self.female_sponsor.id, sponsor_ids)
        self.assertNotIn(self.no_data_sex_sponsor.id, sponsor_ids)

    def test_filter_to_no_data_sponsors(self):
        filter_set = ManualSponsorDeduplicationFilter(
            queryset=Sponsor.objects.all(),
            data={"sex": ["null"]},
        )

        results = filter_set.qs
        sponsor_ids = results.values_list("id", flat=True)

        self.assertNotIn(self.male_sponsor.id, sponsor_ids)
        self.assertNotIn(self.female_sponsor.id, sponsor_ids)
        self.assertIn(self.no_data_sex_sponsor.id, sponsor_ids)


class SponsorFilterDateOfBirthTestCase(BaseTestCase):
    def setUp(self):
        self.sponsor_1 = SponsorFactory(
            date_of_birth="2025-10-01",
            is_principal=True,
        )

        self.sponsor_2 = SponsorFactory(
            date_of_birth="2025-10-05",
            is_principal=True,
        )

        self.sponsor_3 = SponsorFactory(
            date_of_birth=None,
            is_principal=True,
        )

    def test_date_of_birth_filter(self):
        filter_set = ManualSponsorDeduplicationFilter(
            queryset=Sponsor.objects.all(),
            data={
                "date_of_birth": "2025-09-30",
                "date_of_birth_1": "2025-10-02",
            },
        )

        results = filter_set.qs
        sponsor_ids = results.values_list("id", flat=True)

        self.assertEqual(len(results), 1)
        self.assertIn(self.sponsor_1.id, sponsor_ids)
        self.assertNotIn(self.sponsor_2.id, sponsor_ids)

    def test_date_of_birth_filter_null(self):
        filter_set = ManualSponsorDeduplicationFilter(
            queryset=Sponsor.objects.all(),
            data={
                "date_of_birth": "2025-09-29",
                "date_of_birth_1": "2025-09-30",
            },
        )

        results = filter_set.qs
        self.assertEqual(len(results), 0)

    def test_invalid_date_of_birth_range(self):
        filter_set = ManualSponsorDeduplicationFilter(
            queryset=Sponsor.objects.all(),
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


class SponsorFilterCreatedDateTestCase(BaseTestCase):
    def setUp(self):
        self.sponsor_1 = SponsorFactory(
            created_date=timezone.make_aware(datetime(2025, 10, 1, 12, 0, 0)),
            is_principal=True,
        )

        self.sponsor_2 = SponsorFactory(
            created_date=timezone.make_aware(datetime(2025, 10, 5, 12, 0, 0)),
            is_principal=True,
        )

        self.sponsor_3 = SponsorFactory(
            created_date=None,
            is_principal=True,
        )

    def test_created_date_filter(self):
        filter_set = ManualSponsorDeduplicationFilter(
            queryset=Sponsor.objects.all(),
            data={
                "created_date": "2025-09-30",
                "created_date_1": "2025-10-02",
            },
        )

        results = filter_set.qs
        sponsor_ids = results.values_list("id", flat=True)

        self.assertEqual(len(results), 1)
        self.assertIn(self.sponsor_1.id, sponsor_ids)
        self.assertNotIn(self.sponsor_2.id, sponsor_ids)

    def test_created_date_filter_null(self):
        filter_set = ManualSponsorDeduplicationFilter(
            queryset=Sponsor.objects.all(),
            data={
                "created_date": "2025-09-29",
                "created_date_1": "2025-09-30",
            },
        )

        results = filter_set.qs
        self.assertEqual(len(results), 0)

    def test_created_date_birth_range(self):
        filter_set = ManualSponsorDeduplicationFilter(
            queryset=Sponsor.objects.all(),
            data={
                "created_date": "2023-01-31",
                "created_date_1": "2023-01-01",
            },
        )

        self.assertFalse(filter_set.is_valid())
        self.assertIn(
            "created_date",
            filter_set.errors,
        )
        self.assertIn(
            "Date added from date must be before date to.",
            filter_set.errors["created_date"],
        )


class SponsorFilterIsEOITestCase(BaseTestCase):
    def setUp(self):
        self.sponsor_1 = SponsorFactory(is_eoi=True, is_principal=True)
        self.sponsor_2 = SponsorFactory(is_eoi=False, is_principal=True)
        self.sponsor_3 = SponsorFactory(is_eoi=None, is_principal=True)

    def test_filter_eoi_sponsors(self):
        filter_set = ManualSponsorDeduplicationFilter(
            queryset=Sponsor.objects.all(),
            data={"is_eoi": "Yes"},
        )

        results = filter_set.qs
        sponsor_ids = results.values_list("id", flat=True)

        self.assertIn(self.sponsor_1.id, sponsor_ids)
        self.assertNotIn(self.sponsor_2.id, sponsor_ids)
        self.assertNotIn(self.sponsor_3.id, sponsor_ids)
