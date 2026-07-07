import re

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.enums import GroupType
from accounts.models import AccessRequest
from accounts.tests.base import TestSessionTokenMixin
from accounts.tests.factories import AccessRequestFactory
from ontology.tests.factories import AnnouncementFactory
from user_management.templatetags.access_request_extras import (
    render_name_label_from_group_info,
)
from user_management.tests.base import (
    UserGroup,
    get_admin_user,
    get_da_user,
    get_ea_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
    get_user_with_groups,
    get_user_with_no_access,
)


def selectable_card_exists(text, html, body=""):
    pattern = rf'<div[^>]*class="[^"]*govuk-card--selectable[^"]*"[^>]*>.*?{re.escape(text)}.*?{re.escape(body)}.*?</div>'  # noqa: E501
    return re.search(pattern, html, re.DOTALL | re.IGNORECASE) is not None


class LandingPageTests(TestSessionTokenMixin, TestCase):
    def test_should_not_show_task_list_if_no_access(self):
        user = get_user_with_no_access()
        self.client.force_login(user)

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertNotContains(response, "Tasks")

    def test_should_not_show_task_list_if_user_has_access(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertNotContains(response, "Tasks")

    def test_should_show_pending_access_requests(self):
        user = get_la_user()
        self.client.force_login(user)
        access_request = AccessRequestFactory(
            requester=user, status=AccessRequest.Status.PENDING
        )

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertContains(
            response, render_name_label_from_group_info(access_request.group_info)
        )

    def test_pending_access_requests_have_no_remove_action(self):
        user = get_la_user()
        self.client.force_login(user)
        access_request = AccessRequestFactory(
            requester=user, status=AccessRequest.Status.PENDING
        )

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertContains(
            response, render_name_label_from_group_info(access_request.group_info)
        )
        self.assertNotContains(response, "Remove")

    def test_should_not_show_other_users_pending_access_requests(self):
        user = get_la_user()
        other_user = get_user_with_no_access()
        self.client.force_login(user)
        access_request = AccessRequestFactory(
            requester=other_user, status=AccessRequest.Status.PENDING
        )

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertNotContains(
            response, render_name_label_from_group_info(access_request.group_info)
        )

    def test_should_show_rejected_access_requests(self):
        user = get_la_user()
        self.client.force_login(user)
        access_request = AccessRequestFactory(
            requester=user, status=AccessRequest.Status.REJECTED
        )

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertContains(
            response, render_name_label_from_group_info(access_request.group_info)
        )

    def test_rejected_access_requests_have_remove_action(self):
        user = get_la_user()
        self.client.force_login(user)
        access_request = AccessRequestFactory(
            requester=user, status=AccessRequest.Status.REJECTED
        )

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertContains(
            response, render_name_label_from_group_info(access_request.group_info)
        )
        self.assertContains(response, "Remove")

    def test_should_not_show_other_users_rejected_access_requests(self):
        user = get_la_user()
        other_user = get_user_with_no_access()
        self.client.force_login(user)
        access_request = AccessRequestFactory(
            requester=other_user, status=AccessRequest.Status.REJECTED
        )

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertNotContains(
            response, render_name_label_from_group_info(access_request.group_info)
        )

    def test_should_show_approved_access_requests(self):
        user = get_la_user()
        self.client.force_login(user)
        access_request = AccessRequestFactory(
            requester=user, status=AccessRequest.Status.APPROVED
        )

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertContains(
            response, render_name_label_from_group_info(access_request.group_info)
        )

    def test_approved_access_requests_have_no_remove_action(self):
        user = get_la_user()
        self.client.force_login(user)
        access_request = AccessRequestFactory(
            requester=user, status=AccessRequest.Status.APPROVED
        )

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertContains(
            response, render_name_label_from_group_info(access_request.group_info)
        )
        self.assertNotContains(response, "Remove")

    def test_should_not_show_approved_access_requests_if_access_revoked(self):
        user = get_la_user()
        self.client.force_login(user)
        access_request = AccessRequestFactory(
            requester=user, status=AccessRequest.Status.APPROVED, access_revoked=True
        )

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertNotContains(
            response, render_name_label_from_group_info(access_request.group_info)
        )

    def test_should_not_show_other_users_approved_access_requests(self):
        user = get_la_user()
        other_user = get_user_with_no_access()
        self.client.force_login(user)
        access_request = AccessRequestFactory(
            requester=other_user, status=AccessRequest.Status.APPROVED
        )

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertNotContains(
            response, render_name_label_from_group_info(access_request.group_info)
        )

    def test_should_show_empty_message_when_no_pending_access_requests(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertContains(response, "You have no pending requests")

    def test_should_show_empty_message_when_no_rejected_access_requests(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertContains(response, "You have no rejected requests")

    def test_should_show_empty_message_when_no_approved_access_requests(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertContains(response, "You have no approved requests")

    def test_should_show_request_access_button(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertContains(response, "Request access")

    def test_cards_have_correct_content(self):
        user = get_admin_user()
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()
        # DEV users should see all cards
        self.assertTrue(
            selectable_card_exists(
                "Accommodation requests",
                html,
                "Find accommodation requests and safeguarding checks."
                "  You can also move guests (rematch and reassign), withdraw"
                " sponsors or close and reopen accommodation requests.",
            )
        )
        self.assertTrue(
            selectable_card_exists(
                "Accommodation", html, "Look at and update accommodation records."
            )
        )
        self.assertTrue(
            selectable_card_exists(
                "Guests",
                html,
                "Look at and update guest records.",
            )
        )
        self.assertTrue(
            selectable_card_exists(
                "Sponsors and hosts",
                html,
                "Look at and update sponsor and host records.",
            )
        )
        self.assertTrue(
            selectable_card_exists(
                "Visa applications",
                html,
                "Find visa applications for guests and check their status.",
            )
        )
        self.assertTrue(
            selectable_card_exists(
                "Reassignment requests",
                html,
                "Review requests made to reassign guests to your local authority.",
            )
        )
        self.assertTrue(
            selectable_card_exists(
                "Escalated checks",
                html,
                "Review failed safeguarding checks.",
            )
        )
        self.assertTrue(
            selectable_card_exists("Manage people, access and permissions", html)
        )
        self.assertTrue(
            selectable_card_exists(
                "Download data",
                html,
                "Download data for sponsors and hosts, accommodation, guests, and"
                " visa applications. You can also download all data.",
            )
        )
        self.assertTrue(
            selectable_card_exists(
                "Applications to sponsor a child",
                html,
                "View requests to sponsor a Ukrainian child (eligible children or "
                "minors) who will be living in the UK without a parent or guardian. "
                "Checks must be completed offline before the guest applies for a visa.",
            )
        )
        self.assertTrue(
            selectable_card_exists(
                "Visa Information Requests",
                html,
                "Check for current Visa Information Requests that you need to "
                "respond to.",
            )
        )
        self.assertTrue(
            selectable_card_exists(
                "Fix duplicate records",
                html,
                "Find and deduplicate 2 records that represent the same "
                "accommodation, guest or sponsor and host.",
            )
        )

        self.assertContains(response, "Request access to data")


class LandingPageCardVisibilityTests(TestSessionTokenMixin, TestCase):
    def test_la_user_sees_expected_cards(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()
        # LA users should see these cards
        self.assertTrue(selectable_card_exists("Accommodation requests", html))
        self.assertTrue(selectable_card_exists("Accommodation", html))
        self.assertTrue(selectable_card_exists("Guests", html))
        self.assertTrue(selectable_card_exists("Sponsors and hosts", html))
        self.assertTrue(selectable_card_exists("Visa applications", html))
        self.assertTrue(selectable_card_exists("Reassignment requests", html))
        self.assertTrue(selectable_card_exists("Download data", html))
        self.assertTrue(selectable_card_exists("Applications to sponsor a child", html))
        self.assertContains(response, "Request access to data")

        # LA users should not see these cards
        self.assertFalse(selectable_card_exists("Escalated checks", html))
        self.assertFalse(
            selectable_card_exists("Manage people, access and permissions", html)
        )
        self.assertFalse(
            selectable_card_exists(
                "Find and deduplicate 2 records that represent the same accommodation, "
                "guest or sponsor and host.",
                html,
            )
        )

    def test_admin_user_sees_all_cards(self):
        user = get_admin_user()
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()
        # DEV users should see all cards
        self.assertTrue(selectable_card_exists("Accommodation requests", html))
        self.assertTrue(selectable_card_exists("Accommodation", html))
        self.assertTrue(selectable_card_exists("Guests", html))
        self.assertTrue(selectable_card_exists("Sponsors and hosts", html))
        self.assertTrue(selectable_card_exists("Visa applications", html))
        self.assertTrue(selectable_card_exists("Reassignment requests", html))
        self.assertTrue(selectable_card_exists("Escalated checks", html))
        self.assertTrue(
            selectable_card_exists("Manage people, access and permissions", html)
        )
        self.assertTrue(selectable_card_exists("Download data", html))
        self.assertTrue(selectable_card_exists("Applications to sponsor a child", html))
        self.assertTrue(selectable_card_exists("Visa Information Requests", html))
        self.assertContains(response, "Request access to data")
        self.assertTrue(
            selectable_card_exists(
                "Find and deduplicate 2 records that represent the same accommodation, "
                "guest or sponsor and host.",
                html,
            )
        )

    def test_early_adopter_sees_expected_cards(self):
        user = get_ea_user()
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()

        # EA users should see these cards
        self.assertTrue(selectable_card_exists("Accommodation requests", html))
        self.assertTrue(selectable_card_exists("Accommodation", html))
        self.assertTrue(selectable_card_exists("Guests", html))
        self.assertTrue(selectable_card_exists("Sponsors and hosts", html))
        self.assertTrue(selectable_card_exists("Visa applications", html))
        self.assertTrue(selectable_card_exists("Reassignment requests", html))
        self.assertTrue(selectable_card_exists("Download data", html))
        self.assertTrue(selectable_card_exists("Applications to sponsor a child", html))
        self.assertContains(response, "Request access to data")
        self.assertTrue(
            selectable_card_exists(
                "Find and deduplicate 2 records that represent the same accommodation "
                "or sponsor and host.",
                html,
            )
        )

        # EA users should not see these cards
        self.assertFalse(selectable_card_exists("Escalated checks", html))
        self.assertFalse(
            selectable_card_exists("Manage people, access and permissions", html)
        )

    def test_ukvi_user_sees_expected_cards(self):
        user = get_ukvi_user()
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()
        # UKVI users (HOME_OFFICE) should see these cards
        self.assertTrue(selectable_card_exists("Accommodation requests", html))
        self.assertTrue(selectable_card_exists("Accommodation", html))
        self.assertTrue(selectable_card_exists("Guests", html))
        self.assertTrue(selectable_card_exists("Sponsors and hosts", html))
        self.assertFalse(selectable_card_exists("Reassignment requests", html))
        self.assertTrue(selectable_card_exists("Visa applications", html))
        self.assertTrue(selectable_card_exists("Escalated checks", html))
        self.assertTrue(selectable_card_exists("Applications to sponsor a child", html))
        self.assertTrue(selectable_card_exists("Visa Information Requests", html))
        self.assertContains(response, "Request access to data")
        self.assertTrue(selectable_card_exists("Download data", html))

        # Should not see these cards
        self.assertFalse(
            selectable_card_exists("Manage people, access and permissions", html)
        )
        self.assertFalse(
            selectable_card_exists(
                "Find and deduplicate 2 records that represent the same accommodation, "
                "guest or sponsor and host.",
                html,
            )
        )

    def test_devolved_admin_user_sees_expected_cards(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()
        # Should see these cards
        self.assertTrue(selectable_card_exists("Accommodation requests", html))
        self.assertTrue(selectable_card_exists("Accommodation", html))
        self.assertTrue(selectable_card_exists("Guests", html))
        self.assertTrue(selectable_card_exists("Sponsors and hosts", html))
        self.assertTrue(selectable_card_exists("Visa applications", html))
        self.assertTrue(selectable_card_exists("Reassignment requests", html))
        self.assertTrue(selectable_card_exists("Download data", html))
        self.assertTrue(selectable_card_exists("Visa Information Requests", html))
        self.assertContains(response, "Request access to data")

        # Should not see these cards
        self.assertFalse(
            selectable_card_exists("Applications to sponsor a child", html)
        )
        self.assertFalse(selectable_card_exists("Escalated checks", html))
        self.assertFalse(
            selectable_card_exists("Manage people, access and permissions", html)
        )
        self.assertFalse(
            selectable_card_exists(
                "Find and deduplicate 2 records that represent the same accommodation, "
                "guest or sponsor and host.",
                html,
            )
        )

    def test_mhclg_user_sees_expected_cards(self):
        user = get_mhclg_user()
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()
        # Should see these cards
        self.assertTrue(selectable_card_exists("Accommodation requests", html))
        self.assertTrue(selectable_card_exists("Accommodation", html))
        self.assertTrue(selectable_card_exists("Guests", html))
        self.assertTrue(selectable_card_exists("Sponsors and hosts", html))
        self.assertTrue(selectable_card_exists("Visa applications", html))
        self.assertTrue(selectable_card_exists("Reassignment requests", html))
        self.assertTrue(selectable_card_exists("Escalated checks", html))
        self.assertTrue(selectable_card_exists("Applications to sponsor a child", html))
        self.assertTrue(selectable_card_exists("Visa Information Requests", html))
        self.assertContains(response, "Request access to data")
        self.assertTrue(selectable_card_exists("Download data", html))

        # Should not see these cards
        self.assertFalse(
            selectable_card_exists("Manage people, access and permissions", html)
        )
        self.assertFalse(
            selectable_card_exists(
                "Find and deduplicate 2 records that represent the same accommodation, "
                "guest or sponsor and host.",
                html,
            )
        )

    def test_service_support_user_sees_expected_cards(self):
        user = get_service_support_user()
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()
        # Should see these cards
        self.assertTrue(selectable_card_exists("Accommodation requests", html))
        self.assertTrue(selectable_card_exists("Accommodation", html))
        self.assertTrue(selectable_card_exists("Guests", html))
        self.assertTrue(selectable_card_exists("Sponsors and hosts", html))
        self.assertTrue(selectable_card_exists("Visa applications", html))
        self.assertTrue(selectable_card_exists("Reassignment requests", html))
        self.assertTrue(selectable_card_exists("Download data", html))
        self.assertTrue(selectable_card_exists("Visa Information Requests", html))
        self.assertContains(response, "Request access to data")

        # Should not see these cards
        self.assertFalse(
            selectable_card_exists("Applications to sponsor a child", html)
        )
        self.assertFalse(selectable_card_exists("Escalated checks", html))
        self.assertFalse(
            selectable_card_exists("Manage people, access and permissions", html)
        )
        self.assertFalse(
            selectable_card_exists(
                "Find and deduplicate 2 records that represent the same accommodation, "
                "guest or sponsor and host.",
                html,
            )
        )

    def test_multi_group_user_sees_expected_cards(self):
        user = get_user_with_groups(
            [
                UserGroup(name="service_support", type=GroupType.SERVICE_SUPPORT),
                UserGroup(name="mhclg", type=GroupType.MHCLG),
            ]
        )
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))
        html = response.content.decode()
        # Should see these cards
        self.assertTrue(selectable_card_exists("Accommodation requests", html))
        self.assertTrue(selectable_card_exists("Accommodation", html))
        self.assertTrue(selectable_card_exists("Guests", html))
        self.assertTrue(selectable_card_exists("Sponsors and hosts", html))
        self.assertTrue(selectable_card_exists("Visa applications", html))
        self.assertTrue(selectable_card_exists("Reassignment requests", html))
        self.assertTrue(selectable_card_exists("Escalated checks", html))
        self.assertTrue(selectable_card_exists("Download data", html))
        self.assertTrue(selectable_card_exists("Applications to sponsor a child", html))
        self.assertTrue(selectable_card_exists("Visa Information Requests", html))
        self.assertContains(response, "Request access to data")

        # Should not see these cards
        self.assertFalse(
            selectable_card_exists("Manage people, access and permissions", html)
        )
        self.assertFalse(
            selectable_card_exists(
                "Find and deduplicate 2 records that represent the same accommodation, "
                "guest or sponsor and host.",
                html,
            )
        )

    def test_guidance_and_support_section_renders_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:landing-page"))

        self.assertContains(response, "Guidance and support")
        self.assertContains(response, "Training and guidance for Share")
        self.assertContains(response, "Homes for Ukraine: council guides on GOV.UK")
        self.assertContains(response, "Raise a support ticket")
        self.assertContains(response, "Contact us")
        self.assertContains(response, "Phone: 0303 4444 445")
        self.assertContains(response, "Monday to Friday, 9am to 6pm")
        self.assertContains(response, "Find out about call charges")

    def test_should_show_visible_announcements(self):
        user = get_admin_user()
        self.client.force_login(user)

        announcement_visible = AnnouncementFactory(
            title="Announcement Title",
            body="Announcement Body",
            link="https://gov.uk",
            link_text="Read more",
        )
        announcement_visible.save()

        announcement_hidden = AnnouncementFactory(
            title="Hidden Announcement Title",
            body="Hidden Announcement Body",
            hidden=True,
        )
        announcement_hidden.save()

        response = self.client.get(reverse("webapp:landing-page"))

        self.assertContains(response, "Announcements")

        self.assertContains(response, announcement_visible.title)
        self.assertContains(response, announcement_visible.body)
        self.assertContains(response, announcement_visible.link_text)

        self.assertNotContains(response, announcement_hidden.title)
        self.assertNotContains(response, announcement_hidden.body)


class LandingPageFixDuplicateAccommodationTileTests(TestSessionTokenMixin, TestCase):
    TILE_BODY_WITH_GUESTS = (
        "Find and deduplicate 2 records that represent the same accommodation, "
        "guest or sponsor and host."
    )
    TILE_BODY_WITHOUT_GUESTS = (
        "Find and deduplicate 2 records that represent the same accommodation "
        "or sponsor and host."
    )

    def _get_landing_html(self, user):
        self.client.force_login(user)
        return self.client.get(reverse("webapp:landing-page")).content.decode()

    def _count_fix_duplicate_tiles(self, html):
        pattern = (
            r'<div[^>]*class="[^"]*govuk-card--selectable[^"]*"[^>]*>'
            r".*?Fix duplicate records.*?</div>"
        )
        return len(re.findall(pattern, html, re.DOTALL | re.IGNORECASE))

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=True)
    def test_flag_on_la_user_sees_tile(self):
        html = self._get_landing_html(get_la_user())
        self.assertEqual(self._count_fix_duplicate_tiles(html), 1)
        self.assertTrue(
            selectable_card_exists(
                "Fix duplicate records", html, self.TILE_BODY_WITHOUT_GUESTS
            )
        )

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=True)
    def test_flag_on_da_user_sees_tile(self):
        html = self._get_landing_html(get_da_user())
        self.assertEqual(self._count_fix_duplicate_tiles(html), 1)
        self.assertTrue(
            selectable_card_exists(
                "Fix duplicate records", html, self.TILE_BODY_WITHOUT_GUESTS
            )
        )

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=True)
    def test_flag_on_mhclg_user_sees_tile(self):
        html = self._get_landing_html(get_mhclg_user())
        self.assertEqual(self._count_fix_duplicate_tiles(html), 1)

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=True)
    def test_flag_on_service_support_user_sees_tile(self):
        html = self._get_landing_html(get_service_support_user())
        self.assertEqual(self._count_fix_duplicate_tiles(html), 1)

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=False)
    def test_dev_user_sees_tile_with_guests_body_text(self):
        html = self._get_landing_html(get_admin_user())
        self.assertEqual(self._count_fix_duplicate_tiles(html), 1)
        self.assertTrue(
            selectable_card_exists(
                "Fix duplicate records", html, self.TILE_BODY_WITH_GUESTS
            )
        )


@override_settings(FIX_DUPLICATE_RECORDS_ENABLED=False)
class FixDuplicateRecordsFeatureDisabledTests(TestSessionTokenMixin, TestCase):
    def get_landing_page_response(self, user):
        self.client.force_login(user)
        return self.client.get(reverse("webapp:landing-page"))

    def test_la_user_cannot_see_fix_duplicate_records_tile(self):
        self.assertNotContains(
            self.get_landing_page_response(get_la_user()), "Fix duplicate records"
        )

    def test_da_user_cannot_see_fix_duplicate_records_tile(self):
        self.assertNotContains(
            self.get_landing_page_response(get_da_user()), "Fix duplicate records"
        )

    def test_mhclg_user_cannot_see_fix_duplicate_records_tile(self):
        self.assertNotContains(
            self.get_landing_page_response(get_mhclg_user()), "Fix duplicate records"
        )

    def test_service_support_user_cannot_see_fix_duplicate_records_tile(self):
        self.assertNotContains(
            self.get_landing_page_response(get_service_support_user()),
            "Fix duplicate records",
        )

    def test_dev_user_can_always_see_fix_duplicate_records_tile(self):
        self.assertContains(
            self.get_landing_page_response(get_admin_user()), "Fix duplicate records"
        )


class TestFaviconRedirect(TestSessionTokenMixin, TestCase):
    def test_favicon_redirect(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(reverse("webapp:favicon_redirect"))

        target_url = "/static/gds/assets/images/favicon.ico"

        self.assertRedirects(
            response, target_url, status_code=302, fetch_redirect_response=False
        )
