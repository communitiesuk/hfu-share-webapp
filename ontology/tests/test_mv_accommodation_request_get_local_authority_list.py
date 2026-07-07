from django.test import TestCase

from ontology.models import MvAccommodationRequest
from ontology.tests.factories import MvAccommodationRequestFactory


class TestMvAccommodationRequestGetLocalAuthorityListTestCase(TestCase):
    def setUp(self):
        self.somerset_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["somerset"],
            utla_name=["somerset_utla"],
        )

        self.bolton_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["bolton"],
            utla_name=["bolton_utla"],
        )

        self.somerset_bolton_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["somerset", "bolton"],
            utla_name=["somerset_utla", "bolton_utla"],
        )

        self.bristol_accommodation_request_missing_utla = MvAccommodationRequestFactory(
            ltla_name=["bristol"],
            utla_name=[],
        )

        self.bristol_accommodation_request_missing_ltla = MvAccommodationRequestFactory(
            ltla_name=None,
            utla_name=["bristol_utla"],
        )

    def test_should_return_ltla_names(self):
        ltla_names = list(MvAccommodationRequest.objects.all().ltla_names())

        self.assertEqual(ltla_names, sorted(["bolton", "somerset", "bristol"]))

    def test_should_return_utla_names(self):
        utla_names = list(MvAccommodationRequest.objects.all().utla_names())

        self.assertEqual(
            utla_names, sorted(["bolton_utla", "somerset_utla", "bristol_utla"])
        )
