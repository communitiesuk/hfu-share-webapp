import http.client
from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
)
from ontology.tests.factories import MvVolunteerFactory as SponsorFactory
from user_management.tests.base import get_admin_user, get_da_user


class SponsorEditViewTests(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sponsor = SponsorFactory(
            pk="sponsor-1",
            first_name="Initial",
            last_name="Sponsor",
            date_of_birth=date(1990, 5, 15),
            sex="Female",
            email="test@example.com",
            phone_number=["123"],
            passport_details=["abc123"],
            family_situation="Separated",
            is_editable=True,
        )

        # Building so that we avoid trying to .save() the object which will fail
        # due to is_editable = False
        self.uneditable_sponsor = SponsorFactory.build(
            pk="sponsor-2",
            first_name="Second",
            last_name="Sponsor",
            date_of_birth=date(1990, 5, 15),
            sex="Female",
            email="test@example.com",
            phone_number=["123"],
            passport_details=["abc123"],
            family_situation="Separated",
            is_editable=False,
        )
        self.guest = MvPersonFactory(
            first_name="Guest",
            last_name="Person",
        )
        self.scottish_sponsor = SponsorFactory(
            pk="sponsor-3",
            first_name="Scottish",
            last_name="Sponsor",
            date_of_birth=date(1990, 5, 15),
            sex="Female",
            email="test@example.com",
            phone_number=["123"],
            passport_details=["abc123"],
            family_situation="Separated",
            is_editable=True,
        )
        self.scottish_accommodation = MvAccommodationFactory(
            ltla_name="City of Edinburgh",
            full_address="Edinburgh accommodation",
        )
        self.scottish_accommodation.hosts.set([self.scottish_sponsor.id])
        self.scottish_ar = MvAccommodationRequestFactory(
            title="Guest Person to Scottish accom",
            ltla_name=["City of Edinburgh"],
            primary_accommodation=self.scottish_accommodation,
            accommodation_id=[
                self.scottish_accommodation.id,
            ],
            person_id=[self.guest.id],
            number_of_people=1,
            primary_sponsor=self.scottish_sponsor,
            sponsor_id=[self.scottish_sponsor.id],
            active_host=self.scottish_sponsor,
        )

        self.edit_url = reverse("sponsors:detail-edit", kwargs={"pk": self.sponsor.pk})
        self.scottish_edit_url = reverse(
            "sponsors:detail-edit", kwargs={"pk": self.scottish_sponsor.pk}
        )
        self.success_url = reverse(
            "sponsors:detail-overview", kwargs={"pk": self.sponsor.pk}
        )

    def test_edit_view_get_loads_correctly_for_da_users(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(self.scottish_edit_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sponsor and host record for")
        self.assertContains(response, "Scottish Sponsor")
        self.assertContains(response, 'id="id_first_name">\nScottish')
        self.assertContains(response, 'id="id_last_name">\nSponsor')
        self.assertContains(response, 'value="15/05/1990"')
        self.assertContains(response, 'value="Female" selected')

    def test_edit_view_get_loads_correctly_for_admin_users(self):
        user = get_admin_user()
        self.client.force_login(user)
        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sponsor and host record for")
        self.assertContains(response, "Initial Sponsor")
        self.assertContains(response, 'id="id_first_name">\nInitial')
        self.assertContains(response, 'id="id_last_name">\nSponsor')
        self.assertContains(response, 'value="15/05/1990"')
        self.assertContains(response, 'value="Female" selected')

    def test_edit_view_returns_404_for_uneditable_sponsor(self):
        user = get_admin_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("sponsors:detail-edit", kwargs={"pk": self.uneditable_sponsor.id})
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_edit_view_post_returns_404_for_uneditable_sponsor(self):
        user = get_admin_user()
        self.client.force_login(user)
        response = self.client.post(
            reverse("sponsors:detail-edit", kwargs={"pk": self.uneditable_sponsor.id}),
            form_data={},
            follow=True,
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_edit_view_post_updates_sponsor(self):
        user = get_admin_user()
        self.client.force_login(user)
        form_data = {
            "first_name": "Updated",
            "last_name": "Sponsor",
            "date_of_birth": "20/08/1992",
            "sex": "Male",
            "email": "test1@example.com",
            "phone_number-0": "1231",
            "passport_details-0": "abc1231",
            "family_situation": "Single",
        }
        response = self.client.post(self.edit_url, data=form_data, follow=True)

        self.assertEqual(response.status_code, 200)

        self.assertRedirects(
            response, self.success_url, status_code=302, target_status_code=200
        )

        self.sponsor.refresh_from_db()
        self.assertEqual(self.sponsor.full_name, "Updated Sponsor")
        self.assertEqual(self.sponsor.first_name, "Updated")
        self.assertEqual(self.sponsor.last_name, "Sponsor")
        self.assertEqual(self.sponsor.date_of_birth, date(1992, 8, 20))
        self.assertEqual(self.sponsor.sex, "Male")
        self.assertEqual(self.sponsor.email, "test1@example.com")
        self.assertEqual(self.sponsor.phone_number, ["1231"])
        self.assertEqual(self.sponsor.passport_details, ["abc1231"])
        self.assertEqual(self.sponsor.family_situation, "Single")
        self.assertTrue(self.sponsor.edited_in_app)

    def test_edit_view_post_updates_duplicate_sponsor_name(self):
        user = get_admin_user()
        self.client.force_login(user)
        self.sponsor.is_principal = False
        self.sponsor.save()

        form_data = {
            "first_name": "Test",
            "last_name": "Sponsor",
            "date_of_birth": "20/08/1992",
            "sex": "Male",
            "email": "test1@example.com",
            "phone_number-0": "1231",
            "passport_details-0": "abc1231",
            "family_situation": "Single",
        }
        response = self.client.post(self.edit_url, data=form_data, follow=True)

        self.assertEqual(response.status_code, 200)

        self.assertRedirects(
            response, self.success_url, status_code=302, target_status_code=200
        )

        self.sponsor.refresh_from_db()
        self.assertEqual(self.sponsor.full_name, "Test Sponsor")
        self.assertEqual(self.sponsor.first_name, "Test")
        self.assertEqual(self.sponsor.last_name, "Sponsor")
        self.assertEqual(self.sponsor.date_of_birth, date(1992, 8, 20))
        self.assertEqual(self.sponsor.sex, "Male")
        self.assertEqual(self.sponsor.email, "test1@example.com")
        self.assertEqual(self.sponsor.phone_number, ["1231"])
        self.assertEqual(self.sponsor.passport_details, ["abc1231"])
        self.assertEqual(self.sponsor.family_situation, "Single")
        self.assertTrue(self.sponsor.edited_in_app)

    def test_edit_view_post_invalid_data(self):
        user = get_admin_user()
        self.client.force_login(user)
        form_data = {
            "first_name": "Initial",
            "last_name": "",
            "date_of_birth": "20/08/1992",
            "sex": "",
            "email": "test1@example.com",
            "phone_number-0": "1231",
            "passport_details-0": "abc1231",
            "family_situation": "Separated",
        }
        response = self.client.post(self.edit_url, data=form_data)

        self.assertEqual(response.status_code, 200)
        errors = response.context["form"].errors
        self.assertEqual(errors["last_name"][0], "Please enter a valid last name")

        self.sponsor.refresh_from_db()
        self.assertEqual(self.sponsor.first_name, "Initial")
        self.assertEqual(self.sponsor.last_name, "Sponsor")
