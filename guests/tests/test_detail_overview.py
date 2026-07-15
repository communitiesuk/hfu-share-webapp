import http.client
from datetime import date, datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.enums import GroupType
from accounts.tests.base import TestSessionTokenMixin
from accounts.tests.factories import GroupFactory
from deduplication.tests.factories import GuestDuplicateGroupFactory
from guests.views import GuestDetailOverviewView
from ontology.tests.factories import MvAccommodationRequestFactory, MvPersonFactory
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_ukvi_user,
)


class GuestDetailOverviewViewTests(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["ltla_somerset"],
            person_id=["person-2"],
            number_of_people=1,
        )
        self.guest = MvPersonFactory(
            pk="person-2",
            first_name="UPE",
            last_name="Test",
            date_of_birth=date(1991, 6, 20),
            upe_visa_status="UPE_VISA_ACCEPTED",
            accommodation_request=self.accommodation_request,
        )
        self.overview_url = reverse(
            "guests:detail-overview", kwargs={"pk": self.guest.pk}
        )
        self.ltla_group = GroupFactory(
            name="ltla_somerset",
            groupinfo__ltla_name="ltla_somerset",
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY,
        )

        self.dup_record_one = MvPersonFactory(is_principal=False)
        self.dup_record_two = MvPersonFactory(is_principal=False)
        self.dup_principal_record = MvPersonFactory(
            first_name="Test",
            last_name="Principal",
            is_principal=True,
        )
        self.dup_group = GuestDuplicateGroupFactory(
            principal_record=self.dup_principal_record,
            created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        self.dup_group.guests.set([self.dup_record_one, self.dup_record_two])
        self.dup_group.save()

        self.archived_guest = MvPersonFactory(
            first_name="Archived",
            last_name="Sponsor",
            is_principal=True,
            is_archived=True,
            archived_at=datetime(2025, 12, 25, tzinfo=timezone.utc),
        )

    def test_archived_guest_cannot_be_viewed(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse("guests:detail-overview", kwargs={"pk": self.archived_guest.pk})
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_show_upe_visa_status_la_user(self):
        la_user = get_la_user()
        view = GuestDetailOverviewView()
        request = self.client.request().wsgi_request
        request.user = la_user
        view.request = request
        self.assertFalse(view.show_upe_visa_status())

    def test_show_upe_visa_status_ukvi_user(self):
        ukvi_user = get_ukvi_user()
        view = GuestDetailOverviewView()
        request = self.client.request().wsgi_request
        request.user = ukvi_user
        view.request = request
        self.assertTrue(view.show_upe_visa_status())

    def test_overview_page_shows_upe_visa_status_for_ukvi_user(self):
        ukvi_user = get_ukvi_user()
        ukvi_user.groups.add(self.ltla_group)
        self.client.force_login(ukvi_user)
        response = self.client.get(self.overview_url)
        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "UPE visa status")

    def test_overview_page_shows_upe_visa_status_for_admin_user(self):
        admin_user = get_admin_user()
        admin_user.groups.add(self.ltla_group)
        self.client.force_login(admin_user)
        response = self.client.get(self.overview_url)
        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "UPE visa status")

    def test_overview_page_hides_upe_visa_status_for_la_user(self):
        la_user = get_la_user()
        la_user.groups.add(self.ltla_group)
        self.client.force_login(la_user)
        response = self.client.get(self.overview_url)
        self.assertEqual(response.status_code, http.client.OK)
        self.assertNotContains(response, "UPE visa status")

    def test_overview_page_hides_upe_visa_status_for_da_user(self):
        da_user = get_da_user()
        self.accommodation_request.ltla_name = ["Aberdeenshire"]
        self.accommodation_request.save()
        self.client.force_login(da_user)
        response = self.client.get(self.overview_url)
        self.assertEqual(response.status_code, http.client.OK)
        self.assertNotContains(response, "UPE visa status")

    def test_overview_should_display_change_link_only_when_is_principal(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-overview",
                args=[self.dup_principal_record.pk],
            )
        )

        self.assertContains(response, "Change", html=True)

        response = self.client.get(
            reverse(
                "guests:detail-overview",
                args=[self.dup_record_one.pk],
            )
        )

        self.assertNotContains(response, "Change", html=True)

    def test_duplicate_label_renders_for_duplicate_guests_only(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-overview",
                args=[self.dup_record_one.pk],
            )
        )

        self.assertContains(response, "Duplicate")

        response = self.client.get(
            reverse(
                "guests:detail-overview",
                args=[self.dup_principal_record.pk],
            )
        )

        self.assertNotContains(response, "Duplicate")

    def test_duplicate_message_with_principal_record_renders_for_duplicate_guests(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-overview",
                args=[self.dup_record_one.pk],
            )
        )

        self.assertContains(
            response,
            "This record is a duplicate and cannot be changed. "
            "It was combined with another duplicate to create a new principal",
        )

        self.assertRegex(
            response.content.decode(),
            r"<a href=/guests/\d+/overview>"
            f"guest record for "
            f"{self.dup_principal_record.get_full_name()}"
            f"</a>",
        )

        # self.assertContains(
        #     response,
        #     "If this was a mistake you can undo the deduplication "
        #     "from the actions tab.",
        # )

        response = self.client.get(
            reverse(
                "guests:detail-overview",
                args=[self.dup_principal_record.pk],
            )
        )

        self.assertNotContains(
            response, "This record is a duplicate and cannot be changed."
        )
