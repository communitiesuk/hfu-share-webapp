import re

from django.test import TestCase
from django.urls import reverse

from accounts.enums import GroupType
from accounts.tests.base import TestSessionTokenMixin
from user_management.tests.base import (
    UserGroup,
    get_admin_user,
    get_la_user,
    get_user_with_groups,
    get_user_with_no_access,
)


def link_exists(text, html):
    pattern = (
        rf'class="[^"]*govuk-service-navigation__link[^"]*"[^>]*>{re.escape(text)}</a>'
    )
    return re.search(pattern, html, re.DOTALL | re.IGNORECASE) is not None


class NavBarLinkVisibilityTests(TestSessionTokenMixin, TestCase):
    def test_la_user_sees_expected_links(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()
        # LA users should see these links
        self.assertTrue(link_exists("Accommodation requests", html))
        self.assertTrue(link_exists("Accommodation", html))
        self.assertTrue(link_exists("Guests", html))
        self.assertTrue(link_exists("Sponsors and hosts", html))
        self.assertTrue(link_exists("Visa applications", html))
        self.assertTrue(link_exists("Download data", html))
        self.assertTrue(link_exists("Request access", html))

        # Shouldn't see these links
        self.assertFalse(link_exists("Deduplicate records", html))

    def test_admin_user_sees_all_links(self):
        user = get_admin_user()
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()
        # DEV users should see all links
        self.assertTrue(link_exists("Accommodation requests", html))
        self.assertTrue(link_exists("Accommodation", html))
        self.assertTrue(link_exists("Guests", html))
        self.assertTrue(link_exists("Sponsors and hosts", html))
        self.assertTrue(link_exists("Visa applications", html))
        self.assertTrue(link_exists("Download data", html))
        self.assertTrue(link_exists("Request access", html))

        # Shouldn't see these links
        self.assertFalse(link_exists("Deduplicate records", html))

    def test_user_with_no_access_only_sees_request(self):
        user = get_user_with_no_access()
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()

        self.assertTrue(link_exists("Request access", html))

        # Should not see any other links
        self.assertFalse(link_exists("Accommodation requests", html))
        self.assertFalse(link_exists("Accommodation", html))
        self.assertFalse(link_exists("Guests", html))
        self.assertFalse(link_exists("Sponsors and hosts", html))
        self.assertFalse(link_exists("Visa applications", html))
        self.assertFalse(link_exists("Deduplicate records", html))
        self.assertFalse(link_exists("Download data", html))

    def test_ukvi_user_sees_expected_links(self):
        user = get_user_with_groups(
            [
                UserGroup(name="home_office_ops", type=GroupType.HOME_OFFICE),
            ]
        )
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()
        # UKVI users (HOME_OFFICE) should see these links
        self.assertTrue(link_exists("Accommodation requests", html))
        self.assertTrue(link_exists("Accommodation", html))
        self.assertTrue(link_exists("Guests", html))
        self.assertTrue(link_exists("Sponsors and hosts", html))
        self.assertTrue(link_exists("Visa applications", html))
        self.assertTrue(link_exists("Request access", html))
        self.assertTrue(link_exists("Download data", html))

        # Should not see these links
        self.assertFalse(link_exists("Deduplicate records", html))

    def test_devolved_admin_user_sees_expected_links(self):
        user = get_user_with_groups(
            [UserGroup(name="devolved_admin", type=GroupType.DEVOLVED_ADMINISTRATION)]
        )
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()
        # Should see these links
        self.assertTrue(link_exists("Accommodation requests", html))
        self.assertTrue(link_exists("Accommodation", html))
        self.assertTrue(link_exists("Guests", html))
        self.assertTrue(link_exists("Sponsors and hosts", html))
        self.assertTrue(link_exists("Visa applications", html))
        self.assertTrue(link_exists("Download data", html))
        self.assertTrue(link_exists("Request access", html))

        # Shouldn't see these links
        self.assertFalse(link_exists("Deduplicate records", html))

    def test_mhclg_user_sees_expected_links(self):
        user = get_user_with_groups([UserGroup(name="mhclg", type=GroupType.MHCLG)])
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()
        # Should see these links
        self.assertTrue(link_exists("Accommodation requests", html))
        self.assertTrue(link_exists("Accommodation", html))
        self.assertTrue(link_exists("Guests", html))
        self.assertTrue(link_exists("Sponsors and hosts", html))
        self.assertTrue(link_exists("Visa applications", html))
        self.assertTrue(link_exists("Request access", html))
        self.assertTrue(link_exists("Download data", html))

        # Should not see these links
        self.assertFalse(link_exists("Deduplicate records", html))

    def test_service_support_user_sees_expected_links(self):
        user = get_user_with_groups(
            [UserGroup(name="service_support", type=GroupType.SERVICE_SUPPORT)]
        )
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()
        # Should see these links
        self.assertTrue(link_exists("Accommodation requests", html))
        self.assertTrue(link_exists("Accommodation", html))
        self.assertTrue(link_exists("Guests", html))
        self.assertTrue(link_exists("Sponsors and hosts", html))
        self.assertTrue(link_exists("Visa applications", html))
        self.assertTrue(link_exists("Download data", html))
        self.assertTrue(link_exists("Request access", html))

        # Shouldn't see these links
        self.assertFalse(link_exists("Deduplicate records", html))

    def test_multi_group_user_sees_expected_links(self):
        user = get_user_with_groups(
            [
                UserGroup(name="service_support", type=GroupType.SERVICE_SUPPORT),
                UserGroup(name="mhclg", type=GroupType.MHCLG),
            ]
        )
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()
        # Should see these links
        self.assertTrue(link_exists("Accommodation requests", html))
        self.assertTrue(link_exists("Accommodation", html))
        self.assertTrue(link_exists("Guests", html))
        self.assertTrue(link_exists("Sponsors and hosts", html))
        self.assertTrue(link_exists("Visa applications", html))
        self.assertTrue(link_exists("Request access", html))
        self.assertTrue(link_exists("Download data", html))

        # Shouldn't see these links
        self.assertFalse(link_exists("Deduplicate records", html))
