from accounts.models import User
from ontology.models import MvPerson
from ontology.tests.base import MvPersonBaseTestCase


class MvPersonPermissionsTest(MvPersonBaseTestCase):
    def assert_get_for_user_returns(self, user: User, persons: list[MvPerson]):
        return self.assertQuerySetEqual(
            MvPerson.objects.get_for_user(user).order_by("id"),
            sorted(list({str(obj) for obj in persons})),
            transform=str,
        )

    # Minimal tests because this is covered by the LocalAuthorityPermissionsManager test
    def test_get_for_user_returns_all_mv_persons_for_dev_user(self):
        self.assert_get_for_user_returns(self.ltla_user_dev, self.all_persons)

    def test_get_for_user_returns_persons_for_ltla_user(self):
        self.assert_get_for_user_returns(self.ltla_one_a_user, self.ltla_one_a_persons)

    def test_get_for_user_returns_persons_for_utla_user(self):
        self.assert_get_for_user_returns(self.utla_one_user, self.utla_one_persons)

    def test_get_for_user_returns_persons_for_da_user(self):
        self.assert_get_for_user_returns(self.da_main_user, self.da_main_persons)

    def test_get_for_user_returns_persons_for_da_viewer_group(self):
        self.assert_get_for_user_returns(self.da_england_user, self.da_england_persons)
