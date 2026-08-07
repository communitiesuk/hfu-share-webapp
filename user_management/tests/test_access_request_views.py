import http.client

from django.test import TestCase
from django.urls import reverse

from accounts.enums import GroupType
from accounts.models import AccessRequest
from accounts.tests.base import TestSessionTokenMixin
from accounts.tests.factories import AccessRequestFactory, GroupInfoFactory
from user_management.tests.base import (
    get_admin_user,
    get_la_user,
    get_user_with_no_access,
)

WIZARD_STEP_FIELD = "access_request_form_wizard-current_step"


class AccessRequestsListViewTestCase(TestSessionTokenMixin, TestCase):
    def test_access_denied_to_non_admin_users(self):
        url = reverse("user_management:access-requests")
        self.client.force_login(get_la_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_access_allowed_to_admin_users(self):
        url = reverse("user_management:access-requests")
        self.client.force_login(get_admin_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.OK)


class AccessRequestsDetailPageTestCase(TestSessionTokenMixin, TestCase):
    def test_access_denied_to_non_admin_users(self):
        access_request = AccessRequestFactory()
        url = reverse(
            "user_management:access-request-details", kwargs={"pk": access_request.pk}
        )
        self.client.force_login(get_la_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_access_allowed_to_admin_users(self):
        access_request = AccessRequestFactory()
        url = reverse(
            "user_management:access-request-details", kwargs={"pk": access_request.pk}
        )
        self.client.force_login(get_admin_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.OK)


class AccessRequestsFormTestCase(TestSessionTokenMixin, TestCase):
    def test_access_allowed_to_non_admin_users(self):
        url = reverse("user-management:access-request-form")
        self.client.force_login(get_la_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.OK)

    def test_access_allowed_to_user_with_no_groups(self):
        url = reverse("user-management:access-request-form")
        self.client.force_login(get_user_with_no_access())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.OK)

    def test_confirmation_page_access_allowed_to_non_admin_users(self):
        url = reverse("user-management:access-request-confirmation")
        self.client.force_login(get_la_user())
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.client.OK)


class AccessRequestFormWizardDevolvedAdministrationContentTestCase(
    TestSessionTokenMixin, TestCase
):
    def setUp(self):
        super().setUp()
        self.url = reverse("user-management:access-request-form")
        self.client.force_login(get_user_with_no_access())
        self.da_group_info = GroupInfoFactory(
            group_type=GroupType.DEVOLVED_ADMINISTRATION,
            da_name="Northern Ireland",
        )
        self.la_group_info = GroupInfoFactory(
            group_type=GroupType.LOCAL_AUTHORITY,
            ltla_name="Test LTLA",
            is_utla=False,
        )

    def post_step(self, current_step, data):
        return self.client.post(self.url, {WIZARD_STEP_FIELD: current_step, **data})

    def test_da_group_type_step_shows_select_user_group_content(self):
        response = self.post_step(
            "group_type", {"group_type-group_type": GroupType.DEVOLVED_ADMINISTRATION}
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "Select user group")
        self.assertContains(response, "Central user")
        self.assertContains(response, "Local authority")

    def test_devolved_administration_step_shows_central_user_content(self):
        self.post_step(
            "group_type", {"group_type-group_type": GroupType.DEVOLVED_ADMINISTRATION}
        )
        response = self.post_step(
            "da_group_type",
            {"da_group_type-da_group_type": AccessRequest.DaGroupType.CENTRAL_USER},
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "Devolved administration: central user")
        self.assertContains(response, "Select a devolved administration")
        self.assertContains(response, "Northern Ireland")
        self.assertContains(response, "Scotland")
        self.assertContains(response, "Wales")

    def test_local_authority_step_heading_via_devolved_administration_route(self):
        self.post_step(
            "group_type", {"group_type-group_type": GroupType.DEVOLVED_ADMINISTRATION}
        )
        response = self.post_step(
            "da_group_type",
            {
                "da_group_type-da_group_type": (
                    AccessRequest.DaGroupType.LOCAL_AUTHORITY
                )
            },
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "Devolved administration: local authority")
        self.assertContains(
            response, "Select an upper tier or lower tier local authority"
        )
        self.assertContains(
            response,
            "You can only select one. If you need to select more you will need to "
            "start a new data access request for each area.",
        )
        self.assertContains(
            response,
            "If you are from a unitary authority you can select either LTLA or "
            "UTLA for the relevant area you need to access to.",
        )
        self.assertContains(
            response,
            "UTLA users only need to select their relevant UTLA. They will also "
            "get access to the LTLA data for that area, they do not need to submit "
            "another data access request for LTLA data.",
        )

    def test_local_authority_step_heading_via_direct_route(self):
        response = self.post_step(
            "group_type", {"group_type-group_type": GroupType.LOCAL_AUTHORITY}
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "Local authority")
        self.assertContains(
            response,
            "You can only select one. If you need to select more you will need "
            "to start a new data access request for each area.",
        )
        self.assertContains(
            response,
            "If you are from a unitary authority you can select either LTLA or "
            "UTLA for the relevant area you need to access to.",
        )
        self.assertContains(
            response,
            "UTLA users only need to select their relevant UTLA. They will also "
            "get access to the LTLA data for that area, they do not need to submit "
            "another data access request for LTLA data.",
        )

    def test_review_step_renders_correctly_for_central_user_view(self):
        self.post_step(
            "group_type", {"group_type-group_type": GroupType.DEVOLVED_ADMINISTRATION}
        )
        self.post_step(
            "da_group_type",
            {"da_group_type-da_group_type": AccessRequest.DaGroupType.CENTRAL_USER},
        )
        self.post_step(
            "devolved_administration",
            {
                "devolved_administration-devolved_administration": (
                    self.da_group_info.pk
                )
            },
        )
        response = self.post_step(
            "justification", {"justification-justification": "Testing"}
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "Name")
        self.assertContains(response, "User group")
        self.assertContains(response, "Devolved administration - central user")
        self.assertContains(response, "Devolved administration")
        self.assertContains(response, "Northern Ireland")
        self.assertContains(response, "Tell us why you need access")
        self.assertContains(response, "Testing")

    def test_review_step_renders_correctly_for_da_local_authority_view(self):
        self.post_step(
            "group_type", {"group_type-group_type": GroupType.DEVOLVED_ADMINISTRATION}
        )
        self.post_step(
            "da_group_type",
            {"da_group_type-da_group_type": AccessRequest.DaGroupType.LOCAL_AUTHORITY},
        )
        self.post_step(
            "local_authority",
            {"local_authority-local_authority": self.la_group_info.pk},
        )
        response = self.post_step(
            "justification", {"justification-justification": "Testing"}
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "Name")
        self.assertContains(response, "User group")
        self.assertContains(response, "Devolved administration - local authority")
        self.assertContains(response, "Devolved administration")
        self.assertContains(response, "Test LTLA")
        self.assertContains(response, "Tell us why you need access")
        self.assertContains(response, "Testing")

    def test_review_step_keeps_local_authority_label_for_direct_route(self):
        self.post_step(
            "group_type", {"group_type-group_type": GroupType.LOCAL_AUTHORITY}
        )
        self.post_step(
            "local_authority",
            {"local_authority-local_authority": self.la_group_info.pk},
        )
        response = self.post_step(
            "justification", {"justification-justification": "Testing"}
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "Name")
        self.assertContains(response, "User group")
        self.assertContains(response, "Local authority")
        self.assertContains(response, "Tell us why you need access")
        self.assertContains(response, "Testing")

    def test_confirmation_page_shows_the_name_of_the_requested_group(self):
        self.post_step(
            "group_type", {"group_type-group_type": GroupType.DEVOLVED_ADMINISTRATION}
        )
        self.post_step(
            "da_group_type",
            {"da_group_type-da_group_type": AccessRequest.DaGroupType.CENTRAL_USER},
        )
        self.post_step(
            "devolved_administration",
            {
                "devolved_administration-devolved_administration": (
                    self.da_group_info.pk
                )
            },
        )
        self.post_step("justification", {"justification-justification": "Testing"})
        response = self.post_step("review", {})
        self.assertEqual(response.status_code, http.client.FOUND)

        response = self.client.get(
            reverse("user-management:access-request-confirmation")
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(
            response,
            "Your request for access to data for Northern Ireland is submitted.",
            html=True,
        )
        self.assertContains(
            response, "Check your homepage for updates about your request"
        )


class AccessRequestIntroViewTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("user-management:access-request-intro")

    def test_notification_shows_when_user_has_groups(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(
            response, "You already have access to Homes for Ukraine data"
        )

    def test_no_notification_when_user_has_no_groups(self):
        user = get_user_with_no_access()
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertNotContains(
            response, "You already have access to Homes for Ukraine data"
        )
