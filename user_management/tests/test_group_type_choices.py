from accounts.enums import GroupType
from test_utils.base import BaseSimpleTestCase
from user_management.forms import AccessRequestFormGroupTypeStep


class AccessRequestGroupTypeChoicesTestCase(BaseSimpleTestCase):
    def test_browser_test_type_is_not_offered(self):
        form = AccessRequestFormGroupTypeStep()

        values = [value for value, label in form.fields["group_type"].choices]

        self.assertNotIn(GroupType.LOCAL_AUTHORITY_BROWSER_TEST, values)
        self.assertIn(GroupType.LOCAL_AUTHORITY, values)
