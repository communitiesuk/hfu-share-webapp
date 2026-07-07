import http.client

from django.test import TestCase
from django.urls import reverse

from accounts.enums import GroupType
from accounts.models import AccessRequest
from accounts.tests.base import TestSessionTokenMixin
from accounts.tests.factories import AccessRequestFactory
from user_management.tests.base import get_la_user, get_user_with_no_access


class YourRequestPageTests(TestSessionTokenMixin, TestCase):
    def test_should_return_404_for_request_not_belonging_to_user(self):
        user = get_la_user()
        other_user = get_user_with_no_access()
        access_request = AccessRequestFactory(requester=other_user)

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_should_render_local_authority_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.PENDING,
            group_type=GroupType.LOCAL_AUTHORITY,
            da_group_type=None,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertNotContains(response, "Your request for access has been rejected")
        self.assertNotContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertContains(response, "Local Authority")
        self.assertNotContains(response, "User group")
        self.assertNotContains(response, "Choose level of permissions")
        self.assertNotContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertNotContains(response, "Reason for rejections")

    def test_should_render_da_central_group_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.PENDING,
            group_type=GroupType.DEVOLVED_ADMINISTRATION,
            da_group_type=AccessRequest.DaGroupType.CENTRAL_USER,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertNotContains(response, "Your request for access has been rejected")
        self.assertNotContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertNotContains(response, "Local Authority")
        self.assertContains(response, "User group")
        self.assertNotContains(response, "Choose level of permissions")
        self.assertContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertNotContains(response, "Reason for rejections")

    def test_should_render_da_local_authority_group_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.PENDING,
            group_type=GroupType.DEVOLVED_ADMINISTRATION,
            da_group_type=AccessRequest.DaGroupType.LOCAL_AUTHORITY,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertNotContains(response, "Your request for access has been rejected")
        self.assertNotContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertContains(response, "Local Authority")
        self.assertContains(response, "User group")
        self.assertNotContains(response, "Choose level of permissions")
        self.assertNotContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertNotContains(response, "Reason for rejections")

    def test_should_render_home_office_ops_team_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.PENDING,
            group_type=GroupType.HOME_OFFICE,
            da_group_type=None,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertNotContains(response, "Your request for access has been rejected")
        self.assertNotContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertNotContains(response, "Local Authority")
        self.assertContains(response, "User group")
        self.assertNotContains(response, "Choose level of permissions")
        self.assertNotContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertNotContains(response, "Reason for rejections")

    def test_should_render_mhclg_ops_team_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.PENDING,
            group_type=GroupType.MHCLG,
            da_group_type=None,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertNotContains(response, "Your request for access has been rejected")
        self.assertNotContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertNotContains(response, "Local Authority")
        self.assertNotContains(response, "User group")
        self.assertContains(response, "Choose level of permissions")
        self.assertNotContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertNotContains(response, "Reason for rejections")

    def test_should_render_service_support_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.PENDING,
            group_type=GroupType.SERVICE_SUPPORT,
            da_group_type=None,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertNotContains(response, "Your request for access has been rejected")
        self.assertNotContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertNotContains(response, "Local Authority")
        self.assertNotContains(response, "User group")
        self.assertContains(response, "Choose level of permissions")
        self.assertNotContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertNotContains(response, "Reason for rejections")

    def test_should_render_rejected_local_authority_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.REJECTED,
            group_type=GroupType.LOCAL_AUTHORITY,
            da_group_type=None,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertContains(response, "Your request for access has been rejected")
        self.assertNotContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertContains(response, "Local Authority")
        self.assertNotContains(response, "User group")
        self.assertNotContains(response, "Choose level of permissions")
        self.assertNotContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertContains(response, "Reason for rejections")

    def test_should_render_rejected_da_central_group_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.REJECTED,
            group_type=GroupType.DEVOLVED_ADMINISTRATION,
            da_group_type=AccessRequest.DaGroupType.CENTRAL_USER,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertContains(response, "Your request for access has been rejected")
        self.assertNotContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertNotContains(response, "Local Authority")
        self.assertContains(response, "User group")
        self.assertNotContains(response, "Choose level of permissions")
        self.assertContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertContains(response, "Reason for rejections")

    def test_should_render_rejected_da_local_authority_group_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.REJECTED,
            group_type=GroupType.DEVOLVED_ADMINISTRATION,
            da_group_type=AccessRequest.DaGroupType.LOCAL_AUTHORITY,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertContains(response, "Your request for access has been rejected")
        self.assertNotContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertContains(response, "Local Authority")
        self.assertContains(response, "User group")
        self.assertNotContains(response, "Choose level of permissions")
        self.assertNotContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertContains(response, "Reason for rejections")

    def test_should_render_rejected_home_office_ops_team_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.REJECTED,
            group_type=GroupType.HOME_OFFICE,
            da_group_type=None,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertContains(response, "Your request for access has been rejected")
        self.assertNotContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertNotContains(response, "Local Authority")
        self.assertContains(response, "User group")
        self.assertNotContains(response, "Choose level of permissions")
        self.assertNotContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertContains(response, "Reason for rejections")

    def test_should_render_rejected_mhclg_ops_team_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.REJECTED,
            group_type=GroupType.MHCLG,
            da_group_type=None,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertContains(response, "Your request for access has been rejected")
        self.assertNotContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertNotContains(response, "Local Authority")
        self.assertNotContains(response, "User group")
        self.assertContains(response, "Choose level of permissions")
        self.assertNotContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertContains(response, "Reason for rejections")

    def test_should_render_rejected_service_support_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.REJECTED,
            group_type=GroupType.SERVICE_SUPPORT,
            da_group_type=None,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertContains(response, "Your request for access has been rejected")
        self.assertNotContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertNotContains(response, "Local Authority")
        self.assertNotContains(response, "User group")
        self.assertContains(response, "Choose level of permissions")
        self.assertNotContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertContains(response, "Reason for rejections")

    def test_should_render_approved_local_authority_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.APPROVED,
            group_type=GroupType.LOCAL_AUTHORITY,
            da_group_type=None,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertNotContains(response, "Your request for access has been rejected")
        self.assertContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertContains(response, "Local Authority")
        self.assertNotContains(response, "User group")
        self.assertNotContains(response, "Choose level of permissions")
        self.assertNotContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertNotContains(response, "Reason for rejections")

    def test_should_render_approved_da_central_group_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.APPROVED,
            group_type=GroupType.DEVOLVED_ADMINISTRATION,
            da_group_type=AccessRequest.DaGroupType.CENTRAL_USER,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertNotContains(response, "Your request for access has been rejected")
        self.assertContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertNotContains(response, "Local Authority")
        self.assertContains(response, "User group")
        self.assertNotContains(response, "Choose level of permissions")
        self.assertContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertNotContains(response, "Reason for rejections")

    def test_should_render_approved_da_local_authority_group_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.APPROVED,
            group_type=GroupType.DEVOLVED_ADMINISTRATION,
            da_group_type=AccessRequest.DaGroupType.LOCAL_AUTHORITY,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertNotContains(response, "Your request for access has been rejected")
        self.assertContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertContains(response, "Local Authority")
        self.assertContains(response, "User group")
        self.assertNotContains(response, "Choose level of permissions")
        self.assertNotContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertNotContains(response, "Reason for rejections")

    def test_should_render_approved_home_office_ops_team_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.APPROVED,
            group_type=GroupType.HOME_OFFICE,
            da_group_type=None,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertNotContains(response, "Your request for access has been rejected")
        self.assertContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertNotContains(response, "Local Authority")
        self.assertContains(response, "User group")
        self.assertNotContains(response, "Choose level of permissions")
        self.assertNotContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertNotContains(response, "Reason for rejections")

    def test_should_render_approved_mhclg_ops_team_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.APPROVED,
            group_type=GroupType.MHCLG,
            da_group_type=None,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertNotContains(response, "Your request for access has been rejected")
        self.assertContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertNotContains(response, "Local Authority")
        self.assertNotContains(response, "User group")
        self.assertContains(response, "Choose level of permissions")
        self.assertNotContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertNotContains(response, "Reason for rejections")

    def test_should_render_approved_service_support_request(self):
        user = get_la_user()
        access_request = AccessRequestFactory(
            requester=user,
            status=AccessRequest.Status.APPROVED,
            group_type=GroupType.SERVICE_SUPPORT,
            da_group_type=None,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "user_management:access-request-your-request", args=[access_request.pk]
            )
        )

        self.assertNotContains(response, "Your request for access has been rejected")
        self.assertContains(response, "Your request for access has been approved")

        self.assertContains(response, "Request date")
        self.assertContains(response, "Name")
        self.assertNotContains(response, "Local Authority")
        self.assertNotContains(response, "User group")
        self.assertContains(response, "Choose level of permissions")
        self.assertNotContains(response, "Country group")
        self.assertContains(response, "Tell us why access is needed")
        self.assertNotContains(response, "Reason for rejections")
