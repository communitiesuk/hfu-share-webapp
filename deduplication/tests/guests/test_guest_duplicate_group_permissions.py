from accounts.models import User
from deduplication.models import GuestDuplicateGroup
from deduplication.tests.factories import (
    GuestDuplicateGroupFactory,
)
from ontology.tests.base import MvPersonBaseTestCase


class TestGuestDuplicateGroupPermissionsTestCase(MvPersonBaseTestCase):
    def assert_get_for_user_returns(
        self, user: User, duplicate_groups: list[GuestDuplicateGroup]
    ):
        return self.assertQuerySetEqual(
            GuestDuplicateGroup.objects.get_for_user(user).order_by("pk"),
            sorted(duplicate_groups, key=lambda a: a.pk),
        )

    def setUp(self):
        super().setUp()
        self.ltla_one_a_duplicate_group = GuestDuplicateGroupFactory()
        self.ltla_one_a_duplicate_group.guests.set([self.ltla_one_a_person])
        self.ltla_one_a_duplicate_group.principal_record = None
        self.ltla_one_a_duplicate_group.save()

        self.ltla_one_b_duplicate_group = GuestDuplicateGroupFactory()
        self.ltla_one_b_duplicate_group.guests.set([self.ltla_one_b_person])
        self.ltla_one_b_duplicate_group.principal_record = self.ltla_one_b_person
        self.ltla_one_b_duplicate_group.save()

        self.utla_one_duplicate_group = GuestDuplicateGroupFactory()
        self.utla_one_duplicate_group.guests.set(
            [
                self.ltla_one_a_person,
                self.utla_one_but_missing_ltla_person,
            ]
        )
        self.utla_one_duplicate_group.principal_record = self.ltla_one_b_person
        self.utla_one_duplicate_group.save()

        self.da_main_duplicate_group = GuestDuplicateGroupFactory()
        self.da_main_duplicate_group.guests.set(
            [self.ltla_one_a_person, self.ltla_two_a_person]
        )
        self.da_main_duplicate_group.principal_record = (
            self.utla_one_but_missing_ltla_person
        )
        self.da_main_duplicate_group.save()

        self.da_main_da_other_duplicate_group = GuestDuplicateGroupFactory()
        self.da_main_da_other_duplicate_group.guests.set(
            [self.ltla_one_a_person, self.ltla_da_other_person]
        )
        self.da_main_da_other_duplicate_group.principal_record = (
            self.utla_one_but_missing_ltla_person
        )
        self.da_main_da_other_duplicate_group.save()

        self.ltla_one_a_duplicate_groups = [self.ltla_one_a_duplicate_group]
        self.ltla_one_b_duplicate_groups = [self.ltla_one_b_duplicate_group]

        self.utla_one_duplicate_groups = [
            self.ltla_one_a_duplicate_group,
            self.ltla_one_b_duplicate_group,
            self.utla_one_duplicate_group,
        ]

        self.da_main_duplicate_groups = [
            self.ltla_one_a_duplicate_group,
            self.ltla_one_b_duplicate_group,
            self.utla_one_duplicate_group,
            self.da_main_duplicate_group,
        ]

    def test_user_can_access_guest_duplicate_group_if_has_all_ltlas_of_guests(self):
        self.assert_get_for_user_returns(
            self.ltla_one_a_user, self.ltla_one_a_duplicate_groups
        )
        self.assert_get_for_user_returns(
            self.ltla_one_b_user, self.ltla_one_b_duplicate_groups
        )

    def test_user_can_access_guest_duplicate_group_if_has_all_utlas_of_guests(self):
        self.assert_get_for_user_returns(
            self.utla_one_user, self.utla_one_duplicate_groups
        )

    def test_user_can_access_guest_duplicate_group_if_has_all_das_of_guests(self):
        self.assert_get_for_user_returns(
            self.da_main_user, self.da_main_duplicate_groups
        )

    def test_user_cannot_access_guest_duplicate_group_if_missing_any_ltla_of_guests(
        self,
    ):
        self.assertNotIn(
            self.utla_one_duplicate_group,
            GuestDuplicateGroup.objects.get_for_user(self.ltla_one_a_user),
        )

    def test_user_cannot_access_guest_duplicate_group_if_missing_any_utla_of_guests(
        self,
    ):
        self.assertNotIn(
            self.da_main_duplicate_group,
            GuestDuplicateGroup.objects.get_for_user(self.utla_one_user),
        )

    def test_user_cannot_access_guest_duplicate_group_if_missing_any_da_of_guests(
        self,
    ):
        self.assertNotIn(
            self.da_main_da_other_duplicate_group,
            GuestDuplicateGroup.objects.get_for_user(self.da_main_user),
        )
