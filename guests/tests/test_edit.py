import http.client
from datetime import date, datetime, timezone

from bs4 import BeautifulSoup
from django.urls import reverse

from accounts.enums import GroupType
from accounts.tests.base import TestSessionTokenMixin
from accounts.tests.factories import GroupFactory
from guests.forms import (
    GuestEditAdminForm,
    GuestEditForm,
    GuestEditMHCLGForm,
    GuestEditUKVIForm,
)
from guests.views import GuestEditView
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvGroupFactory,
    MvPersonFactory,
)
from test_utils.base import BaseTestCase
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_ukvi_user,
)


class GuestEditViewTests(TestSessionTokenMixin, BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = get_admin_user()
        self.accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["ltla_test"],
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
            name="ltla_test",
            groupinfo__ltla_name="ltla_test",
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

        soup = BeautifulSoup(response.content, "html.parser")

        heading = soup.find("h1")

        self.assertEqual(
            heading.get_text(" ", strip=True), "Guest record for Initial Guest"
        )

        first_name_input = soup.find(
            "input", {"name": "first_name", "value": "Initial"}
        )
        last_name_input = soup.find("input", {"name": "last_name", "value": "Guest"})
        date_of_birth_input = soup.find(
            "input", {"name": "date_of_birth", "value": "15/05/1990"}
        )
        gender_option = soup.find("option", {"value": "Female", "selected": True})

        self.assertIsNotNone(first_name_input)
        self.assertIsNotNone(last_name_input)
        self.assertIsNotNone(date_of_birth_input)
        self.assertIsNotNone(gender_option)

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
        self.assertEqual(
            errors["date_of_birth"][0], "Enter a valid date for 'Date of birth'"
        )

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
        self.assertContains(response, "Ukraine Permission Extension (UPE) visa status")

    def test_edit_view_content_for_admin_user(self):
        admin_user = get_admin_user()
        admin_user.groups.add(self.ltla_group)
        self.client.force_login(admin_user)
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "Ukraine Permission Extension (UPE) visa status")

    def test_upe_visa_status_required_error_spells_out_upe(self):
        form = GuestEditUKVIForm(data={}, instance=self.guest)
        self.assertEqual(
            form.errors["upe_visa_status"],
            ["Please select a Ukraine Permission Extension (UPE) visa status"],
        )

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

    def test_get_form_class_for_mhclg_user(self):
        mhclg_user = get_mhclg_user()
        view = GuestEditView()
        view.request = self.client.request().wsgi_request
        view.request.user = mhclg_user
        form_class = view.get_form_class()
        self.assertEqual(form_class, GuestEditMHCLGForm)


class GuestEditEligibleChildTests(TestSessionTokenMixin, BaseTestCase):
    def setUp(self):
        super().setUp()
        self.accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["ltla_test"],
            person_id=["child-1", "sibling-1"],
            number_of_people=2,
            is_uam=False,
            is_uam_edited_time=None,
        )
        self.group = MvGroupFactory()
        self.guest = MvPersonFactory(
            pk="child-1",
            first_name="Child",
            last_name="Guest",
            is_uam=False,
            is_uam_edited_time=None,
            accommodation_request=self.accommodation_request,
            group=self.group,
        )
        self.sibling = MvPersonFactory(
            pk="sibling-1",
            is_uam=False,
            accommodation_request=self.accommodation_request,
        )
        self.ltla_group = GroupFactory(
            name="ltla_test",
            groupinfo__ltla_name="ltla_test",
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY,
        )
        self.edit_url = reverse("guests:detail-edit", kwargs={"pk": self.guest.pk})

    def get_form_data(self, **overrides):
        return {
            "first_name": "Child",
            "last_name": "Guest",
            "date_of_birth": "20/08/2012",
            "email-0": "test@example.com",
            "passport_id-0": "abc123",
            **overrides,
        }

    def post_is_uam(self, value):
        self.client.force_login(get_mhclg_user())
        return self.client.post(self.edit_url, data=self.get_form_data(is_uam=value))

    def test_mhclg_user_sees_eligible_child_radios(self):
        self.client.force_login(get_mhclg_user())
        response = self.client.get(self.edit_url)

        soup = BeautifulSoup(response.content, "html.parser")
        radios = soup.find_all("input", {"name": "is_uam", "type": "radio"})
        self.assertEqual([radio["value"] for radio in radios], ["True", "False"])
        self.assertContains(
            response,
            "Is the guest an eligible child travelling without a parent or guardian?",
        )

    def test_mhclg_user_can_edit_other_fields(self):
        self.client.force_login(get_mhclg_user())
        self.client.post(
            self.edit_url,
            data=self.get_form_data(is_uam="True", first_name="Changed"),
        )

        self.guest.refresh_from_db()
        self.assertEqual(self.guest.first_name, "Changed")
        self.assertTrue(self.guest.is_uam)

    def test_setting_eligible_child_updates_guest_and_accommodation_request(self):
        response = self.post_is_uam("True")

        self.assertRedirects(
            response,
            reverse("guests:detail-overview", kwargs={"pk": self.guest.pk}),
            fetch_redirect_response=False,
        )
        self.guest.refresh_from_db()
        self.accommodation_request.refresh_from_db()

        self.assertTrue(self.guest.is_uam)
        self.assertIsNotNone(self.guest.is_uam_edited_time)
        self.assertTrue(self.accommodation_request.is_uam)
        self.assertEqual(
            self.accommodation_request.is_uam_edited_time,
            self.guest.is_uam_edited_time,
        )
        self.assertTrue(self.accommodation_request.edited_in_app)

    def test_unsetting_eligible_child_updates_accommodation_request(self):
        self.guest.is_uam = True
        self.guest.save()
        self.accommodation_request.is_uam = True
        self.accommodation_request.save()

        self.post_is_uam("False")

        self.guest.refresh_from_db()
        self.accommodation_request.refresh_from_db()
        self.assertFalse(self.guest.is_uam)
        self.assertFalse(self.accommodation_request.is_uam)
        self.assertIsNotNone(self.accommodation_request.is_uam_edited_time)

    def test_accommodation_request_stays_eligible_child_if_another_guest_is(self):
        self.guest.is_uam = True
        self.guest.save()
        self.sibling.is_uam = True
        self.sibling.save()
        self.accommodation_request.is_uam = True
        self.accommodation_request.save()

        self.post_is_uam("False")

        self.guest.refresh_from_db()
        self.accommodation_request.refresh_from_db()
        self.assertFalse(self.guest.is_uam)
        self.assertTrue(self.accommodation_request.is_uam)

    def test_accommodation_request_updated_when_it_does_not_list_the_guest(self):
        self.accommodation_request.person_id = ["sibling-1"]
        self.accommodation_request.save()

        self.post_is_uam("True")

        self.accommodation_request.refresh_from_db()
        self.assertTrue(self.accommodation_request.is_uam)

    def test_unchanged_eligible_child_does_not_update_edited_time(self):
        self.post_is_uam("False")

        self.guest.refresh_from_db()
        self.accommodation_request.refresh_from_db()
        self.assertIsNone(self.guest.is_uam_edited_time)
        self.assertIsNone(self.accommodation_request.is_uam_edited_time)

    def test_only_the_guests_current_accommodation_request_is_updated(self):
        other_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["ltla_test"],
            person_id=["child-1"],
            is_uam=False,
        )

        self.post_is_uam("True")

        other_accommodation_request.refresh_from_db()
        self.assertFalse(other_accommodation_request.is_uam)

    def test_admin_user_can_edit_eligible_child(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(self.edit_url)

        soup = BeautifulSoup(response.content, "html.parser")
        self.assertTrue(soup.find_all("input", {"name": "is_uam", "type": "radio"}))

    def test_other_users_do_not_see_eligible_child(self):
        la_user = get_la_user()
        la_user.groups.add(self.ltla_group)
        ukvi_user = get_ukvi_user()

        for user in [la_user, ukvi_user]:
            with self.subTest(user=user):
                self.client.force_login(user)
                response = self.client.get(self.edit_url)

                self.assertNotContains(response, "Eligible child (UAM)")

    def test_la_user_cannot_change_eligible_child(self):
        la_user = get_la_user()
        la_user.groups.add(self.ltla_group)
        self.client.force_login(la_user)

        self.client.post(self.edit_url, data=self.get_form_data(is_uam="True"))

        self.guest.refresh_from_db()
        self.assertFalse(self.guest.is_uam)
