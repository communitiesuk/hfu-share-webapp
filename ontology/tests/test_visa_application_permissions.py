from accounts.models import User
from ontology.models import VisaApplication
from ontology.tests.base import VisaApplicationBaseTestCase


class VisaApplicationPermissionsTestCase(VisaApplicationBaseTestCase):
    # Tests here are slightly maximal for historical reasons.
    # Most of this is covered by LocalAuthorityPermissionsManager

    def assert_get_for_user_returns(
        self, user: User, visa_applications: list[VisaApplication]
    ):
        return self.assertQuerySetEqual(
            VisaApplication.objects.get_for_user(user).order_by("visa_application_id"),
            sorted(list({str(obj) for obj in visa_applications})),
            transform=str,
        )

    def test_get_for_user_returns_all_visa_applications_for_dev_user(self):
        self.assert_get_for_user_returns(
            self.ltla_user_dev,
            self.all_visa_applications,
        )

    def test_get_for_user_returns_only_visa_applications_matching_groups_single_la(
        self,
    ):
        self.assert_get_for_user_returns(
            self.ltla_one_a_user, self.ltla_one_a_visa_applications
        )

        self.assert_get_for_user_returns(
            self.ltla_two_a_user, self.ltla_two_a_visa_applications
        )

    def test_get_for_user_returns_only_visa_applications_matching_groups_multi_la(
        self,
    ):
        self.ltla_one_a_user.groups.set([self.ltla_one_a_group, self.ltla_two_a_group])

        self.assert_get_for_user_returns(
            self.ltla_one_a_user,
            self.ltla_one_a_visa_applications + self.ltla_two_a_visa_applications,
        )

    def test_get_for_user_returns_only_visa_applications_matching_groups_single_utla(
        self,
    ):
        self.assert_get_for_user_returns(
            self.utla_one_user, self.utla_one_visa_applications
        )

        self.assert_get_for_user_returns(
            self.utla_two_user, self.utla_two_visa_applications
        )

    def test_get_for_user_returns_only_visa_applications_matching_groups_multi_utla(
        self,
    ):
        self.assert_get_for_user_returns(
            self.multi_utla_user,
            self.utla_one_visa_applications + self.utla_two_visa_applications,
        )

    def test_get_for_user_returns_only_visa_applications_matching_groups_single_da(
        self,
    ):
        self.assert_get_for_user_returns(
            self.da_main_user, self.da_main_visa_applications
        )

        self.assert_get_for_user_returns(
            self.da_other_user, self.da_other_visa_applications
        )

    def test_get_for_user_returns_only_visa_applications_matching_groups_multi_da(
        self,
    ):
        self.assert_get_for_user_returns(
            self.multi_da_user,
            self.da_main_visa_applications + self.da_other_visa_applications,
        )

    def test_get_for_user_returns_only_applications_matching_groups_da_viewer_group(
        self,
    ):
        self.assert_get_for_user_returns(
            self.da_england_user,
            self.da_england_visa_applications,
        )
