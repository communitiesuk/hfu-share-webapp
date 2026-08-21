from typing import cast

from django import forms
from django.test import TestCase

from accommodation_requests.forms import MoveGuestsFormSelectLocalAuthorityStep
from accounts.enums import BROWSER_TEST_LTLA_NAMES, GroupType
from accounts.tests.factories import GroupFactory, UserFactory


class ReassignLaDropdownTestCase(TestCase):
    def setUp(self):
        self.real_la_group = GroupFactory(
            groupinfo__ltla_name="Realshire",
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY,
            groupinfo__da_name="England",
        )
        self.browser_test_group = GroupFactory(
            name="ltla_hobbiton_browser_test",
            groupinfo__ltla_name=BROWSER_TEST_LTLA_NAMES[0],
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY_BROWSER_TEST,
            groupinfo__da_name="England",
        )

    def _dropdown_ltla_names(self, user) -> set[str]:
        form = MoveGuestsFormSelectLocalAuthorityStep(country="England", user=user)
        field = cast(forms.ModelChoiceField, form.fields["local_authority"])
        return {group_info.ltla_name for group_info in field.queryset or []}

    def test_normal_la_user_does_not_see_browser_test_las(self):
        user = UserFactory()
        user.groups.set([self.real_la_group])

        ltla_names = self._dropdown_ltla_names(user)
        self.assertIn("Realshire", ltla_names)
        self.assertNotIn(BROWSER_TEST_LTLA_NAMES[0], ltla_names)

    def test_browser_test_user_sees_real_and_browser_test_las(self):
        user = UserFactory()
        user.groups.set([self.browser_test_group])

        ltla_names = self._dropdown_ltla_names(user)
        self.assertIn("Realshire", ltla_names)
        self.assertIn(BROWSER_TEST_LTLA_NAMES[0], ltla_names)

    def test_no_user_defaults_to_real_las_only(self):
        ltla_names = self._dropdown_ltla_names(None)
        self.assertIn("Realshire", ltla_names)
        self.assertNotIn(BROWSER_TEST_LTLA_NAMES[0], ltla_names)
