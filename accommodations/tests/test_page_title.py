from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvUkPostcodeFactory,
)
from user_management.tests.base import get_admin_user


class AccommodationPageTitlesTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.accom_wo_space = MvAccommodationFactory(
            postcode=MvUkPostcodeFactory(postcode="AB1CD3"),
        )
        self.accom_w_space = MvAccommodationFactory(
            postcode=MvUkPostcodeFactory(postcode="AB1 CD3"),
        )
        self.accom_fewer_char = MvAccommodationFactory(
            postcode=MvUkPostcodeFactory(postcode="XYZ"),
        )
        self.accom_no_postcode = MvAccommodationFactory()

    def test_accommodation_detail_tab_titles(self):
        pages_and_titles = [
            (
                "accommodations:detail-overview",
                "Accommodations: AB1C, Overview - Share Homes for Ukraine data",
            ),
            (
                "accommodations:detail-actions",
                "Accommodations: AB1C, Actions - Share Homes for Ukraine data",
            ),
            (
                "accommodations:detail-linked-records",
                "Accommodations: AB1C, Linked records - Share Homes for Ukraine data",
            ),
            (
                "accommodations:detail-properties",
                "Accommodations: AB1C, Properties - Share Homes for Ukraine data",
            ),
            (
                "accommodations:detail-history",
                "Accommodations: AB1C, History - Share Homes for Ukraine data",
            ),
        ]
        user = get_admin_user()
        self.client.force_login(user)

        for view_name, expected_title in pages_and_titles:
            with self.subTest(view_name=view_name):
                response = self.client.get(
                    reverse(
                        view_name,
                        args=[self.accom_wo_space.pk],
                    )
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["TITLE"], expected_title)

    def test_accom_with_space_in_postcode(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.accom_w_space.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["TITLE"],
            "Accommodations: AB1C, Overview - Share Homes for Ukraine data",
        )

    def test_accom_with_truncated_postcode(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.accom_fewer_char.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["TITLE"],
            "Accommodations: XYZ, Overview - Share Homes for Ukraine data",
        )

    def test_accom_with_no_postcode(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-overview",
                args=[self.accom_no_postcode.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["TITLE"],
            "Accommodations: Overview - Share Homes for Ukraine data",
        )
