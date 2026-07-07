from accounts.models import User
from ontology.models import MvUkPostcode
from ontology.tests.base import UkPostCodeTestCase


class MvUkPostcodePermissionsTest(UkPostCodeTestCase):
    def assert_get_for_user_returns(self, user: User, postcodes: list[MvUkPostcode]):
        return self.assertQuerySetEqual(
            MvUkPostcode.objects.get_for_user(user).order_by("id"),
            sorted(postcodes, key=lambda p: p.id),
        )

    # Minimal tests because this is covered by the LocalAuthorityPermissionsManager test
    def test_get_for_user_returns_all_mv_postcodes_for_dev_user(self):
        self.assert_get_for_user_returns(self.ltla_user_dev, self.all_postcodes)

    def test_get_for_user_returns_postcodes_for_ltla_user(self):
        self.assert_get_for_user_returns(
            self.ltla_one_a_user, self.ltla_one_a_postcodes
        )
        self.assert_get_for_user_returns(
            self.ltla_two_a_user, self.ltla_two_a_postcodes
        )

    def test_get_for_user_returns_postcodes_for_utla_user(self):
        self.assert_get_for_user_returns(self.utla_one_user, self.utla_one_postcodes)
        self.assert_get_for_user_returns(self.utla_two_user, self.utla_two_postcodes)

    def test_get_for_user_returns_postcodes_for_da_user(self):
        self.assert_get_for_user_returns(self.da_main_user, self.da_main_postcodes)
        self.assert_get_for_user_returns(self.da_other_user, self.da_other_postcodes)

    def test_get_for_user_returns_postcodes_for_da_viewer_groups(self):
        self.assert_get_for_user_returns(
            self.da_england_user, self.da_england_postcodes
        )
