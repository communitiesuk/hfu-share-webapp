from accounts.models import User
from ontology.models import PersonMasterRecord
from ontology.tests.base import PersonMasterRecordBaseTestCase


class PersonMasterRecordPermissionsTest(PersonMasterRecordBaseTestCase):
    def assert_get_for_user_returns(
        self, user: User, person_master_records: list[PersonMasterRecord]
    ):
        return self.assertQuerySetEqual(
            PersonMasterRecord.objects.get_for_user(user).order_by("record_id"),
            sorted(list({str(obj) for obj in person_master_records})),
            transform=str,
        )

    def test_get_for_user_returns_all_pmrs_for_dev_user(self):
        self.assert_get_for_user_returns(
            self.ltla_user_dev, self.all_person_master_records
        )

    def test_get_for_user_returns_only_pmrs_matching_groups_single_ltla(self):
        """
        Tests that get_for_user only returns suggested duplicates
        if the linked person records are all in the user's ltla
        single ltla case
        """
        self.assert_get_for_user_returns(
            self.ltla_one_a_user, self.ltla_one_a_person_master_records
        )

    def test_get_for_user_returns_only_pmrs_matching_groups_multi_ltla(self):
        """
        Tests that get_for_user only returns suggested duplicates
        if the linked person records are all in the user's ltla
        multi ltla case
        """
        self.assert_get_for_user_returns(
            self.ltla_one_a_ltla_one_b_user,
            self.ltla_one_a_person_master_records
            + self.ltla_one_b_person_master_records
            + self.mixed_ltla_one_a_ltla_one_b_person_master_records,
        )

    def test_get_for_user_returns_only_pmrs_matching_groups_single_utla(self):
        """
        Tests that get_for_user only returns suggested duplicates
        if the linked person records are all in the user's utla
        single utla case
        """
        self.assert_get_for_user_returns(
            self.utla_one_user, self.utla_one_person_master_records
        )

    def test_get_for_user_returns_only_pmrs_matching_groups_multi_utla(self):
        """
        Tests that get_for_user only returns suggested duplicates
        if the linked person records are all in the user's utla
        multi utla case
        """
        self.assert_get_for_user_returns(
            self.multi_utla_user,
            self.utla_one_person_master_records + self.utla_two_person_master_records,
        )

        self.multi_utla_user.groups.set([self.utla_one_group])

        self.assert_get_for_user_returns(
            self.multi_utla_user, self.utla_one_person_master_records
        )

    def test_get_for_user_returns_only_pmrs_matching_groups_single_ltla_and_utla(self):
        """
        Tests that get_for_user only returns suggested duplicates
        if the linked person records are all in the user's ltla
        and utlas
        """
        self.ltla_one_a_user.groups.set([self.ltla_one_a_group, self.utla_two_group])
        self.assert_get_for_user_returns(
            self.ltla_one_a_user,
            self.ltla_one_a_person_master_records + self.utla_two_person_master_records,
        )
