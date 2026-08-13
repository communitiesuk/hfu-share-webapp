from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.db import IntegrityError
from django.test import RequestFactory, TestCase

from accounts.authentication import Authentication
from accounts.models import User
from accounts.tests.factories import UserFactory

TENANT_ID = "11111111-1111-1111-1111-111111111111"
OBJECT_ID = "22222222-2222-2222-2222-222222222222"
OTHER_OBJECT_ID = "44444444-4444-4444-4444-444444444444"
EMAIL = "user@example.com"
FIRST_NAME = "Test"
LAST_NAME = "User"

ENTRA_AUTH = {"ALLOWED_TENANTS": [TENANT_ID]}


class LinkEntraIdentityTestCase(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/auth_callback")
        self.request.session = SessionStore()
        self.token = {
            "access_token": "access-token",
            "id_token_claims": {
                "tid": TENANT_ID,
                "oid": OBJECT_ID,
                "preferred_username": EMAIL,
            },
        }

        patcher = patch.object(
            Authentication,
            "_get_user_profile",
            return_value={
                "givenName": FIRST_NAME,
                "surname": LAST_NAME,
                "mail": EMAIL,
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def authenticate(self):
        with self.settings(ENTRA_AUTH=ENTRA_AUTH):
            return Authentication(self.request).authenticate(self.token)

    def test_attaches_the_identity_to_a_user_created_before_the_entra_fields(self):
        legacy_user = UserFactory(
            email=EMAIL, username=EMAIL, entra_oid=None, entra_tid=None
        )

        user = self.authenticate()

        self.assertEqual(user.pk, legacy_user.pk)
        legacy_user.refresh_from_db()
        self.assertEqual(str(legacy_user.entra_oid), OBJECT_ID)
        self.assertEqual(str(legacy_user.entra_tid), TENANT_ID)
        self.assertEqual(User.objects.count(), 1)

    def test_denies_access_when_the_email_belongs_to_another_entra_identity(self):
        existing_user = UserFactory(
            email=EMAIL, username=EMAIL, entra_oid=OTHER_OBJECT_ID, entra_tid=TENANT_ID
        )

        user = self.authenticate()

        self.assertIsInstance(user, AnonymousUser)
        existing_user.refresh_from_db()
        self.assertEqual(str(existing_user.entra_oid), OTHER_OBJECT_ID)
        self.assertEqual(User.objects.count(), 1)

    def test_recovers_the_account_after_its_entra_identity_is_cleared(self):
        existing_user = UserFactory(
            email=EMAIL,
            username="legacy-username",
            entra_oid=OTHER_OBJECT_ID,
            entra_tid=TENANT_ID,
            is_dev=True,
        )

        self.assertIsInstance(self.authenticate(), AnonymousUser)

        existing_user.entra_oid = None
        existing_user.entra_tid = None
        existing_user.save(update_fields=["entra_oid", "entra_tid"])

        user = self.authenticate()

        self.assertEqual(user.pk, existing_user.pk)
        self.assertEqual(str(user.entra_oid), OBJECT_ID)
        self.assertEqual(str(user.entra_tid), TENANT_ID)
        self.assertTrue(user.is_dev())
        self.assertEqual(User.objects.count(), 1)

    def test_matches_on_the_email_regardless_of_case(self):
        legacy_user = UserFactory(
            email=EMAIL.upper(), username=EMAIL.upper(), entra_oid=None, entra_tid=None
        )

        user = self.authenticate()

        self.assertEqual(user.pk, legacy_user.pk)
        self.assertEqual(User.objects.count(), 1)

    def test_creates_a_user_when_no_account_matches(self):
        user = self.authenticate()

        self.assertEqual(user.email, EMAIL)
        self.assertEqual(user.username, EMAIL)
        self.assertEqual(str(user.entra_oid), OBJECT_ID)
        self.assertEqual(User.objects.count(), 1)

    def test_updates_the_user_matched_on_the_entra_identity(self):
        UserFactory(
            email=EMAIL,
            username=EMAIL,
            entra_oid=OBJECT_ID,
            entra_tid=TENANT_ID,
            first_name="Stale",
        )

        user = self.authenticate()

        self.assertEqual(user.first_name, FIRST_NAME)
        self.assertEqual(User.objects.count(), 1)

    def test_denies_access_when_the_tenant_is_not_allowed(self):
        self.token["id_token_claims"]["tid"] = "33333333-3333-3333-3333-333333333333"

        user = self.authenticate()

        self.assertIsInstance(user, AnonymousUser)
        self.assertEqual(User.objects.count(), 0)

    @patch("accounts.authentication.User.objects.create_user")
    def test_denies_access_when_the_account_cannot_be_created(self, mock_create_user):
        mock_create_user.side_effect = IntegrityError(
            "duplicate key value violates unique constraint "
            '"accounts_user_username_key"'
        )

        user = self.authenticate()

        self.assertIsInstance(user, AnonymousUser)
        self.assertEqual(User.objects.count(), 0)
