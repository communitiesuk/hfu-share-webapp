import http.client
import uuid

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
    SafeguardingReferralFactory,
)
from user_management.tests.base import get_ukvi_user


class SearchEscalatedChecksTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = get_ukvi_user()
        self.client.force_login(self.user)
        self.url = reverse("safeguarding:escalated_checks")

        sponsor = MvVolunteerFactory(full_name="Test Sponsor")
        accommodation_request = MvAccommodationRequestFactory(primary_sponsor=sponsor)
        person1 = MvPersonFactory(
            first_name="Jane",
            last_name="Brown",
            date_of_birth="1990-02-01",
            passport_id=["A2234567"],
            gwf=["GWF123457"],
            application_number=["UAN123416"],
            visa_status="Active",
            accommodation_request=accommodation_request,
        )
        referral_1 = SafeguardingReferralFactory(
            id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            person=person1,
        )

        sponsor2 = MvVolunteerFactory(full_name="Alice Smith")
        accommodation_request2 = MvAccommodationRequestFactory(primary_sponsor=sponsor2)
        person2 = MvPersonFactory(
            first_name="Alice",
            last_name="Smith",
            date_of_birth="1985-05-12",
            passport_id=["B7654321"],
            gwf=["GWF654321"],
            application_number=["UAN654321"],
            visa_status="Pending",
            accommodation_request=accommodation_request2,
        )
        referral_2 = SafeguardingReferralFactory(
            id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            person=person2,
        )

        sponsor3 = MvVolunteerFactory(full_name="Carlos Rivera")
        accommodation_request3 = MvAccommodationRequestFactory(primary_sponsor=sponsor3)
        person3 = MvPersonFactory(
            first_name="Carlos",
            last_name="Rivera",
            date_of_birth="1978-09-23",
            passport_id=["C2345678"],
            gwf=["GWF234567"],
            application_number=["UAN234567"],
            visa_status="Expired",
            accommodation_request=accommodation_request3,
        )
        referral_3 = SafeguardingReferralFactory(
            id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
            person=person3,
        )

        sponsor4 = MvVolunteerFactory(full_name="Fatima Al-Farsi")
        accommodation_request4 = MvAccommodationRequestFactory(primary_sponsor=sponsor4)
        person4 = MvPersonFactory(
            first_name="Fatima",
            last_name="Al-Farsi",
            date_of_birth="1995-11-30",
            passport_id=["D8765432"],
            gwf=["GWF876543"],
            application_number=["UAN876543"],
            visa_status="Active",
            accommodation_request=accommodation_request4,
        )
        referral_4 = SafeguardingReferralFactory(
            id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
            person=person4,
        )

        sponsor5 = MvVolunteerFactory(full_name="Liam O'Connor")
        accommodation_request5 = MvAccommodationRequestFactory(primary_sponsor=sponsor5)
        person5 = MvPersonFactory(
            first_name="Liam",
            last_name="O'Connor",
            date_of_birth="2000-03-15",
            passport_id=["E3456789"],
            gwf=["GWF345678"],
            application_number=["UAN345678"],
            visa_status="Pending",
            accommodation_request=accommodation_request5,
        )
        referral_5 = SafeguardingReferralFactory(
            id=uuid.UUID("55555555-5555-5555-5555-555555555555"),
            person=person5,
        )

        sponsor6 = MvVolunteerFactory(full_name="Mei Chen")
        accommodation_request6 = MvAccommodationRequestFactory(primary_sponsor=sponsor6)
        person6 = MvPersonFactory(
            first_name="Mei",
            last_name="Chen",
            date_of_birth="1992-07-08",
            passport_id=["F9876543"],
            gwf=["GWF987654"],
            application_number=["UAN987654"],
            visa_status="Active",
            accommodation_request=accommodation_request6,
        )
        referral_6 = SafeguardingReferralFactory(
            id=uuid.UUID("66666666-6666-6666-6666-666666666666"),
            person=person6,
        )

        self.guests = [
            referral_1,
            referral_2,
            referral_3,
            referral_4,
            referral_5,
            referral_6,
        ]

    def test_get_view_no_match(self):
        form_data = {
            "search": "anythingthatdoesnotmatch",
        }
        response = self.client.get(self.url, data=form_data, follow=True)
        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(response.status_code, 200)
        for guest in self.guests:
            self.assertNotContains(response, guest.person.first_name)

    def test_get_view_no_search(self):
        form_data = {}
        response = self.client.get(self.url, data=form_data, follow=True)
        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(response.status_code, 200)
        for guest in self.guests:
            self.assertContains(response, guest.person.first_name)

    def test_search_by_first_name(self):
        guest = self.guests[0]
        form_data = {"search": guest.person.first_name}
        response = self.client.get(self.url, data=form_data, follow=True)
        self.assertContains(response, guest.person.first_name)
        for other in self.guests[1:]:
            self.assertNotContains(response, other.person.first_name)

    def test_search_by_last_name(self):
        guest = self.guests[1]
        form_data = {"search": guest.person.last_name}
        response = self.client.get(self.url, data=form_data, follow=True)
        self.assertContains(response, guest.person.first_name)
        for idx, other in enumerate(self.guests):
            if idx != 1:
                self.assertNotContains(response, other.person.first_name)

    def test_search_by_passport_id(self):
        guest = self.guests[3]
        passport_id = guest.person.passport_id[0]
        form_data = {"search": passport_id}
        response = self.client.get(self.url, data=form_data, follow=True)
        self.assertContains(response, guest.person.first_name)
        for idx, other in enumerate(self.guests):
            if idx != 3:
                self.assertNotContains(response, other.person.first_name)

    def test_search_by_gwf(self):
        guest = self.guests[4]
        gwf = guest.person.gwf[0]
        form_data = {"search": gwf}
        response = self.client.get(self.url, data=form_data, follow=True)
        self.assertContains(response, guest.person.first_name)
        for idx, other in enumerate(self.guests):
            if idx != 4:
                self.assertNotContains(response, other.person.first_name)

    def test_search_by_application_number(self):
        guest = self.guests[5]
        application_number = guest.person.application_number[0]
        form_data = {"search": application_number}
        response = self.client.get(self.url, data=form_data, follow=True)
        self.assertContains(response, guest.person.first_name)
        for idx, other in enumerate(self.guests):
            if idx != 5:
                self.assertNotContains(response, other.person.first_name)

    def test_search_with_exact_match(self):
        # Create a person with a name that could match partially
        sponsor7 = MvVolunteerFactory(full_name="Test Sponsor 7")
        accommodation_request7 = MvAccommodationRequestFactory(primary_sponsor=sponsor7)
        person7 = MvPersonFactory(
            first_name="Joe",
            last_name="Smith",
            date_of_birth="1980-01-01",
            passport_id=["G1111111"],
            gwf=["GWF111111"],
            application_number=["UAN111111"],
            visa_status="Active",
            accommodation_request=accommodation_request7,
        )
        SafeguardingReferralFactory(
            id=uuid.UUID("77777777-7777-7777-7777-777777777777"),
            person=person7,
        )

        # Exact match search for "Alice Smith" should only match person2, not person7
        form_data = {"search": '"Alice Smith"'}
        response = self.client.get(self.url, data=form_data, follow=True)
        self.assertContains(response, self.guests[1].person.first_name)
        self.assertNotContains(response, person7.first_name)
