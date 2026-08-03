from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase

from accounts.admin import CustomUserAdmin
from accounts.models import User
from accounts.tests.factories import UserFactory


class ClearEntraIdentityActionTest(TestCase):
    def setUp(self):
        self.admin = CustomUserAdmin(User, AdminSite())
        self.request = RequestFactory().get("/admin/accounts/user/")
        self.request.session = {}
        self.request._messages = FallbackStorage(self.request)

    def test_clears_the_entra_fields_for_selected_users(self):
        user = UserFactory()

        self.admin.clear_entra_identity(self.request, User.objects.filter(pk=user.pk))

        user.refresh_from_db()
        self.assertIsNone(user.entra_oid)
        self.assertIsNone(user.entra_tid)
