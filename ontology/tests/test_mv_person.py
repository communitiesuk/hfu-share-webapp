from ontology.tests.base import LocalAuthorityBaseTestCaseMixin
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvGroupFactory,
    MvPersonFactory,
)


class MvPersonTest(LocalAuthorityBaseTestCaseMixin):
    def test_person_with_correct_old_group_foreign_key_works(self):
        MvGroupFactory(id="Group-123")
        person = MvPersonFactory(
            old_group_id="Group-123",
        )

        # Doesn't raise error
        self.assertEqual(person.old_group_id, "Group-123")

    def test_old_group_with_nonexistent_value_doesnt_raise_error(self):
        # Won't raise Key constraint exception
        person = MvPersonFactory(old_group_id="nonexistent_old_group_id")

        self.assertEqual(person.old_group_id, "nonexistent_old_group_id")

    def test_person_with_correct_ar_key_works(self):
        MvAccommodationRequestFactory(id="AR-123")
        person = MvPersonFactory(accommodation_request_id="AR-123")

        # Doesn't raise error
        self.assertEqual(person.accommodation_request_id, "AR-123")

    def test_accommodation_request_id_with_nonexistent_value_wont_error(self):
        # Won't raise Key constraint exception
        person = MvPersonFactory(
            accommodation_request=None,  # prevent factory from auto-creating AR
            accommodation_request_id="nonexistent_id",
        )

        self.assertEqual(person.accommodation_request_id, "nonexistent_id")

    def test_get_accommodation_request_returns_ar(self):
        ar = MvAccommodationRequestFactory(id="AR-123")
        person = MvPersonFactory(accommodation_request=ar)

        self.assertEqual(person.get_accommodation_request(), ar)

    def test_get_accommodation_request_returns_none_if_no_ar_id(self):
        person = MvPersonFactory(accommodation_request=None)

        self.assertIsNone(person.get_accommodation_request())

    def test_get_accommodation_request_returns_none_if_broken_ar_id(self):
        person = MvPersonFactory(
            accommodation_request=None,  # prevent factory from auto-creating AR
            accommodation_request_id="nonexistent_id",
        )

        self.assertIsNone(person.get_accommodation_request())

    def test_ar_request_restrict_for_user_fetchs_ar_from_correct_la(self):
        ar = MvAccommodationRequestFactory(
            id="AR-123",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )

        person = MvPersonFactory(accommodation_request=ar)

        restricted_ar = person.accommodation_request_restrict_for_user(
            self.ltla_one_a_user
        )

        self.assertEqual(restricted_ar, ar)

    def test_ar_restrict_for_user_wont_fetch_record_from_different_la(self):
        ar = MvAccommodationRequestFactory(
            id="AR-123",
            ltla_name=[self.ltla_two_a_name],
            utla_name=[self.utla_two_name],
        )

        person = MvPersonFactory(accommodation_request=ar)

        restricted_ar = person.accommodation_request_restrict_for_user(
            self.ltla_one_a_user
        )

        self.assertEqual(restricted_ar, None)

    def test_ar_restrict_for_user_with_broken_ar_id_wont_500(self):
        person = MvPersonFactory(
            accommodation_request=None, accommodation_request_id="nonexistent_id"
        )

        restricted_ar = person.accommodation_request_restrict_for_user(
            self.ltla_user_dev
        )

        self.assertEqual(restricted_ar, None)

    def test_get_page_title_without_ar_wont_500(self):
        person = MvPersonFactory(
            first_name="John",
            last_name="Doe",
            accommodation_request=None,  # prevent factory from auto-creating AR
            accommodation_request_id="nonexistent_id",
        )

        title = person.get_page_title()

        self.assertEqual(title, "John Doe")

    def test_display_link_data_creates_correct_title(self):
        person = MvPersonFactory(
            first_name="First", last_name="Last", email=["abc@example.com"]
        )

        data = person.display_link_data(None, None)

        self.assertEqual(data.title, "First Last (abc@example.com)")

    def test_display_link_data_with_email_but_no_name_creates_correct_title(self):
        person = MvPersonFactory(email=["abc@example.com"])

        data = person.display_link_data(None, None)

        self.assertEqual(data.title, "(abc@example.com)")

    def test_mv_person_factory_does_not_create_archived_record(self):
        sponsor = MvPersonFactory()

        self.assertFalse(sponsor.is_archived)
        self.assertIsNone(sponsor.archived_at)
