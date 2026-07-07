from django.test import TestCase

from accounts.enums import GroupType
from accounts.tests.factories import GroupInfoFactory
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    ReassignmentRequestFactory,
)


class LtlaUtlaGroupInfoTest(TestCase):
    def setUp(self):
        self.ltla_group = GroupInfoFactory(
            ltla_name="Test LTLA",
            gss_code="TESTLTLA",
            group_type=GroupType.LOCAL_AUTHORITY,
        )
        self.ltla_group_empty_string = GroupInfoFactory(
            ltla_name="", group_type=GroupType.LOCAL_AUTHORITY
        )
        self.ltla_group_none = GroupInfoFactory(
            ltla_name=None, group_type=GroupType.LOCAL_AUTHORITY
        )
        self.utla_group = GroupInfoFactory(
            utla_name="Test UTLA", group_type=GroupType.LOCAL_AUTHORITY
        )
        self.utla_group_empty_string = GroupInfoFactory(
            utla_name="", group_type=GroupType.LOCAL_AUTHORITY
        )
        self.utla_group_none = GroupInfoFactory(
            utla_name=None, group_type=GroupType.LOCAL_AUTHORITY
        )

    def test_ar_ltla_group_info_returns_matching_group(self):
        ar = MvAccommodationRequestFactory(ltla_name=["Test LTLA"])
        result = ar.ltla_group_info

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.ltla_group)

    def test_ar_ltla_group_info_returns_none_when_no_match(self):
        ar = MvAccommodationRequestFactory(ltla_name=["Nonexistent LTLA"])
        result = ar.ltla_group_info

        self.assertEqual(len(result), 0)

    def test_ar_utla_group_info_returns_matching_group(self):
        ar = MvAccommodationRequestFactory(utla_name=["Test UTLA"])
        result = ar.utla_group_info

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.utla_group)

    def test_ar_utla_group_info_returns_none_when_no_match(self):
        ar = MvAccommodationRequestFactory(utla_name=["Nonexistent UTLA"])
        result = ar.utla_group_info

        self.assertEqual(len(result), 0)

    def test_accommodation_ltla_group_info_returns_matching_group(self):
        accommodation = MvAccommodationFactory(ltla_name="Test LTLA")
        result = accommodation.ltla_group_info

        self.assertEqual(result, self.ltla_group)

    def test_accommodation_ltla_group_info_returns_none_when_no_match(self):
        accommodation = MvAccommodationFactory(ltla_name="Nonexistent LTLA")
        result = accommodation.ltla_group_info

        self.assertIsNone(result)

    def test_accommodation_utla_group_info_returns_matching_group(self):
        accommodation = MvAccommodationFactory(utla_name="Test UTLA")
        result = accommodation.utla_group_info

        self.assertEqual(result, self.utla_group)

    def test_accommodation_utla_group_info_returns_none_when_no_match(self):
        accommodation = MvAccommodationFactory(utla_name="Nonexistent UTLA")
        result = accommodation.utla_group_info

        self.assertIsNone(result)

    def test_reassignment_request_proposed_by_group_info_returns_matching_group(self):
        reassignment_request = ReassignmentRequestFactory(
            proposed_by_ltla_code="TESTLTLA"
        )
        result = reassignment_request.proposed_by_group_info

        self.assertEqual(result, self.ltla_group)

    def test_reassignment_request_proposed_by_group_info_returns_none_when_no_match(
        self,
    ):
        reassignment_request = ReassignmentRequestFactory(
            proposed_by_ltla_code="NONEXISTENT123"
        )
        result = reassignment_request.proposed_by_group_info

        self.assertIsNone(result)
