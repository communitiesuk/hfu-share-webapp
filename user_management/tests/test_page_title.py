import http.client

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from accounts.tests.factories import AccessRequestFactory, GroupFactory, UserFactory
from user_management.tests.base import (
    get_admin_user,
)


class AccessRequestsDetailPageTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.service_name = settings.SERVICE_NAME

        self.requester = UserFactory(
            email="test1.user@example.com",
            first_name="Test1",
            last_name="User",
        )

        self.requester_no_last_name = UserFactory(
            email="test2.user@example.com",
            first_name="Test2",
            last_name="",
        )

        self.requester_no_names = UserFactory(
            email="test3.user@example.com",
            first_name="",
            last_name="",
        )

    def test_access_request_tab_title(self):
        access_request = AccessRequestFactory(requester=self.requester)
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "user_management:access-request-details",
                kwargs={"pk": access_request.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["TITLE"],
            f"Review access request: TU - {self.service_name}",
        )

    def test_access_request_tab_title_with_no_last_name(self):
        access_request = AccessRequestFactory(requester=self.requester_no_last_name)
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "user_management:access-request-details",
                kwargs={"pk": access_request.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["TITLE"], f"Review access request: T - {self.service_name}"
        )

    def test_access_request_tab_title_with_no_names(self):
        access_request = AccessRequestFactory(requester=self.requester_no_names)
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "user_management:access-request-details",
                kwargs={"pk": access_request.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["TITLE"], f"Review access request - {self.service_name}"
        )


class UserDetailPageTitleTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.service_name = settings.SERVICE_NAME

        self.user = UserFactory(
            id="999",
            first_name="Test",
            last_name="User",
            username="testuser",
            email="test@example.com",
        )

        self.user_no_surname = UserFactory(
            id="1000",
            first_name=None,
            last_name="User",
            username="nosurname",
            email="nosurname@example.com",
        )

        self.user_email_only = UserFactory(
            id="1001",
            first_name=None,
            last_name=None,
            username="emailonly",
            email="email@example.com",
        )

    def test_user_detail_page_title_with_names(self):
        self.client.force_login(get_admin_user())
        url = reverse("user_management:user-details", kwargs={"pk": self.user.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(
            response.context["TITLE"], f"User account: TU - {self.service_name}"
        )

    def test_user_detail_page_title_surname_only(self):
        self.client.force_login(get_admin_user())
        url = reverse(
            "user_management:user-details", kwargs={"pk": self.user_no_surname.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(
            response.context["TITLE"], f"User account: U - {self.service_name}"
        )

    def test_user_detail_page_title_email_only(self):
        self.client.force_login(get_admin_user())
        url = reverse(
            "user_management:user-details", kwargs={"pk": self.user_email_only.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(
            response.context["TITLE"], f"User account: ema - {self.service_name}"
        )


class GroupDetailPageTitleTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.service_name = settings.SERVICE_NAME
        self.group_to_view = GroupFactory(name="test_group")

    def test_group_detail_page_title(self):
        self.client.force_login(get_admin_user())
        url = reverse(
            "user_management:group-details", kwargs={"pk": self.group_to_view.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(
            response.context["TITLE"],
            f"Group details: test_group - {self.service_name}",
        )
