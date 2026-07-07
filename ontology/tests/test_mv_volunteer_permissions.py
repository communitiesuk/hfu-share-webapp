from accounts.models import User
from ontology.models import MvVolunteer
from ontology.tests.base import MvVolunteerBaseTestCase


class MvVolunteerPermissionsTest(MvVolunteerBaseTestCase):
    def assert_get_for_user_returns(self, user: User, volunteers: list[MvVolunteer]):
        return self.assertQuerySetEqual(
            MvVolunteer.objects.get_for_user(user).order_by("id"),
            sorted(volunteers, key=lambda a: a.id),
        )

    # Minimal tests because this is covered by the LocalAuthorityPermissionsManager test
    def test_get_for_user_returns_all_mv_volunteers_for_dev_user(self):
        all_volunteers = list(MvVolunteer.objects.all())
        self.assert_get_for_user_returns(self.ltla_user_dev, all_volunteers)

    def test_get_for_user_returns_volunteers_for_ltla_user(self):
        self.assert_get_for_user_returns(
            self.ltla_one_a_user, self.ltla_one_a_volunteers
        )
        self.assert_get_for_user_returns(
            self.ltla_two_a_user, self.ltla_two_a_volunteers
        )

    def test_get_for_user_returns_volunteers_for_utla_user(self):
        self.assert_get_for_user_returns(self.utla_one_user, self.utla_one_volunteers)
        self.assert_get_for_user_returns(self.utla_two_user, self.utla_two_volunteers)

    def test_get_for_user_returns_volunteers_for_da_user(self):
        self.assert_get_for_user_returns(self.da_main_user, self.da_main_volunteers)
        self.assert_get_for_user_returns(self.da_other_user, self.da_other_volunteers)

    def test_get_for_user_returns_volunteers_for_da_user_with_viewer_groups(self):
        self.assert_get_for_user_returns(
            self.da_england_user, self.da_england_volunteers
        )
