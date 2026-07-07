from accounts.models import User
from ontology.models import MvAccommodationRequest
from ontology.tests.base import MvAccommodationRequestTestCase


class MvAccommodationRequestPermissionsTest(MvAccommodationRequestTestCase):
    def assert_get_for_user_returns(
        self, user: User, requests: list[MvAccommodationRequest]
    ):
        return self.assertQuerySetEqual(
            MvAccommodationRequest.objects.get_for_user(user).order_by("id"),
            sorted(list({str(obj) for obj in requests})),
            transform=str,
        )

    # Minimal tests because this is covered by the LocalAuthorityPermissionsManager test
    def test_get_for_user_returns_all_mv_persons_for_dev_user(self):
        self.assert_get_for_user_returns(
            self.ltla_user_dev, self.all_accommodation_requests
        )

    def test_get_for_user_returns_persons_for_ltla_user(self):
        self.assert_get_for_user_returns(
            self.ltla_one_a_user, self.ltla_one_a_accommodation_requests
        )

    def test_get_for_user_returns_persons_for_utla_user(self):
        self.assert_get_for_user_returns(
            self.utla_one_user, self.utla_one_accommodation_requests
        )

    def test_get_for_user_returns_persons_for_da_user(self):
        self.assert_get_for_user_returns(
            self.da_main_user, self.da_main_accommodation_requests
        )

    def test_get_for_user_returns_persons_for_da_viewer_groups(self):
        self.assert_get_for_user_returns(
            self.da_england_user, self.da_england_accommodation_requests
        )
