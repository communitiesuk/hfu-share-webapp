import http.client
from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import MvAccommodationFactory as AccommodationFactory
from ontology.tests.factories import MvUkPostcodeFactory as PostCodeFactory
from user_management.tests.base import get_admin_user, get_da_user, get_la_user


class AccommodationEditViewTests(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = get_admin_user()
        self.default_postcode = PostCodeFactory(postcode_formatted="SA11 2AA")
        self.accommodation = AccommodationFactory(
            full_address="1 Test Street, Neath Port Talbot, SA11 2AA",
            postcode=self.default_postcode,
            current_capacity="1",
            availability_start_date="2024-05-05",
            availability_end_date="2025-05-05",
            wheelchair_accessible=True,
            edited_in_app=False,
            is_editable=True,
            ltla_name="LTLA",
            utla_name="UTLA",
        )

        # Building so that we avoid trying to .save() the object which will fail
        # due to is_editable = False
        self.uneditable_accommodation = AccommodationFactory.build(
            full_address="1 Test Street, Neath Port Talbot, SA11 2AA",
            postcode=self.default_postcode,
            current_capacity="1",
            availability_start_date="2024-05-05",
            availability_end_date="2025-05-05",
            wheelchair_accessible=True,
            is_editable=False,
        )

        self.ltla_accommodation = AccommodationFactory(
            full_address="Somerset LTLA Address",
            postcode=self.default_postcode,
            current_capacity="1",
            availability_start_date="2024-05-05",
            availability_end_date="2025-05-05",
            wheelchair_accessible=True,
            edited_in_app=False,
            is_editable=True,
            ltla_name="ltla_somerset",
        )
        self.da_accommodation = AccommodationFactory(
            full_address="Scotland DA address",
            postcode=self.default_postcode,
            current_capacity="1",
            availability_start_date="2024-05-05",
            availability_end_date="2025-05-05",
            wheelchair_accessible=True,
            edited_in_app=False,
            is_editable=True,
            ltla_name="Aberdeenshire",
            utla_name="Aberdeenshire",
        )

        self.edit_url = reverse(
            "accommodations:edit", kwargs={"pk": self.accommodation.id}
        )
        self.success_url = reverse(
            "accommodations:detail-overview", kwargs={"pk": self.accommodation.id}
        )

    def test_overview_get_loads_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse("accommodations:edit", kwargs={"pk": self.accommodation.id})
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_allowed_access(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("accommodations:edit", kwargs={"pk": self.ltla_accommodation.id})
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_denied_access_to_other_la_accom(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("accommodations:edit", kwargs={"pk": self.accommodation.id})
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_da_user_is_allowed_access(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("accommodations:edit", kwargs={"pk": self.da_accommodation.id})
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_denied_access_to_other_da_accom(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("accommodations:edit", kwargs={"pk": self.accommodation.id})
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_edit_view_returns_404_for_uneditable_accommodation(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "accommodations:edit", kwargs={"pk": self.uneditable_accommodation.id}
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_edit_view_post_returns_404_for_uneditable_accommodation(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse(
                "accommodations:edit", kwargs={"pk": self.uneditable_accommodation.id}
            ),
            form_data={},
            follow=True,
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_edit_view_get_loads_correctly(self):
        self.client.force_login(self.user)
        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertTemplateUsed(
            response, "accommodations/edit_view/edit_view_question.html"
        )
        self.assertContains(response, "Accommodation record for")
        self.assertContains(response, "1 Test Street, Neath Port Talbot, SA11 2AA")
        self.assertContains(response, 'name="current_capacity" value="1"')
        self.assertContains(response, 'name="availability_start_date"')
        self.assertContains(response, 'name="availability_end_date"')
        # this is loaded by js now
        self.assertNotContains(response, 'name="postcode"')

    def test_edit_view_post_updates_accommodation(self):
        self.client.force_login(self.user)
        new_postcode = PostCodeFactory(postcode_formatted="SA11 2AA")
        form_data = {
            "full_address": "1 Test Street, Neath Port Talbot, SA11 2AA",
            "current_capacity": "1",
            "availability_start_date": "2024-05-05",
            "availability_end_date": "2025-05-05",
            "wheelchair_accessible": False,
            "postcode": new_postcode.postcode_formatted,
        }
        response = self.client.post(self.edit_url, data=form_data, follow=True)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertRedirects(
            response,
            self.success_url,
            status_code=http.client.FOUND,
            target_status_code=http.client.OK,
        )

        self.accommodation.refresh_from_db()
        self.assertEqual(
            self.accommodation.full_address,
            "1 Test Street, Neath Port Talbot, SA11 2AA",
        )

        self.assertEqual(self.accommodation.current_capacity, 1)
        self.assertEqual(self.accommodation.availability_start_date, date(2024, 5, 5))
        self.assertEqual(self.accommodation.availability_end_date, date(2025, 5, 5))
        self.assertEqual(self.accommodation.wheelchair_accessible, False)
        self.assertEqual(
            self.accommodation.postcode.postcode_formatted,
            new_postcode.postcode_formatted,
        )
        self.assertTrue(self.accommodation.edited_in_app)

    def test_edit_view_post_updates_duplicate_accommodation_address(self):
        self.client.force_login(self.user)
        self.accommodation.is_principal = False
        self.accommodation.save()

        new_postcode = PostCodeFactory(postcode_formatted="SA11 2AA")
        form_data = {
            "full_address": "New full address, New town address, SA11 2AA",
            "current_capacity": "1",
            "availability_start_date": "2024-05-05",
            "availability_end_date": "2025-05-05",
            "wheelchair_accessible": False,
            "postcode": new_postcode.postcode_formatted,
        }
        response = self.client.post(self.edit_url, data=form_data, follow=True)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertRedirects(
            response,
            self.success_url,
            status_code=http.client.FOUND,
            target_status_code=http.client.OK,
        )

        self.accommodation.refresh_from_db()
        self.assertEqual(
            self.accommodation.full_address,
            "New full address, New town address, SA11 2AA",
        )
        self.assertContains(response, "Duplicate")

        self.assertEqual(self.accommodation.current_capacity, 1)
        self.assertEqual(self.accommodation.availability_start_date, date(2024, 5, 5))
        self.assertEqual(self.accommodation.availability_end_date, date(2025, 5, 5))
        self.assertEqual(self.accommodation.wheelchair_accessible, False)
        self.assertEqual(
            self.accommodation.postcode.postcode_formatted,
            new_postcode.postcode_formatted,
        )
        self.assertTrue(self.accommodation.edited_in_app)

    def test_edit_view_post_invalid_data(self):
        self.client.force_login(self.user)
        form_data = {
            "full_address": "",
            "current_capacity": "1",
            "availability_start_date": "2024-05-05",
            "availability_end_date": "2025-05-05",
            "wheelchair_accessible": True,
            "postcode": self.default_postcode.id,
        }
        response = self.client.post(self.edit_url, data=form_data)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertTemplateUsed(
            response, "accommodations/edit_view/edit_view_question.html"
        )
        errors = response.context["form"].errors
        self.assertEqual(errors["full_address"][0], "Please enter a valid UK address")

        self.accommodation.refresh_from_db()
        self.assertEqual(
            self.accommodation.full_address,
            "1 Test Street, Neath Port Talbot, SA11 2AA",
        )

        self.assertEqual(self.accommodation.current_capacity, 1)
        self.assertEqual(self.accommodation.availability_start_date, date(2024, 5, 5))
        self.assertEqual(self.accommodation.availability_end_date, date(2025, 5, 5))
        self.assertEqual(self.accommodation.wheelchair_accessible, True)
