from django.db.models import QuerySet

from accounts.models import User
from ontology.models import VisaApplication
from ontology.tests.base import (
    LocalAuthorityPermissionsManagerBaseTestCase,
)
from user_management.tests.base import get_admin_user


class LocalAuthorityPermissionsManagerTestCase(
    LocalAuthorityPermissionsManagerBaseTestCase
):
    def _assert_visa_applications_query_set_equal(
        self,
        queryset: QuerySet[VisaApplication],
        visa_applications: list[VisaApplication],
    ):
        return self.assertQuerySetEqual(
            queryset.order_by("visa_application_id"),
            sorted(list({str(obj) for obj in visa_applications})),
            transform=str,
        )

    def assert_get_for_user_returns(
        self, user: User, visa_applications: list[VisaApplication]
    ):
        return self._assert_visa_applications_query_set_equal(
            VisaApplication.objects.get_for_user(user), visa_applications
        )

    def assert_get_all_annotate_with_user_can_view_returns(
        self, user: User, visa_applications: list[VisaApplication]
    ):
        return self._assert_visa_applications_query_set_equal(
            VisaApplication.objects.get_all_annotate_with_user_can_view(user),
            visa_applications,
        )

    def test_get_for_user_returns_all_objects_for_dev_user(self):
        self.assert_get_for_user_returns(self.ltla_user_dev, self.all_objects)

    def test_get_for_user_returns_only_objects_matching_groups_single_ltla(
        self,
    ):
        self.assert_get_for_user_returns(self.ltla_one_a_user, self.ltla_one_a_objects)

        self.assert_get_for_user_returns(self.ltla_two_a_user, self.ltla_two_a_objects)

        self.ltla_one_a_user.groups.set([self.ltla_one_a_no_utla_group])

        self.assert_get_for_user_returns(self.ltla_one_a_user, self.ltla_one_a_objects)

    def test_get_for_user_returns_only_objects_matching_groups_multi_ltla(
        self,
    ):
        self.assert_get_for_user_returns(
            self.ltla_one_a_ltla_one_b_user,
            self.ltla_one_a_objects + self.ltla_one_b_objects,
        )

    def test_get_for_user_returns_only_objects_matching_groups_single_utla(
        self,
    ):
        self.assert_get_for_user_returns(
            self.utla_one_user,
            self.utla_one_objects,
        )

        self.assert_get_for_user_returns(self.utla_two_user, self.utla_two_objects)

    def test_get_for_user_returns_only_objects_matching_groups_multi_utla(
        self,
    ):
        self.assert_get_for_user_returns(
            self.multi_utla_user, self.utla_one_objects + self.utla_two_objects
        )

    def test_get_for_user_returns_da_england_objects(
        self,
    ):
        self.assert_get_for_user_returns(self.da_england_user, self.da_england_objects)

    def test_get_for_user_returns_da_wales_objects(
        self,
    ):
        self.assert_get_for_user_returns(self.da_wales_user, self.da_wales_objects)

    def test_get_for_user_returns_da_scotland_objects(
        self,
    ):
        self.assert_get_for_user_returns(
            self.da_scotland_user, self.da_scotland_objects
        )

    def test_get_for_user_returns_da_northern_ireland_objects(
        self,
    ):
        self.assert_get_for_user_returns(
            self.da_northern_ireland_user, self.da_northern_ireland_objects
        )

    def test_get_for_user_returns_only_objects_matching_groups_single_da(
        self,
    ):
        self.assert_get_for_user_returns(self.da_main_user, self.da_main_objects)

        self.assert_get_for_user_returns(self.da_other_user, self.da_other_objects)

    def test_get_for_user_returns_only_objects_matching_groups_multi_da(
        self,
    ):
        self.assert_get_for_user_returns(
            self.multi_da_user, self.da_main_objects + self.da_other_objects
        )

    def test_get_for_user_returns_objects_from_utla_and_ltla_groups(self):
        self.utla_one_user.groups.set([self.utla_one_group, self.ltla_two_a_group])

        self.assert_get_for_user_returns(
            self.utla_one_user, self.utla_one_objects + self.ltla_two_a_objects
        )

    def test_get_for_user_returns_objects_from_da_and_other_la_groups(self):
        self.da_main_user.groups.set([self.da_main_group, self.ltla_other_da_group])

        self.assert_get_for_user_returns(
            self.da_main_user, self.da_main_objects + self.ltla_other_da_objects
        )

    def test_get_all_annotate_with_user_can_view_returns_all_objects(self):
        self.assert_get_all_annotate_with_user_can_view_returns(
            self.ltla_one_a_user, self.all_objects
        )

    def test_get_all_annotate_with_user_can_view_annotates_correctly_for_la_user(
        self,
    ):
        visa_applications = VisaApplication.objects.get_all_annotate_with_user_can_view(
            self.ltla_one_a_user
        )

        for visa_application in visa_applications:
            if visa_application in self.ltla_one_a_objects:
                self.assertTrue(visa_application.user_can_view)
            else:
                self.assertFalse(visa_application.user_can_view)

    def test_get_all_annotate_with_user_can_view_annotates_correctly_for_admin_user(
        self,
    ):
        visa_applications = VisaApplication.objects.get_all_annotate_with_user_can_view(
            get_admin_user()
        )

        for visa_application in visa_applications:
            self.assertTrue(visa_application.user_can_view)

    def test_get_all_annotate_with_user_can_view_annotates_correctly_for_da_user(
        self,
    ):
        visa_applications = VisaApplication.objects.get_all_annotate_with_user_can_view(
            self.da_england_user,
        )

        for visa_application in visa_applications:
            if visa_application in self.da_england_objects:
                self.assertTrue(visa_application.user_can_view)
            else:
                self.assertFalse(visa_application.user_can_view)
