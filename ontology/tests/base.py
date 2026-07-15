from unittest.mock import MagicMock

from django.contrib.auth.models import Group
from django.db.models import QuerySet
from django.test import TestCase

from accounts.enums import GroupType
from accounts.tests.factories import GroupFactory, UserFactory
from ontology.mixins import DaViewerGroupNames
from ontology.models import MvAccommodation, MvVolunteer
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvUkPostcodeFactory,
    MvVolunteerFactory,
    PersonMasterRecordFactory,
    SponsorshipCertificationFormFactory,
    VisaApplicationFactory,
)


def create_mock_queryset(result: list) -> QuerySet:
    mock_queryset = MagicMock(spec=QuerySet)
    mock_queryset.all.return_value = result
    mock_queryset.order_by.return_value = result
    mock_queryset.union = MagicMock(
        spec=QuerySet, side_effect=lambda qs: create_mock_queryset(qs.all() + result)
    )

    return mock_queryset


class LocalAuthorityBaseTestCaseMixin(TestCase):
    def setUp(self):
        super().setUp()
        # ltla names
        self.ltla_one_a_name = "test_ltla_one_a"
        self.ltla_one_b_name = "test_ltla_one_b"
        self.ltla_two_a_name = "test_ltla_two_a"
        self.ltla_two_b_name = "test_ltla_two_b"
        self.ltla_other_da_name = "test_ltla_other_da"

        # utla names
        self.utla_one_name = "test_utla_one"
        self.utla_two_name = "test_utla_two"
        self.utla_other_da_name = "test_utla_other_da"

        # da names
        self.da_main_name = "test_da_main"
        self.da_other_name = "test_da_other"

        # groups
        self.da_main_group = GroupFactory(
            groupinfo__da_name=self.da_main_name,
            groupinfo__is_da=True,
            groupinfo__group_type=GroupType.DEVOLVED_ADMINISTRATION,
        )
        self.da_other_group = GroupFactory(
            groupinfo__da_name=self.da_other_name,
            groupinfo__is_da=True,
            groupinfo__group_type=GroupType.DEVOLVED_ADMINISTRATION,
        )

        self.utla_one_group = GroupFactory(
            groupinfo__utla_name=self.utla_one_name,
            groupinfo__is_utla=True,
            groupinfo__parent_da=self.da_main_group.groupinfo,
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY,
        )

        self.ltla_one_a_no_utla_group = GroupFactory(
            groupinfo__ltla_name=self.ltla_one_a_name,
            groupinfo__parent_da=self.da_main_group.groupinfo,
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY,
        )

        self.utla_two_group = GroupFactory(
            groupinfo__utla_name=self.utla_two_name,
            groupinfo__is_utla=True,
            groupinfo__parent_da=self.da_main_group.groupinfo,
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY,
        )
        self.utla_other_da_group = GroupFactory(
            groupinfo__utla_name=self.utla_other_da_name,
            groupinfo__is_utla=True,
            groupinfo__parent_da=self.da_other_group.groupinfo,
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY,
        )

        self.ltla_one_a_group = GroupFactory(
            groupinfo__ltla_name=self.ltla_one_a_name,
            groupinfo__utla_name=self.utla_one_name,
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY,
            groupinfo__parent_da=self.da_main_group.groupinfo,
            groupinfo__parent_utla=self.utla_one_group.groupinfo,
        )
        self.ltla_one_b_group = GroupFactory(
            groupinfo__ltla_name=self.ltla_one_b_name,
            groupinfo__utla_name=self.utla_one_name,
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY,
            groupinfo__parent_da=self.da_main_group.groupinfo,
            groupinfo__parent_utla=self.utla_one_group.groupinfo,
        )
        self.ltla_two_a_group = GroupFactory(
            groupinfo__ltla_name=self.ltla_two_a_name,
            groupinfo__utla_name=self.utla_two_name,
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY,
            groupinfo__parent_da=self.da_main_group.groupinfo,
            groupinfo__parent_utla=self.utla_two_group.groupinfo,
        )
        self.ltla_two_b_group = GroupFactory(
            groupinfo__ltla_name=self.ltla_two_b_name,
            groupinfo__utla_name=self.utla_two_name,
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY,
            groupinfo__parent_da=self.da_main_group.groupinfo,
            groupinfo__parent_utla=self.utla_two_group.groupinfo,
        )
        self.ltla_other_da_group = GroupFactory(
            groupinfo__ltla_name=self.ltla_other_da_name,
            groupinfo__utla_name=self.utla_other_da_name,
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY,
            groupinfo__parent_da=self.da_other_group.groupinfo,
        )

        self.da_england_group = Group.objects.get(name="da_england")
        self.da_wales_group = Group.objects.get(name="da_wales")
        self.da_scotland_group = Group.objects.get(name="da_scotland")
        self.da_northern_ireland_group = Group.objects.get(name="da_northern_ireland")

        # type: ignore[attr-defined]
        self.da_england_ltla_groups = self.da_england_group.groupinfo.da_parent_of.all()

        # dev user
        self.ltla_user_dev = UserFactory(
            username="is_dev", email="dev@example.com", is_dev=True
        )

        # ltla users
        self.ltla_one_a_user = UserFactory(
            username="ltla_one_a_user", email="ltla_one_a_user@example.com"
        )
        self.ltla_one_a_user.groups.set([self.ltla_one_a_group])
        self.ltla_one_b_user = UserFactory(
            username="ltla_one_b_user", email="ltla_one_b_user@example.com"
        )
        self.ltla_one_b_user.groups.set([self.ltla_one_b_group])

        self.ltla_two_a_user = UserFactory(
            username="ltla_two_a_user", email="ltla_two_a_user@example.com"
        )
        self.ltla_two_a_user.groups.set([self.ltla_two_a_group])

        self.ltla_two_b_user = UserFactory(
            username="ltla_two_b_user", email="ltla_two_b_user@example.com"
        )
        self.ltla_two_b_user.groups.set([self.ltla_two_b_group])

        self.ltla_one_a_ltla_one_b_user = UserFactory(
            username="multi_ltla_user", email="multi_ltla_user@example.com"
        )
        self.ltla_one_a_ltla_one_b_user.groups.set(
            [self.ltla_one_a_group, self.ltla_one_b_group]
        )

        self.ltla_no_group_user = UserFactory(
            username="ltla_no_group_user", email="ltla_no_group_user@example.com"
        )

        # utla users
        self.utla_one_user = UserFactory(
            username="utla_user_one", email="utla_user_one@example.com"
        )
        self.utla_one_user.groups.set([self.utla_one_group])

        self.utla_two_user = UserFactory(
            username="utla_user_two", email="utla_user_two@example.com"
        )
        self.utla_two_user.groups.set([self.utla_two_group])

        self.multi_utla_user = UserFactory(
            username="multi_utla_user", email="multi_utla_user@example.com"
        )
        self.multi_utla_user.groups.set([self.utla_one_group, self.utla_two_group])

        # da users
        self.da_main_user = UserFactory(
            username="da_user_main", email="da_user_main@example.com"
        )
        self.da_main_user.groups.set([self.da_main_group])

        self.da_other_user = UserFactory(
            username="da_user_other", email="da_user_other@example.com"
        )
        self.da_other_user.groups.set([self.da_other_group])

        self.multi_da_user = UserFactory(
            username="multi_da_user", email="multi_da_user@example.com"
        )
        self.multi_da_user.groups.set([self.da_main_group, self.da_other_group])

        self.da_england_user = UserFactory(
            username="da_england_user", email="da_england_user@example.com"
        )
        self.da_england_user.groups.set([self.da_england_group])

        self.da_wales_user = UserFactory(
            username="da_wales_user", email="da_wales_user@example.com"
        )
        self.da_wales_user.groups.set([self.da_wales_group])

        self.da_scotland_user = UserFactory(
            username="da_scotland_user", email="da_scotland_user@example.com"
        )
        self.da_scotland_user.groups.set([self.da_scotland_group])

        self.da_northern_ireland_user = UserFactory(
            username="da_northern_ireland_user",
            email="da_northern_ireland_user@example.com",
        )
        self.da_northern_ireland_user.groups.set([self.da_northern_ireland_group])


class VisaApplicationBaseTestCase(LocalAuthorityBaseTestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()

        # applications
        self.ltla_one_a_visa_application = VisaApplicationFactory(
            ltla_name=self.ltla_one_a_name,
            utla_name=self.utla_one_name,
        )
        self.ltla_two_a_visa_application = VisaApplicationFactory(
            ltla_name=self.ltla_two_a_name,
            utla_name=self.utla_two_name,
        )
        self.ltla_other_da_visa_application = VisaApplicationFactory(
            ltla_name=self.ltla_other_da_name,
            utla_name=self.utla_other_da_name,
        )
        self.da_england_visa_application = VisaApplicationFactory(
            ltla_name="", utla_name="", viewer_group_names=[DaViewerGroupNames.ENGLAND]
        )

        self.all_visa_applications = [
            self.ltla_one_a_visa_application,
            self.ltla_two_a_visa_application,
            self.ltla_other_da_visa_application,
            self.da_england_visa_application,
        ]
        self.ltla_one_a_visa_applications = [
            self.ltla_one_a_visa_application,
        ]
        self.ltla_two_a_visa_applications = [
            self.ltla_two_a_visa_application,
        ]
        self.utla_one_visa_applications = [
            self.ltla_one_a_visa_application,
        ]
        self.utla_two_visa_applications = [
            self.ltla_two_a_visa_application,
        ]
        self.da_main_visa_applications = [
            self.ltla_one_a_visa_application,
            self.ltla_two_a_visa_application,
        ]
        self.da_other_visa_applications = [
            self.ltla_other_da_visa_application,
        ]
        self.da_england_visa_applications = [
            self.da_england_visa_application,
        ]


class MvPersonBaseTestCase(LocalAuthorityBaseTestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.ltla_one_a_person = MvPersonFactory(
            accommodation_request__ltla_name=[self.ltla_one_a_name],
            accommodation_request__utla_name=[self.utla_one_name],
        )
        self.ltla_one_b_person = MvPersonFactory(
            accommodation_request__ltla_name=[self.ltla_one_b_name],
            accommodation_request__utla_name=[self.utla_one_name],
        )
        self.ltla_two_a_person = MvPersonFactory(
            accommodation_request__ltla_name=[self.ltla_two_a_name],
            accommodation_request__utla_name=[self.utla_two_name],
        )
        self.ltla_two_b_person = MvPersonFactory(
            accommodation_request__ltla_name=[self.ltla_two_b_name],
            accommodation_request__utla_name=[self.utla_two_name],
        )
        self.ltla_one_a_but_missing_utla_person = MvPersonFactory(
            accommodation_request__ltla_name=[self.ltla_one_a_name],
            accommodation_request__utla_name=[],
        )
        self.utla_one_but_missing_ltla_person = MvPersonFactory(
            accommodation_request__ltla_name=[],
            accommodation_request__utla_name=[self.utla_one_name],
        )
        self.ltla_da_other_person = MvPersonFactory(
            accommodation_request__ltla_name=[self.ltla_other_da_name],
            accommodation_request__utla_name=[self.utla_other_da_name],
        )
        self.ltla_da_other_but_missing_utla_person = MvPersonFactory(
            accommodation_request__ltla_name=[self.ltla_other_da_name],
            accommodation_request__utla_name=[],
        )
        self.utla_da_other_but_missing_ltla_person = MvPersonFactory(
            accommodation_request__ltla_name=[],
            accommodation_request__utla_name=[self.utla_other_da_name],
        )
        self.ltla_one_a_ltla_two_a_multi_la_person = MvPersonFactory(
            accommodation_request__ltla_name=[
                self.ltla_one_a_name,
                self.ltla_two_a_name,
            ],
            accommodation_request__utla_name=[self.utla_one_name, self.utla_two_name],
        )
        self.ltla_one_a_ltla_one_b_multi_la_person = MvPersonFactory(
            accommodation_request__ltla_name=[
                self.ltla_one_a_name,
                self.ltla_one_b_name,
            ],
            accommodation_request__utla_name=[self.utla_one_name],
        )
        self.da_england_person = MvPersonFactory(
            accommodation_request__ltla_name=[],
            accommodation_request__utla_name=[],
            viewer_group_names=[DaViewerGroupNames.ENGLAND],
        )

        self.all_persons = [
            self.ltla_one_a_person,
            self.ltla_two_a_person,
            self.ltla_one_b_person,
            self.ltla_two_b_person,
            self.ltla_one_a_but_missing_utla_person,
            self.utla_one_but_missing_ltla_person,
            self.ltla_da_other_person,
            self.ltla_da_other_but_missing_utla_person,
            self.utla_da_other_but_missing_ltla_person,
            self.ltla_one_a_ltla_two_a_multi_la_person,
            self.ltla_one_a_ltla_one_b_multi_la_person,
            self.da_england_person,
        ]
        self.ltla_one_a_persons = [
            self.ltla_one_a_person,
            self.ltla_one_a_but_missing_utla_person,
            self.ltla_one_a_ltla_two_a_multi_la_person,
            self.ltla_one_a_ltla_one_b_multi_la_person,
        ]
        self.ltla_two_a_persons = [
            self.ltla_two_a_person,
            self.ltla_one_a_ltla_two_a_multi_la_person,
        ]
        self.utla_one_persons = [
            self.ltla_one_a_person,
            self.ltla_one_b_person,
            self.utla_one_but_missing_ltla_person,
            self.ltla_one_a_but_missing_utla_person,
            self.ltla_one_a_ltla_two_a_multi_la_person,
            self.ltla_one_a_ltla_one_b_multi_la_person,
        ]
        self.utla_two_persons = [
            self.ltla_two_a_person,
            self.ltla_two_b_person,
            self.ltla_one_a_ltla_two_a_multi_la_person,
        ]
        self.da_main_persons = [
            self.ltla_one_a_person,
            self.ltla_two_a_person,
            self.ltla_one_b_person,
            self.ltla_two_b_person,
            self.ltla_one_a_but_missing_utla_person,
            self.utla_one_but_missing_ltla_person,
            self.ltla_one_a_ltla_two_a_multi_la_person,
            self.ltla_one_a_ltla_one_b_multi_la_person,
        ]
        self.da_other_persons = [
            self.ltla_da_other_person,
            self.ltla_da_other_but_missing_utla_person,
            self.utla_da_other_but_missing_ltla_person,
        ]
        self.da_england_persons = [
            self.da_england_person,
        ]


class MvAccommodationRequestTestCase(LocalAuthorityBaseTestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.ltla_one_a_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )
        self.ltla_one_b_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=[self.ltla_one_b_name],
            utla_name=[self.utla_one_name],
        )
        self.ltla_two_a_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=[self.ltla_two_a_name],
            utla_name=[self.utla_two_name],
        )
        self.ltla_two_b_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=[self.ltla_two_b_name],
            utla_name=[self.utla_two_name],
        )
        self.ltla_one_a_but_missing_utla_accommodation_request = (
            MvAccommodationRequestFactory(
                ltla_name=[self.ltla_one_a_name],
                utla_name=[],
            )
        )
        self.utla_one_but_missing_ltla_accommodation_request = (
            MvAccommodationRequestFactory(
                ltla_name=[],
                utla_name=[self.utla_one_name],
            )
        )
        self.ltla_other_da_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=[self.ltla_other_da_name],
            utla_name=[self.utla_other_da_name],
        )
        self.ltla_other_da_but_missing_utla_accommodation_request = (
            MvAccommodationRequestFactory(
                ltla_name=[self.ltla_other_da_name],
                utla_name=[],
            )
        )
        self.utla_other_da_but_missing_ltla_accommodation_request = (
            MvAccommodationRequestFactory(
                ltla_name=[],
                utla_name=[self.utla_other_da_name],
            )
        )
        self.ltla_one_a_ltla_one_b_multi_la_accommodation_request = (
            MvAccommodationRequestFactory(
                ltla_name=[self.ltla_one_a_name, self.ltla_one_b_name],
                utla_name=[self.utla_one_name],
            )
        )
        self.ltla_one_a_ltla_two_a_multi_la_accommodation_request = (
            MvAccommodationRequestFactory(
                ltla_name=[self.ltla_one_a_name, self.ltla_two_a_name],
                utla_name=[self.utla_one_name, self.utla_two_name],
            )
        )
        self.da_england_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=[""],
            utla_name=[""],
            viewer_group_names=[DaViewerGroupNames.ENGLAND],
        )

        self.all_accommodation_requests = [
            self.ltla_one_a_accommodation_request,
            self.ltla_one_b_accommodation_request,
            self.ltla_two_a_accommodation_request,
            self.ltla_two_b_accommodation_request,
            self.ltla_one_a_but_missing_utla_accommodation_request,
            self.utla_one_but_missing_ltla_accommodation_request,
            self.ltla_other_da_accommodation_request,
            self.ltla_other_da_but_missing_utla_accommodation_request,
            self.utla_other_da_but_missing_ltla_accommodation_request,
            self.ltla_one_a_ltla_two_a_multi_la_accommodation_request,
            self.ltla_one_a_ltla_one_b_multi_la_accommodation_request,
            self.da_england_accommodation_request,
        ]
        self.ltla_one_a_accommodation_requests = [
            self.ltla_one_a_accommodation_request,
            self.ltla_one_a_but_missing_utla_accommodation_request,
            self.ltla_one_a_ltla_two_a_multi_la_accommodation_request,
            self.ltla_one_a_ltla_one_b_multi_la_accommodation_request,
        ]
        self.ltla_two_a_accommodation_requests = [
            self.ltla_two_a_accommodation_request,
            self.ltla_one_a_ltla_two_a_multi_la_accommodation_request,
            self.ltla_one_a_ltla_one_b_multi_la_accommodation_request,
        ]
        self.utla_one_accommodation_requests = [
            self.ltla_one_a_accommodation_request,
            self.ltla_one_b_accommodation_request,
            self.utla_one_but_missing_ltla_accommodation_request,
            self.ltla_one_a_but_missing_utla_accommodation_request,
            self.ltla_one_a_ltla_two_a_multi_la_accommodation_request,
            self.ltla_one_a_ltla_one_b_multi_la_accommodation_request,
        ]
        self.utla_two_accommodation_requests = [
            self.ltla_two_a_accommodation_request,
            self.ltla_two_b_accommodation_request,
            self.ltla_one_a_ltla_two_a_multi_la_accommodation_request,
        ]
        self.da_main_accommodation_requests = [
            self.ltla_one_a_accommodation_request,
            self.ltla_one_b_accommodation_request,
            self.ltla_two_a_accommodation_request,
            self.ltla_two_b_accommodation_request,
            self.ltla_one_a_but_missing_utla_accommodation_request,
            self.utla_one_but_missing_ltla_accommodation_request,
            self.ltla_one_a_ltla_two_a_multi_la_accommodation_request,
            self.ltla_one_a_ltla_one_b_multi_la_accommodation_request,
        ]
        self.da_other_accommodation_requests = [
            self.ltla_other_da_accommodation_request,
            self.ltla_other_da_but_missing_utla_accommodation_request,
            self.utla_other_da_but_missing_ltla_accommodation_request,
        ]
        self.da_england_accommodation_requests = [
            self.da_england_accommodation_request,
        ]


class MvAccommodationTestCase(LocalAuthorityBaseTestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.ltla_one_a_accommodation = MvAccommodationFactory(
            ltla_name=self.ltla_one_a_name,
            utla_name=self.utla_one_name,
        )
        self.ltla_one_b_accommodation = MvAccommodationFactory(
            ltla_name=self.ltla_one_b_name,
            utla_name=self.utla_one_name,
        )
        self.ltla_two_a_accommodation = MvAccommodationFactory(
            ltla_name=self.ltla_two_a_name,
            utla_name=self.utla_two_name,
        )
        self.ltla_two_b_accommodation = MvAccommodationFactory(
            ltla_name=self.ltla_two_b_name,
            utla_name=self.utla_two_name,
        )
        self.ltla_other_da_accommodation = MvAccommodationFactory(
            ltla_name=self.ltla_other_da_name,
            utla_name=self.utla_other_da_name,
        )
        self.ltla_one_a_but_missing_utla_accommodation = MvAccommodationFactory(
            ltla_name=self.ltla_one_a_name,
            utla_name="",
        )

        self.utla_one_missing_ltla_accommodation = MvAccommodationFactory(
            ltla_name="",
            utla_name=self.utla_one_name,
        )
        self.utla_other_da_missing_ltla_accommodation = MvAccommodationFactory(
            ltla_name="",
            utla_name=self.utla_other_da_name,
        )
        self.ltla_other_da_missing_utla_accommodation = MvAccommodationFactory(
            ltla_name="",
            utla_name=self.utla_other_da_name,
        )

        self.da_england_accommodation = MvAccommodationFactory(
            ltla_name="", utla_name="", viewer_group_names=[DaViewerGroupNames.ENGLAND]
        )

        self.all_accommodations = [
            self.ltla_one_a_accommodation,
            self.ltla_one_a_but_missing_utla_accommodation,
            self.ltla_one_b_accommodation,
            self.ltla_two_a_accommodation,
            self.ltla_two_b_accommodation,
            self.ltla_other_da_accommodation,
            self.utla_one_missing_ltla_accommodation,
            self.ltla_other_da_missing_utla_accommodation,
            self.utla_other_da_missing_ltla_accommodation,
            self.da_england_accommodation,
        ]
        self.ltla_one_a_accommodations = [
            self.ltla_one_a_accommodation,
            self.ltla_one_a_but_missing_utla_accommodation,
        ]
        self.ltla_two_a_accommodations = [
            self.ltla_two_a_accommodation,
        ]
        self.utla_one_accommodations = [
            self.ltla_one_a_accommodation,
            self.ltla_one_b_accommodation,
            self.ltla_one_a_but_missing_utla_accommodation,
            self.utla_one_missing_ltla_accommodation,
        ]
        self.utla_two_accommodations = [
            self.ltla_two_a_accommodation,
            self.ltla_two_b_accommodation,
        ]
        self.utla_other_da_accommodations = [
            self.ltla_other_da_accommodation,
            self.utla_other_da_missing_ltla_accommodation,
        ]
        self.da_main_accommodations = [
            self.ltla_one_a_accommodation,
            self.ltla_one_b_accommodation,
            self.ltla_two_a_accommodation,
            self.ltla_two_b_accommodation,
            self.ltla_one_a_but_missing_utla_accommodation,
            self.utla_one_missing_ltla_accommodation,
        ]
        self.da_other_accommodations = [
            self.ltla_other_da_accommodation,
            self.utla_other_da_missing_ltla_accommodation,
            self.ltla_other_da_missing_utla_accommodation,
        ]
        self.da_england_accommodations = [
            self.da_england_accommodation,
        ] + list(
            MvAccommodation.objects.filter(
                ltla_name__in=self.da_england_ltla_groups.values_list(
                    "ltla_name", flat=True
                ).distinct()
            )
        )


class PersonMasterRecordBaseTestCase(LocalAuthorityBaseTestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.ltla_one_a_person_one = MvPersonFactory(
            accommodation_request__ltla_name=[self.ltla_one_a_name],
            accommodation_request__utla_name=[self.utla_one_name],
        )
        self.ltla_one_a_person_two = MvPersonFactory(
            accommodation_request__ltla_name=[self.ltla_one_a_name],
            accommodation_request__utla_name=[self.utla_one_name],
        )
        self.ltla_one_b_person_one = MvPersonFactory(
            accommodation_request__ltla_name=[self.ltla_one_b_name],
            accommodation_request__utla_name=[self.utla_one_name],
        )
        self.ltla_one_b_person_two = MvPersonFactory(
            accommodation_request__ltla_name=[self.ltla_one_b_name],
            accommodation_request__utla_name=[self.utla_one_name],
        )
        self.ltla_two_a_person_one = MvPersonFactory(
            accommodation_request__ltla_name=[self.ltla_two_a_name],
            accommodation_request__utla_name=[self.utla_two_name],
        )
        self.ltla_two_a_person_two = MvPersonFactory(
            accommodation_request__ltla_name=[self.ltla_two_a_name],
            accommodation_request__utla_name=[self.utla_two_name],
        )

        self.ltla_one_a_person_master_record = PersonMasterRecordFactory()
        self.ltla_one_a_person_master_record.persons.set(
            [
                self.ltla_one_a_person_one,
                self.ltla_one_a_person_one,
            ]
        )
        self.ltla_one_b_person_master_record = PersonMasterRecordFactory()
        self.ltla_one_b_person_master_record.persons.set(
            [
                self.ltla_one_b_person_one,
                self.ltla_one_b_person_two,
            ]
        )

        self.mixed_ltla_one_a_ltla_one_b_person_master_record = (
            PersonMasterRecordFactory()
        )
        self.mixed_ltla_one_a_ltla_one_b_person_master_record.persons.set(
            [
                self.ltla_one_a_person_one,
                self.ltla_one_b_person_one,
            ]
        )

        self.ltla_two_a_person_master_record = PersonMasterRecordFactory()
        self.ltla_two_a_person_master_record.persons.set(
            [
                self.ltla_two_a_person_one,
                self.ltla_two_a_person_two,
            ]
        )

        self.all_person_master_records = [
            self.ltla_one_a_person_master_record,
            self.ltla_one_b_person_master_record,
            self.mixed_ltla_one_a_ltla_one_b_person_master_record,
            self.ltla_two_a_person_master_record,
        ]
        self.ltla_one_a_person_master_records = [self.ltla_one_a_person_master_record]
        self.ltla_one_b_person_master_records = [self.ltla_one_b_person_master_record]
        self.ltla_two_a_person_master_records = [self.ltla_two_a_person_master_record]
        self.mixed_ltla_one_a_ltla_one_b_person_master_records = [
            self.mixed_ltla_one_a_ltla_one_b_person_master_record
        ]
        self.utla_one_person_master_records = (
            self.ltla_one_a_person_master_records
            + self.ltla_one_b_person_master_records
            + self.mixed_ltla_one_a_ltla_one_b_person_master_records
        )

        self.utla_two_person_master_records = [self.ltla_two_a_person_master_record]


class LocalAuthorityPermissionsManagerBaseTestCase(
    LocalAuthorityBaseTestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()

        self.ltla_one_a_object = VisaApplicationFactory(
            ltla_name=self.ltla_one_a_name, utla_name=self.utla_one_name
        )
        self.ltla_two_a_object = VisaApplicationFactory(
            ltla_name=self.ltla_two_a_name, utla_name=self.utla_two_name
        )
        self.ltla_one_b_object = VisaApplicationFactory(
            ltla_name=self.ltla_one_b_name, utla_name=self.utla_one_name
        )
        self.ltla_two_b_object = VisaApplicationFactory(
            ltla_name=self.ltla_two_b_name, utla_name=self.utla_two_name
        )
        self.ltla_one_a_but_missing_utla_object = VisaApplicationFactory(
            ltla_name=self.ltla_one_a_name, utla_name=""
        )
        self.utla_one_but_missing_ltla_object = VisaApplicationFactory(
            ltla_name="", utla_name=self.utla_one_name
        )

        self.ltla_other_da_object = VisaApplicationFactory(
            ltla_name=self.ltla_other_da_name, utla_name=self.utla_other_da_name
        )
        self.ltla_other_da_but_missing_utla_object = VisaApplicationFactory(
            ltla_name=self.ltla_other_da_name, utla_name=""
        )
        self.utla_other_da_but_missing_ltla_object = VisaApplicationFactory(
            ltla_name="", utla_name=self.utla_other_da_name
        )

        self.da_england_object_missing_ltla_missing_utla = VisaApplicationFactory(
            ltla_name="", utla_name="", viewer_group_names=[DaViewerGroupNames.ENGLAND]
        )
        self.da_scotland_object_missing_ltla_missing_utla = VisaApplicationFactory(
            ltla_name="", utla_name="", viewer_group_names=[DaViewerGroupNames.SCOTLAND]
        )
        self.da_wales_object_missing_ltla_missing_utla = VisaApplicationFactory(
            ltla_name="", utla_name="", viewer_group_names=[DaViewerGroupNames.WALES]
        )
        self.da_northern_ireland_object_missing_ltla_missing_utla = (
            VisaApplicationFactory(
                ltla_name="",
                utla_name="",
                viewer_group_names=[DaViewerGroupNames.NORTHERN_IRELAND],
            )
        )

        self.all_objects = [
            self.ltla_one_a_object,
            self.ltla_two_a_object,
            self.ltla_one_b_object,
            self.ltla_two_b_object,
            self.ltla_one_a_but_missing_utla_object,
            self.utla_one_but_missing_ltla_object,
            self.ltla_other_da_object,
            self.ltla_other_da_but_missing_utla_object,
            self.utla_other_da_but_missing_ltla_object,
        ]
        self.ltla_one_a_objects = [
            self.ltla_one_a_object,
            self.ltla_one_a_but_missing_utla_object,
        ]
        self.ltla_one_b_objects = [
            self.ltla_one_b_object,
        ]
        self.ltla_two_a_objects = [
            self.ltla_two_a_object,
        ]
        self.ltla_other_da_objects = [
            self.ltla_other_da_object,
            self.ltla_other_da_but_missing_utla_object,
        ]
        self.utla_one_objects = [
            self.ltla_one_a_object,
            self.ltla_one_b_object,
            self.utla_one_but_missing_ltla_object,
            self.ltla_one_a_but_missing_utla_object,
        ]
        self.utla_two_objects = [
            self.ltla_two_a_object,
            self.ltla_two_b_object,
        ]
        self.utla_other_da_objects = [
            self.ltla_other_da_object,
            self.utla_other_da_but_missing_ltla_object,
        ]
        self.da_main_objects = [
            self.ltla_one_a_object,
            self.ltla_two_a_object,
            self.ltla_one_b_object,
            self.ltla_two_b_object,
            self.ltla_one_a_but_missing_utla_object,
            self.utla_one_but_missing_ltla_object,
        ]
        self.da_other_objects = [
            self.ltla_other_da_object,
            self.ltla_other_da_but_missing_utla_object,
            self.utla_other_da_but_missing_ltla_object,
        ]

        self.da_england_objects = [self.da_england_object_missing_ltla_missing_utla]
        self.da_wales_objects = [self.da_wales_object_missing_ltla_missing_utla]
        self.da_scotland_objects = [self.da_scotland_object_missing_ltla_missing_utla]
        self.da_northern_ireland_objects = [
            self.da_northern_ireland_object_missing_ltla_missing_utla
        ]

        self.all_objects = [
            self.ltla_one_a_object,
            self.ltla_two_a_object,
            self.ltla_one_b_object,
            self.ltla_two_b_object,
            self.ltla_one_a_but_missing_utla_object,
            self.utla_one_but_missing_ltla_object,
            self.ltla_other_da_object,
            self.ltla_other_da_but_missing_utla_object,
            self.utla_other_da_but_missing_ltla_object,
            self.da_england_object_missing_ltla_missing_utla,
            self.da_wales_object_missing_ltla_missing_utla,
            self.da_scotland_object_missing_ltla_missing_utla,
            self.da_northern_ireland_object_missing_ltla_missing_utla,
        ]


class MvVolunteerBaseTestCase(MvAccommodationTestCase):
    def setUp(self):
        super().setUp()

        self.ltla_one_a_volunteer = MvVolunteerFactory()
        self.ltla_one_b_volunteer = MvVolunteerFactory()
        self.ltla_two_a_volunteer = MvVolunteerFactory()
        self.ltla_two_b_volunteer = MvVolunteerFactory()
        self.ltla_one_a_but_missing_utla_volunteer = MvVolunteerFactory()
        self.utla_one_but_missing_ltla_volunteer = MvVolunteerFactory()
        self.ltla_da_other_volunteer = MvVolunteerFactory()
        self.ltla_da_other_but_missing_utla_volunteer = MvVolunteerFactory()
        self.utla_da_other_but_missing_ltla_volunteer = MvVolunteerFactory()
        self.ltla_one_a_ltla_two_a_multi_la_volunteer = MvVolunteerFactory()
        self.ltla_one_a_ltla_one_b_multi_la_volunteer = MvVolunteerFactory()
        self.da_england_volunteer = MvVolunteerFactory(
            first_name="da_england",
            last_name="volunteer",
            viewer_group_names=[DaViewerGroupNames.ENGLAND],
        )

        self.ltla_one_a_accommodation.hosts.set(
            [
                self.ltla_one_a_volunteer,
                self.ltla_one_a_ltla_two_a_multi_la_volunteer,
                self.ltla_one_a_ltla_one_b_multi_la_volunteer,
            ]
        )
        self.ltla_one_b_accommodation.hosts.set(
            [self.ltla_one_b_volunteer, self.ltla_one_a_ltla_one_b_multi_la_volunteer]
        )
        self.ltla_two_a_accommodation.hosts.set(
            [self.ltla_two_a_volunteer, self.ltla_one_a_ltla_two_a_multi_la_volunteer]
        )
        self.ltla_two_b_accommodation.hosts.set([self.ltla_two_b_volunteer])
        self.ltla_one_a_but_missing_utla_accommodation.hosts.set(
            [self.ltla_one_a_but_missing_utla_volunteer]
        )
        self.utla_one_missing_ltla_accommodation.hosts.set(
            [self.utla_one_but_missing_ltla_volunteer]
        )
        self.ltla_other_da_accommodation.hosts.set([self.ltla_da_other_volunteer])
        self.ltla_other_da_missing_utla_accommodation.hosts.set(
            [self.ltla_da_other_but_missing_utla_volunteer]
        )
        self.utla_other_da_missing_ltla_accommodation.hosts.set(
            [self.utla_da_other_but_missing_ltla_volunteer]
        )
        self.da_england_accommodation.hosts.set([self.da_england_volunteer])

        self.ltla_one_a_volunteers = [
            self.ltla_one_a_volunteer,
            self.ltla_one_a_but_missing_utla_volunteer,
            self.ltla_one_a_ltla_one_b_multi_la_volunteer,
            self.ltla_one_a_ltla_two_a_multi_la_volunteer,
        ]
        self.ltla_two_a_volunteers = [
            self.ltla_two_a_volunteer,
            self.ltla_one_a_ltla_two_a_multi_la_volunteer,
        ]
        self.utla_one_volunteers = [
            self.ltla_one_a_volunteer,
            self.ltla_one_b_volunteer,
            self.utla_one_but_missing_ltla_volunteer,
            self.ltla_one_a_but_missing_utla_volunteer,
            self.ltla_one_a_ltla_one_b_multi_la_volunteer,
            self.ltla_one_a_ltla_two_a_multi_la_volunteer,
        ]
        self.utla_two_volunteers = [
            self.ltla_two_a_volunteer,
            self.ltla_two_b_volunteer,
            self.ltla_one_a_ltla_two_a_multi_la_volunteer,
        ]
        self.da_main_volunteers = [
            self.ltla_one_a_volunteer,
            self.ltla_two_a_volunteer,
            self.ltla_one_b_volunteer,
            self.ltla_two_b_volunteer,
            self.ltla_one_a_but_missing_utla_volunteer,
            self.utla_one_but_missing_ltla_volunteer,
            self.ltla_one_a_ltla_one_b_multi_la_volunteer,
            self.ltla_one_a_ltla_two_a_multi_la_volunteer,
        ]
        self.da_other_volunteers = [
            self.ltla_da_other_volunteer,
            self.ltla_da_other_but_missing_utla_volunteer,
            self.utla_da_other_but_missing_ltla_volunteer,
        ]
        self.da_england_volunteers = [
            self.da_england_volunteer,
        ] + list(
            MvVolunteer.objects.filter(
                accommodations__ltla_name__in=self.da_england_ltla_groups.values_list(
                    "ltla_name", flat=True
                ).distinct()
            )
        )


class UamsBaseTestCase(LocalAuthorityBaseTestCaseMixin):
    def setUp(self):
        super().setUp()

        self.ltla_one_a_uam = SponsorshipCertificationFormFactory(
            reference="SPON-1",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )
        self.ltla_two_a_uam = SponsorshipCertificationFormFactory(
            reference="SPON-2",
            ltla_name=[self.ltla_two_a_name],
            utla_name=[self.utla_two_name],
        )

        self.scotland_da_uam = SponsorshipCertificationFormFactory(
            reference="SPON-3",
            ltla_name=["Aberdeenshire"],
            utla_name=["Aberdeenshire"],
        )

        self.multiple_ltlas = SponsorshipCertificationFormFactory(
            reference="SPON-4",
            ltla_name=[self.ltla_one_a_name, self.ltla_one_b_name],
            utla_name=[self.utla_one_name],
        )

        self.multiple_utlas = SponsorshipCertificationFormFactory(
            reference="SPON-5",
            ltla_name=[self.ltla_two_a_name],
            utla_name=[self.utla_one_name, self.utla_two_name],
        )

        self.all_uams = [
            self.ltla_one_a_uam,
            self.ltla_two_a_uam,
            self.scotland_da_uam,
            self.multiple_ltlas,
            self.multiple_utlas,
        ]


class UkPostCodeTestCase(LocalAuthorityBaseTestCaseMixin):
    def setUp(self):
        super().setUp()

        self.ltla_one_a_postcode = MvUkPostcodeFactory(
            ltla_name=self.ltla_one_a_name,
            utla_name=self.utla_one_name,
            postcode_formatted="SW1A 1AA",
        )
        self.ltla_one_b_postcode = MvUkPostcodeFactory(
            ltla_name=self.ltla_one_b_name,
            utla_name=self.utla_one_name,
            postcode_formatted="SW1A 2BB",
        )
        self.ltla_two_a_postcode = MvUkPostcodeFactory(
            ltla_name=self.ltla_two_a_name,
            utla_name=self.utla_two_name,
            postcode_formatted="SW1A 3CC",
        )
        self.ltla_two_b_postcode = MvUkPostcodeFactory(
            ltla_name=self.ltla_two_b_name,
            utla_name=self.utla_two_name,
            postcode_formatted="SW1A 4DD",
        )
        self.ltla_other_da_postcode = MvUkPostcodeFactory(
            ltla_name=self.ltla_other_da_name,
            utla_name=self.utla_other_da_name,
            postcode_formatted="SW1A 5EE",
        )
        self.ltla_one_a_but_missing_utla_postcode = MvUkPostcodeFactory(
            ltla_name=self.ltla_one_a_name,
            utla_name="",
            postcode_formatted="SW1A 6FF",
        )
        self.utla_one_but_missing_ltla_postcode = MvUkPostcodeFactory(
            ltla_name="",
            utla_name=self.utla_one_name,
            postcode_formatted="SW1A 7GG",
        )
        self.da_england_postcode = MvUkPostcodeFactory(
            ltla_name="",
            utla_name="",
            viewer_group_names=[DaViewerGroupNames.ENGLAND],
            postcode_formatted="ENGL AND",
        )

        self.all_postcodes = [
            self.ltla_one_a_postcode,
            self.ltla_one_b_postcode,
            self.ltla_two_a_postcode,
            self.ltla_two_b_postcode,
            self.ltla_other_da_postcode,
            self.ltla_one_a_but_missing_utla_postcode,
            self.utla_one_but_missing_ltla_postcode,
            self.da_england_postcode,
        ]

        self.ltla_one_a_postcodes = [
            self.ltla_one_a_postcode,
            self.ltla_one_a_but_missing_utla_postcode,
        ]

        self.ltla_two_a_postcodes = [
            self.ltla_two_a_postcode,
        ]

        self.utla_one_postcodes = [
            self.ltla_one_a_postcode,
            self.ltla_one_b_postcode,
            self.ltla_one_a_but_missing_utla_postcode,
            self.utla_one_but_missing_ltla_postcode,
        ]

        self.utla_two_postcodes = [
            self.ltla_two_a_postcode,
            self.ltla_two_b_postcode,
        ]

        self.da_main_postcodes = [
            self.ltla_one_a_postcode,
            self.ltla_one_b_postcode,
            self.ltla_two_a_postcode,
            self.ltla_two_b_postcode,
            self.ltla_one_a_but_missing_utla_postcode,
            self.utla_one_but_missing_ltla_postcode,
        ]

        self.da_other_postcodes = [
            self.ltla_other_da_postcode,
        ]

        self.da_england_postcodes = [
            self.da_england_postcode,
        ]
