from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import MvVolunteer
from ontology.tests.factories import MvVolunteerFactory
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class DeduplicationSponsorListViewTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.sponsor = MvVolunteerFactory(
            first_name="[A firstname",
            last_name="testlastname",
            sex="Female",
            date_of_birth=datetime(1999, 1, 1, tzinfo=timezone.utc),
            email="test@example.com",
            phone_number=["01134960698"],
            residential_postcodes=["OX1 1OX"],
            is_eoi=False,
            created_date=datetime(2010, 12, 12, tzinfo=timezone.utc),
            is_principal=True,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

        self.non_principal_sponsor = MvVolunteerFactory(
            first_name="[afirstname",
            last_name="duplicate",
            is_principal=False,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

    def test_renders_sponsor_list_with_correct_layout(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:sponsors",
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sponsors and hosts")
        self.assertContains(response, "Name")
        self.assertContains(response, "Sex")
        self.assertContains(response, "Date of birth")
        self.assertContains(response, "Email address")
        self.assertContains(response, "Phone number")
        self.assertContains(response, "EOI host")
        self.assertContains(response, "Date added")

    def test_renders_sponsor_list_content(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:sponsors",
            )
        )

        self.assertContains(response, self.sponsor.full_name)
        self.assertContains(response, self.sponsor.sex)
        self.assertContains(response, self.sponsor.date_of_birth.strftime("%-d %b %Y"))
        self.assertContains(response, self.sponsor.email)
        self.assertContains(response, self.sponsor.phone_number[0])
        self.assertContains(response, "False")
        self.assertContains(response, self.sponsor.created_date.strftime("%-d %b %Y"))

    def test_does_not_render_non_principal_sponsor(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:sponsors",
            )
        )

        self.assertNotContains(response, self.non_principal_sponsor.full_name)

    def test_admin_user_can_access_list_view(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:sponsors",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_la_user_can_access_list_view(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:sponsors",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_da_user_can_access_list_view(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:sponsors",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_mhclg_user_can_access_list_view(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:sponsors",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_service_support_user_can_access_list_view(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:sponsors",
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_ukvi_user_can_access_list_view(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:sponsors",
            )
        )

        self.assertEqual(response.status_code, 200)
