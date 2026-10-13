from ontology.models import MvAccommodationRequest
from ontology.tests.factories import MvAccommodationRequestFactory
from test_utils.base import BaseTestCase


class TestMvAccommodationRequestGetLocalAuthorityListTestCase(BaseTestCase):
    def setUp(self):
        self.test_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["test"],
            utla_name=["test_utla"],
        )

        self.bolton_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["bolton"],
            utla_name=["bolton_utla"],
        )

        self.test_bolton_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["test", "bolton"],
            utla_name=["test_utla", "bolton_utla"],
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

        self.assertEqual(ltla_names, sorted(["bolton", "test", "bristol"]))

    def test_should_return_utla_names(self):
        utla_names = list(MvAccommodationRequest.objects.all().utla_names())

        self.assertEqual(
            utla_names, sorted(["bolton_utla", "test_utla", "bristol_utla"])
        )
