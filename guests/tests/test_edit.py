import http.client
from datetime import date, datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.enums import GroupType
from accounts.tests.base import TestSessionTokenMixin
from accounts.tests.factories import GroupFactory
from guests.forms import GuestEditAdminForm, GuestEditForm, GuestEditUKVIForm
from guests.views import GuestEditView
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvGroupFactory,
    MvPersonFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_ukvi_user,
)


class GuestEditViewTests(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = get_admin_user()
        self.accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["ltla_somerset"],
            person_id=["person-1"],
            number_of_people=1,
        )
        self.group = MvGroupFactory()

        self.guest = MvPersonFactory(
            pk="person-1",
            first_name="Initial",
            last_name="Guest",
            date_of_birth=date(1990, 5, 15),
            gender="Female",
            disability_flag=True,
            email=["test@example.com"],
            phone=["123"],
            passport_id=["abc123"],
            accommodation_request=self.accommodation_request,
            group=self.group,
        )
        self.ltla_group = GroupFactory(
            name="ltla_somerset",
            groupinfo__ltla_name="ltla_somerset",
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY,
        )

        self.edit_url = reverse("guests:detail-edit", kwargs={"pk": self.guest.pk})
        self.success_url = reverse(
            "guests:detail-overview", kwargs={"pk": self.guest.pk}
        )

        self.archived_guest = MvPersonFactory(
            first_name="Archived",
            last_name="Sponsor",
            is_principal=True,
            is_archived=True,
            archived_at=datetime(2025, 12, 25, tzinfo=timezone.utc),
        )

    def test_edit_view_get_loads_correctly(self):
        self.client.force_login(self.user)
        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "Guest record for")
        self.assertContains(response, "Initial Guest")
        self.assertContains(response, 'id="id_first_name">\nInitial')
        self.assertContains(response, 'id="id_last_name">\nGuest')
        self.assertContains(response, 'value="15/05/1990"')
        self.assertContains(response, 'value="Female" selected')

    def test_edit_view_returns_404_for_archived_guest(self):
        user = get_admin_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse("guests:detail-edit", kwargs={"pk": self.archived_guest.pk})
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_edit_view_post_updates_guest(self):
        self.client.force_login(self.user)
        form_data = {
            "first_name": "Updated",
            "last_name": "Guest",
            "date_of_birth": "20/08/1992",
            "gender": "Male",
            "disability_flag": False,
            "email-0": "test1@example.com",
            "email-1": "test2@example.com",
            "phone-0": "1231",
            "passport_id-0": "abc1231",
            "upe_visa_status": "UPE_VISA_ACCEPTED",
        }
        response = self.client.post(self.edit_url, data=form_data, follow=True)

        self.assertEqual(response.status_code, http.client.OK)

        self.assertRedirects(
            response,
            self.success_url,
            status_code=http.client.FOUND,
            target_status_code=http.client.OK,
        )

        self.guest.refresh_from_db()
        self.assertEqual(self.guest.first_name, "Updated")
        self.assertEqual(self.guest.last_name, "Guest")
        self.assertEqual(self.guest.date_of_birth, date(1992, 8, 20))
        self.assertEqual(self.guest.gender, "Male")
        self.assertEqual(self.guest.disability_flag, False)
        self.assertEqual(self.guest.email, ["test1@example.com", "test2@example.com"])
        self.assertEqual(self.guest.phone, ["1231"])
        self.assertEqual(self.guest.passport_id, ["abc1231"])
        self.assertTrue(self.guest.edited_in_app)

    def test_edit_view_updates_guest_associated_objects(self):
        self.client.force_login(self.user)
        form_data = {
            "first_name": "Updated",
            "last_name": "Guest",
            "date_of_birth": "20/08/1992",
            "gender": "Male",
            "disability_flag": False,
            "email-0": "test1@example.com",
            "email-1": "test2@example.com",
            "phone-0": "1231",
            "passport_id-0": "abc1231",
            "upe_visa_status": "UPE_VISA_ACCEPTED",
        }

        response = self.client.post(self.edit_url, data=form_data, follow=True)

        self.assertEqual(response.status_code, http.client.OK)

        self.guest.refresh_from_db()
        self.group.refresh_from_db()
        self.accommodation_request.refresh_from_db()

        self.assertEqual(self.accommodation_request.title, "Updated Guest")
        self.assertTrue(
            self.accommodation_request.primary_contact_first_name, "Updated"
        )
        self.assertTrue(self.accommodation_request.primary_contact_last_name, "Guest")
        self.assertTrue(self.group.primary_contact_first_name, "Updated")
        self.assertTrue(self.group.primary_contact_last_name, "Guest")

        self.assertTrue(self.accommodation_request.edited_in_app)
        self.assertTrue(self.group.edited_in_app)

    def test_edit_view_post_invalid_data(self):
        self.client.force_login(self.user)
        form_data = {
            "first_name": "",
            "last_name": "User",
            "date_of_birth": "invalid-date",
            "gender": "Male",
            "disability_flag": True,
            "email-0": "test1@example.com",
            "email-1": "test2@example.com",
            "phone-0": "1231",
            "passport_id-0": "abc1231",
            "upe_visa_status": "",
        }
        response = self.client.post(self.edit_url, data=form_data)

        self.assertEqual(response.status_code, http.client.OK)
        errors = response.context["form"].errors
        self.assertEqual(errors["first_name"][0], "Please enter a valid name")
        self.assertEqual(errors["date_of_birth"][0], "Enter a valid date.")

        self.guest.refresh_from_db()
        self.assertEqual(self.guest.first_name, "Initial")
        self.assertEqual(self.guest.date_of_birth, date(1990, 5, 15))

    def test_edit_view_content_for_la_user(self):
        la_user = get_la_user()
        la_user.groups.add(self.ltla_group)
        self.client.force_login(la_user)
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, http.client.OK)
        self.assertNotContains(response, "UPE visa status")

    def test_edit_view_content_for_da_user(self):
        self.accommodation_request.ltla_name = ["Aberdeenshire"]
        self.accommodation_request.save()
        da_user = get_da_user()
        self.client.force_login(da_user)
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, http.client.OK)
        self.assertNotContains(response, "UPE visa status")

    def test_edit_view_content_for_ukvi_user(self):
        ukvi_user = get_ukvi_user()
        ukvi_user.groups.add(self.ltla_group)
        self.client.force_login(ukvi_user)
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "UPE visa status")

    def test_edit_view_content_for_admin_user(self):
        admin_user = get_admin_user()
        admin_user.groups.add(self.ltla_group)
        self.client.force_login(admin_user)
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "UPE visa status")

    def test_get_form_class_for_la_user(self):
        la_user = get_la_user()
        view = GuestEditView()
        view.request = self.client.request().wsgi_request
        view.request.user = la_user
        form_class = view.get_form_class()
        self.assertEqual(form_class, GuestEditForm)

    def test_get_form_class_for_da_user(self):
        da_user = get_da_user()
        view = GuestEditView()
        view.request = self.client.request().wsgi_request
        view.request.user = da_user
        form_class = view.get_form_class()
        self.assertEqual(form_class, GuestEditForm)

    def test_get_form_class_for_ukvi_user(self):
        ukvi_user = get_ukvi_user()
        view = GuestEditView()
        view.request = self.client.request().wsgi_request
        view.request.user = ukvi_user
        form_class = view.get_form_class()
        self.assertEqual(form_class, GuestEditUKVIForm)

    def test_get_form_class_for_admin_user(self):
        admin_user = get_admin_user()
        view = GuestEditView()
        view.request = self.client.request().wsgi_request
        view.request.user = admin_user
        form_class = view.get_form_class()
        self.assertEqual(form_class, GuestEditAdminForm)
