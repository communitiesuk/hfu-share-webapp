from django.test import RequestFactory

from ontology.tests.base import UamsBaseTestCase
from uams.views import UamsListView
from user_management.tests.base import get_da_user


class UamsListViewTestCase(UamsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.request = RequestFactory().get("/")

    def test_get_queryset_for_ltla_user(self):
        """
        Test that get_queryset returns for the regular ltla users.
        """

        self.request.user = self.ltla_one_a_user
        view = UamsListView()
        view.request = self.request

        self.assertQuerySetEqual(
            list(view.get_queryset()),
            [str(self.ltla_one_a_uam), str(self.multiple_ltlas)],
            transform=str,
        )

    def test_get_queryset_for_utla_user(self):
        """
        Test that get_queryset returns for regular utla users.
        """

        self.request.user = self.utla_two_user
        view = UamsListView()
        view.request = self.request

        self.assertQuerySetEqual(
            list(view.get_queryset()),
            [str(self.ltla_two_a_uam), str(self.multiple_utlas)],
            transform=str,
        )

    def test_get_queryset_for_da_user(self):
        """
        Test that get_queryset returns for regular da users.
        """

        self.request.user = get_da_user()
        view = UamsListView()
        view.request = self.request

        self.assertQuerySetEqual(
            list(view.get_queryset()),
            [str(self.scotland_da_uam)],
            transform=str,
        )

    def test_get_queryset_returns_all_for_dev_user(self):
        """
        Test that get_queryset returns all objects for a dev user.
        """

        self.request.user = self.ltla_user_dev
        view = UamsListView()
        view.request = self.request

        self.assertQuerySetEqual(
            list(view.get_queryset()),
            list(map(str, self.all_uams)),
            transform=str,
        )

    def test_get_queryset_returns_empty_if_no_uams(self):
        """
        Test that get_queryset returns an empty queryset if no user LAs have UAMs
        """

        self.request.user = self.ltla_no_group_user
        view = UamsListView()
        view.request = self.request

        self.assertQuerySetEqual(
            list(view.get_queryset()),
            [],
            transform=str,
        )
