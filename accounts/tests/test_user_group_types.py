from typing import cast

from django.contrib.auth.models import Group

from accounts.enums import GroupType
from accounts.models import User
from accounts.tests.factories import GroupFactory, UserFactory
from test_utils.base import BaseTestCase


class UserGroupTypesTestCase(BaseTestCase):
    def _user_with_type(self, group_type: GroupType) -> User:
        user = cast(User, UserFactory())
        group = cast(Group, GroupFactory(groupinfo__group_type=group_type))
        user.groups.set([group])
        return user

    def test_get_group_types_returns_user_group_types(self):
        user = self._user_with_type(GroupType.MHCLG)

        self.assertEqual(user.get_group_types(), {GroupType.MHCLG})

    def test_browser_test_type_counts_as_local_authority(self):
        user = self._user_with_type(GroupType.LOCAL_AUTHORITY_BROWSER_TEST)

        self.assertEqual(
            user.get_group_types(),
            {GroupType.LOCAL_AUTHORITY_BROWSER_TEST, GroupType.LOCAL_AUTHORITY},
        )

    def test_plain_local_authority_type_is_unchanged(self):
        user = self._user_with_type(GroupType.LOCAL_AUTHORITY)

        self.assertEqual(user.get_group_types(), {GroupType.LOCAL_AUTHORITY})

    def test_is_la_is_true_for_browser_test_user(self):
        user = self._user_with_type(GroupType.LOCAL_AUTHORITY_BROWSER_TEST)

        self.assertTrue(user.is_la())

    def test_is_in_group_types_accepts_local_authority_for_browser_test_user(self):
        user = self._user_with_type(GroupType.LOCAL_AUTHORITY_BROWSER_TEST)

        self.assertTrue(user.is_in_group_types([GroupType.LOCAL_AUTHORITY]))
        self.assertFalse(user.is_in_group_types([GroupType.MHCLG]))
