import http.client

from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from test_utils.base import BaseTestCase
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_early_adopter_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class DeduplicationSponsorSelectedViewTests(TestSessionTokenMixin, BaseTestCase):
    def test_page_title(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertEqual(
            response.context["TITLE"],
            "Fix duplicate records - Share Homes for Ukraine data",
        )

    def test_page_title_per_record_type(self):
        record_types_and_titles = [
            ("accommodations", "Fix duplicate accommodation records"),
            ("guests", "Fix duplicate guest records"),
            ("sponsors", "Fix duplicate sponsor records"),
        ]
        user = get_admin_user()
        self.client.force_login(user)

        for record_type, expected_title in record_types_and_titles:
            with self.subTest(record_type=record_type):
                response = self.client.get(
                    reverse(
                        f"deduplication:{record_type}:"
                        "select-and-review-records-manual-step",
                        kwargs={"step": "select-record"},
                    ),
                    follow=True,
                )
                self.assertEqual(
                    response.context["TITLE"],
                    f"{expected_title} - Share Homes for Ukraine data",
                )

    def test_dev_user_can_access_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_can_access_view(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_can_access_view(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertEqual(response.status_code, http.client.OK)

    def test_mhclg_user_can_access_view(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertEqual(response.status_code, http.client.OK)

    def test_ukvi_user_cannot_access_view(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_renders_review_list_with_correct_layout(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(reverse("deduplication:select-record-type"))

        self.assertContains(response, "Fix duplicate records")
        self.assertContains(response, "Select the type of record you want to fix")

        self.assertContains(response, "Accommodation")
        self.assertContains(response, "Guests")
        self.assertContains(response, "Sponsors and hosts")

        self.assertContains(
            response,
            "Continue to find records using filter and search, and deduplicate them.",
        )

        self.assertContains(
            response,
            '<button class="govuk-button"type="submit">Continue</button>',
            html=True,
        )

        self.assertContains(
            response,
            '<a class="govuk-button govuk-button--secondary" '
            'href="/landing-page">Cancel</a>',
            html=True,
        )

    def test_dev_user_can_see_all_options(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertContains(response, 'value="Accommodation"')
        self.assertContains(response, 'value="Guests"')
        self.assertContains(response, 'value="Sponsors and hosts"')

    def test_la_user_can_see_all_options(self):
        self.client.force_login(get_la_user())
        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertContains(response, 'value="Accommodation"')
        self.assertContains(response, 'value="Guests"')
        self.assertContains(response, 'value="Sponsors and hosts"')

    def test_la_ea_user_can_see_all_options(self):
        self.client.force_login(get_la_early_adopter_user())
        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertContains(response, 'value="Accommodation"')
        self.assertContains(response, 'value="Guests"')
        self.assertContains(response, 'value="Sponsors and hosts"')

    def test_da_user_can_see_all_options(self):
        self.client.force_login(get_da_user())
        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertContains(response, 'value="Accommodation"')
        self.assertContains(response, 'value="Guests"')
        self.assertContains(response, 'value="Sponsors and hosts"')

    def test_mhclg_user_can_see_all_options(self):
        self.client.force_login(get_mhclg_user())
        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertContains(response, 'value="Accommodation"')
        self.assertContains(response, 'value="Guests"')
        self.assertContains(response, 'value="Sponsors and hosts"')

    def test_service_support_user_can_see_all_options(self):
        self.client.force_login(get_service_support_user())
        response = self.client.get(reverse("deduplication:select-record-type"))
        self.assertContains(response, 'value="Accommodation"')
        self.assertContains(response, 'value="Guests"')
        self.assertContains(response, 'value="Sponsors and hosts"')
