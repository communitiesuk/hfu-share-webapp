from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.views import SelectAndReviewRecordsStep
from ontology.tests.factories import MvAccommodationFactory, MvUkPostcodeFactory
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class DeduplicationAccommodationListViewTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.accommodation = MvAccommodationFactory(
            full_address="A Test Somerset LTLA Address",
            ltla_name="ltla_somerset",
            utla_name="utla_somerset",
            postcode=MvUkPostcodeFactory(postcode="ABC123"),
            is_principal=True,
        )

        self.non_principal_accommodation = MvAccommodationFactory(
            full_address="A Test Non principal Address",
            ltla_name="ltla_somerset",
            utla_name="utla_somerset",
            postcode=MvUkPostcodeFactory(postcode="CBA321"),
            is_principal=False,
        )

    def test_redirects_to_list_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual",
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "/review-potential-duplicate-records-manual"
            "/accommodations"
            "/deduplicate"
            "/select-record/",
        )

    def test_renders_accommodation_list_with_correct_layout(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            )
        )

        self.assertContains(response, "Fix duplicate accommodation records")

        self.assertContains(response, "Select a record to review and deduplicate")

        self.assertContains(response, "Address")
        self.assertContains(response, "Postcode")
        self.assertContains(response, "Lower tier LA")
        self.assertContains(response, "Upper tier LA")

    def test_renders_accommodation_list_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            ),
            {"page": 1},
        )

        response_list = sorted(
            response.context["object_list"],
            key=lambda obj: obj.full_address,
        )
        self.assertEqual(response_list[0].full_address, self.accommodation.full_address)
        self.assertEqual(
            response_list[0].postcode.postcode_formatted,
            self.accommodation.postcode.postcode_formatted,
        )
        self.assertEqual(response_list[0].ltla_name, self.accommodation.ltla_name)
        self.assertEqual(response_list[0].utla_name, self.accommodation.utla_name)

    def test_does_not_render_non_principal_accommodation(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "deduplication:accommodations:select-and-review-records-manual-step",
                kwargs={
                    "step": SelectAndReviewRecordsStep.SELECT_RECORD,
                },
            )
        )

        self.assertNotContains(response, self.non_principal_accommodation.full_address)


class DeduplicationAccommodationWizardAccessTests(TestSessionTokenMixin, TestCase):
    def _follow_wizard_entry(self, user):
        self.client.force_login(user)
        return self.client.get(
            reverse("deduplication:accommodations:select-and-review-records-manual"),
            follow=True,
        )

    def _get_wizard_entry(self, user):
        self.client.force_login(user)
        return self.client.get(
            reverse("deduplication:accommodations:select-and-review-records-manual")
        )

    def test_dev_user_can_access_accommodation_wizard(self):
        response = self._follow_wizard_entry(get_admin_user())
        self.assertEqual(response.status_code, 200)

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=False)
    def test_flag_off_dev_user_can_still_access_accommodation_wizard(self):
        response = self._follow_wizard_entry(get_admin_user())
        self.assertEqual(response.status_code, 200)

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=True)
    def test_flag_on_la_user_can_access_accommodation_wizard(self):
        response = self._follow_wizard_entry(get_la_user())
        self.assertEqual(response.status_code, 200)

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=False)
    def test_flag_off_la_user_cannot_access_accommodation_wizard(self):
        response = self._get_wizard_entry(get_la_user())
        self.assertEqual(response.status_code, 403)

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=True)
    def test_flag_on_da_user_can_access_accommodation_wizard(self):
        response = self._follow_wizard_entry(get_da_user())
        self.assertEqual(response.status_code, 200)

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=True)
    def test_flag_on_mhclg_user_can_access_accommodation_wizard(self):
        response = self._follow_wizard_entry(get_mhclg_user())
        self.assertEqual(response.status_code, 200)

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=False)
    def test_flag_off_mhclg_user_cannot_access_accommodation_wizard(self):
        response = self._get_wizard_entry(get_mhclg_user())
        self.assertEqual(response.status_code, 403)

    @override_settings(FIX_DUPLICATE_RECORDS_ENABLED=True)
    def test_flag_on_service_support_user_can_access_accommodation_wizard(self):
        response = self._follow_wizard_entry(get_service_support_user())
        self.assertEqual(response.status_code, 200)

    def test_ukvi_user_cannot_access_accommodation_wizard(self):
        user = get_ukvi_user()
        response = self._get_wizard_entry(user)
        self.assertEqual(response.status_code, 404)
