from typing import Tuple

from bs4 import BeautifulSoup
from django.urls import reverse

from accounts.enums import GroupType
from accounts.tests.base import TestSessionTokenMixin
from test_utils.base import BaseTestCase
from user_management.tests.base import (
    UserGroup,
    get_admin_user,
    get_la_user,
    get_user_with_groups,
    get_user_with_no_access,
)


class NavBarLinkVisibilityTests(TestSessionTokenMixin, BaseTestCase):
    def assert_links_exist(self, soup: BeautifulSoup, *links: Tuple[str, ...]):
        for navigation_link, expected_text in zip(
            soup.select(
                "a.govuk-service-navigation__link",
            ),
            links,
            strict=True,
        ):
            self.assertEqual(navigation_link.text.strip(), expected_text)

    def test_la_user_sees_expected_links(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        soup = BeautifulSoup(response.content.decode("utf-8"), "html.parser")

        # LA users should see these links
        self.assert_links_exist(
            soup,
            "Visa applications",
            "Guests",
            "Sponsors and hosts",
            "Accommodation",
            "Accommodation requests",
            "Download data",
            "Request access",
        )

    def test_admin_user_sees_all_links(self):
        user = get_admin_user()
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        soup = BeautifulSoup(response.content.decode("utf-8"), "html.parser")

        # DEV users should see all links
        self.assert_links_exist(
            soup,
            "Visa applications",
            "Guests",
            "Sponsors and hosts",
            "Accommodation",
            "Accommodation requests",
            "Download data",
            "Request access",
        )

    def test_user_with_no_access_only_sees_request(self):
        user = get_user_with_no_access()
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        soup = BeautifulSoup(response.content.decode("utf-8"), "html.parser")

        self.assert_links_exist(
            soup,
            "Request access",
        )

    def test_ukvi_user_sees_expected_links(self):
        user = get_user_with_groups(
            [
                UserGroup(name="home_office_ops", type=GroupType.HOME_OFFICE),
            ]
        )
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        soup = BeautifulSoup(response.content.decode("utf-8"), "html.parser")
        # UKVI users (HOME_OFFICE) should see these links
        self.assert_links_exist(
            soup,
            "Visa applications",
            "Guests",
            "Sponsors and hosts",
            "Accommodation",
            "Accommodation requests",
            "Download data",
            "Request access",
        )

    def test_devolved_admin_user_sees_expected_links(self):
        user = get_user_with_groups(
            [UserGroup(name="devolved_admin", type=GroupType.DEVOLVED_ADMINISTRATION)]
        )
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        soup = BeautifulSoup(response.content.decode("utf-8"), "html.parser")
        # Should see these links
        self.assert_links_exist(
            soup,
            "Visa applications",
            "Guests",
            "Sponsors and hosts",
            "Accommodation",
            "Accommodation requests",
            "Download data",
            "Request access",
        )

    def test_mhclg_user_sees_expected_links(self):
        user = get_user_with_groups([UserGroup(name="mhclg", type=GroupType.MHCLG)])
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        soup = BeautifulSoup(response.content.decode("utf-8"), "html.parser")
        # Should see these links
        self.assert_links_exist(
            soup,
            "Visa applications",
            "Guests",
            "Sponsors and hosts",
            "Accommodation",
            "Accommodation requests",
            "Download data",
            "Request access",
        )

    def test_service_support_user_sees_expected_links(self):
        user = get_user_with_groups(
            [UserGroup(name="service_support", type=GroupType.SERVICE_SUPPORT)]
        )
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        soup = BeautifulSoup(response.content.decode("utf-8"), "html.parser")
        # Should see these links
        self.assert_links_exist(
            soup,
            "Visa applications",
            "Guests",
            "Sponsors and hosts",
            "Accommodation",
            "Accommodation requests",
            "Download data",
            "Request access",
        )

    def test_links_shown_on_page_without_user_actions_mixin(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("user-management:access-request-confirmation")
        )
        soup = BeautifulSoup(response.content.decode("utf-8"), "html.parser")

        self.assert_links_exist(
            soup,
            "Visa applications",
            "Guests",
            "Sponsors and hosts",
            "Accommodation",
            "Accommodation requests",
            "Download data",
            "Request access",
        )

    def test_group_change_updates_links_without_logging_in_again(self):
        user = get_user_with_no_access()
        self.client.force_login(user)
        soup = BeautifulSoup(
            self.client.get(reverse("webapp:landing-page")).content.decode("utf-8"),
            "html.parser",
        )

        self.assert_links_exist(
            soup,
            "Request access",
        )

        la_user = get_la_user()
        user.groups.set(la_user.groups.all())

        soup = BeautifulSoup(
            self.client.get(reverse("webapp:landing-page")).content.decode("utf-8"),
            "html.parser",
        )
        self.assert_links_exist(
            soup,
            "Visa applications",
            "Guests",
            "Sponsors and hosts",
            "Accommodation",
            "Accommodation requests",
            "Download data",
            "Request access",
        )

    def test_multi_group_user_sees_expected_links(self):
        user = get_user_with_groups(
            [
                UserGroup(name="service_support", type=GroupType.SERVICE_SUPPORT),
                UserGroup(name="mhclg", type=GroupType.MHCLG),
            ]
        )
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        soup = BeautifulSoup(response.content.decode("utf-8"), "html.parser")
        # Should see these links
        self.assert_links_exist(
            soup,
            "Visa applications",
            "Guests",
            "Sponsors and hosts",
            "Accommodation",
            "Accommodation requests",
            "Download data",
            "Request access",
        )
