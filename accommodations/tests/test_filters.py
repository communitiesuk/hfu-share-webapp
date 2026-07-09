from django.test import TestCase

from accommodations.views import AccommodationFilter
from ontology.models import MvAccommodation
from ontology.tests.factories import MvAccommodationFactory


class AccommodationFilterIncludeDuplicatesTestCase(TestCase):
    def setUp(self):
        self.records = [
            MvAccommodationFactory(
                is_principal=is_principal,
                ltla_name=ltla_name,
                utla_name=utla_name,
            )
            for is_principal, ltla_name, utla_name in (
                (
                    True,
                    "Southend-on-Sea",
                    "Essex",
                ),
                (
                    False,
                    "Ipswich",
                    "Suffolk",
                ),
                (
                    None,
                    "Norwich",
                    "Norfolk",
                ),
            )
        ]

    def test_filter_ltla(self):
        ltla_names_and_results = [
            ("Southend-on-Sea", (True, False, False)),
            ("Ipswich", (False, True, False)),
            ("Norwich", (False, False, True)),
        ]

        for ltla_name, expected_records in ltla_names_and_results:
            with self.subTest(ltla_name=ltla_name):
                filter_set = AccommodationFilter(
                    queryset=MvAccommodation.objects.all(),
                    data={"ltla_name": ltla_name, "include_duplicates": "Yes"},
                )

                results = filter_set.qs
                accommodation_ids = results.values_list("id", flat=True)

                for record, expected_record in zip(
                    self.records, expected_records, strict=False
                ):
                    if expected_record:
                        self.assertIn(record.id, accommodation_ids)
                    else:
                        self.assertNotIn(record.id, accommodation_ids)

    def test_filter_utla(self):
        utla_names_and_results = [
            ("Essex", (True, False, False)),
            ("Suffolk", (False, True, False)),
            ("Norfolk", (False, False, True)),
        ]

        for utla_name, expected_records in utla_names_and_results:
            with self.subTest(utla_name=utla_name):
                filter_set = AccommodationFilter(
                    queryset=MvAccommodation.objects.all(),
                    data={"utla_name": utla_name, "include_duplicates": "Yes"},
                )

                results = filter_set.qs
                accommodation_ids = results.values_list("id", flat=True)

                for record, expected_record in zip(
                    self.records, expected_records, strict=False
                ):
                    if expected_record:
                        self.assertIn(record.id, accommodation_ids)
                    else:
                        self.assertNotIn(record.id, accommodation_ids)

    def test_filter_duplicates(self):
        include_duplicates_and_results = [
            ("Yes", (True, True, True)),
            (None, (True, False, False)),
        ]

        for include_duplicates, expected_records in include_duplicates_and_results:
            with self.subTest(include_duplicates=include_duplicates):
                filter_set = AccommodationFilter(
                    queryset=MvAccommodation.objects.all(),
                    data={"include_duplicates": include_duplicates},
                )

                results = filter_set.qs
                accommodation_ids = results.values_list("id", flat=True)

                for record, expected_record in zip(
                    self.records, expected_records, strict=False
                ):
                    if expected_record:
                        self.assertIn(record.id, accommodation_ids)
                    else:
                        self.assertNotIn(record.id, accommodation_ids)
