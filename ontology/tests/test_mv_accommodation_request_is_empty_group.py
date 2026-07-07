from django.test import TestCase

from ontology.tests.factories import MvAccommodationRequestFactory


class MvAccommodationRequestIsEmptyGroup(TestCase):
    def test_ar_with_null_person_id_is_not_empty_group(self):
        accommodation_request = MvAccommodationRequestFactory(
            person_id=None,
            title="Alice Smith to 12 FAKE ROAD, AB12 3CD",
            number_of_people=1,
        )

        self.assertEqual(accommodation_request.is_empty_group, False)

    def test_ar_with_empty_person_id_list_is_empty_group(self):
        accommodation_request = MvAccommodationRequestFactory(
            person_id=[],
            title="Empty group to 12 FAKE ROAD, AB12 3CD",
            number_of_people=0,
        )

        self.assertEqual(accommodation_request.is_empty_group, True)

    def test_ar_with_person_id_is_not_empty_group(self):
        accommodation_request = MvAccommodationRequestFactory(
            person_id=["some-person-id"],
            title="Alice Smith to 12 FAKE ROAD, AB12 3CD",
            number_of_people=1,
        )

        self.assertEqual(accommodation_request.is_empty_group, False)

    def test_legacy_ar_with_empty_group_title_and_zero_people_is_empty_group(self):
        accommodation_request = MvAccommodationRequestFactory(
            title="Empty group to 45 FAKE STREET, XY9 8ZZ",
            number_of_people=0,
        )

        self.assertEqual(accommodation_request.is_empty_group, True)

    def test_legacy_ar_is_not_empty_group_because_number_of_people(self):
        accommodation_request = MvAccommodationRequestFactory(
            title="Empty group to 45 FAKE STREET, XY9 8ZZ",
            number_of_people=1,
        )

        self.assertEqual(accommodation_request.is_empty_group, False)

    def test_legacy_ar_is_not_empty_group_because_title(self):
        accommodation_request = MvAccommodationRequestFactory(
            title="Bob Jones to 45 FAKE LANE, XY9 8ZZ",
            number_of_people=0,
        )

        self.assertEqual(accommodation_request.is_empty_group, False)
