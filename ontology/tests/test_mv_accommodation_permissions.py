from accounts.models import User
from ontology.models import MvAccommodation
from ontology.tests.base import MvAccommodationTestCase


class MvAccommodationPermissionsTest(MvAccommodationTestCase):
    def assert_get_for_user_returns(
        self, user: User, accommodations: list[MvAccommodation]
    ):
        return self.assertQuerySetEqual(
            MvAccommodation.objects.get_for_user(user).order_by("id"),
            sorted(accommodations, key=lambda a: a.id),
        )

    # Minimal tests because this is covered by the LocalAuthorityPermissionsManager test
    def test_get_for_user_returns_all_mv_accommodations_for_dev_user(self):
        all_accommodations = list(MvAccommodation.objects.all())
        self.assert_get_for_user_returns(self.ltla_user_dev, all_accommodations)

    def test_get_for_user_returns_accommodations_for_ltla_user(self):
        self.assert_get_for_user_returns(
            self.ltla_one_a_user, self.ltla_one_a_accommodations
        )

    def test_get_for_user_returns_accommodations_for_utla_user(self):
        self.assert_get_for_user_returns(
            self.utla_one_user, self.utla_one_accommodations
        )

    def test_get_for_user_returns_accommodations_for_da_user(self):
        self.assert_get_for_user_returns(self.da_main_user, self.da_main_accommodations)

    def test_get_for_user_returns_accommodations_for_da_viewer_group(self):
        self.assert_get_for_user_returns(
            self.da_england_user, self.da_england_accommodations
        )
