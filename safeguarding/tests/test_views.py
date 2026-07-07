import http.client
from datetime import datetime

from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import (
    DevCheckV2,
    SafeguardingReferral,
)
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
    SafeguardingNotificationFactory,
    SafeguardingReferralFactory,
)
from safeguarding.tests.base import SafeguardingBaseTestCase
from safeguarding.views import (
    EscalatedChecksTable,
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_ukvi_user,
)


class EscalatedChecksViewTest(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.user = get_ukvi_user()
        self.url = reverse("safeguarding:escalated_checks")

    def test_ukvi_user_can_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_denied_access(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_da_user_is_denied_access(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_get_view(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "safeguarding/escalated_checks_list.html")
        self.assertContains(response, "Escalated checks")
        self.assertIsInstance(response.context_data["table"], EscalatedChecksTable)

    def test_table_displays_model_data(self):
        self.client.force_login(self.user)
        sponsor = MvVolunteerFactory(full_name="Test Sponsor")
        accommodation_request = MvAccommodationRequestFactory(primary_sponsor=sponsor)
        person = MvPersonFactory(
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-01",
            passport_id=["A1234567"],
            gwf=["GWF123456"],
            application_number=["UAN123456"],
            visa_status="Arrived",
            accommodation_request=accommodation_request,
        )

        known_date = timezone.make_aware(datetime(2025, 6, 3, 13, 34, 0))
        SafeguardingReferralFactory(
            person=person,
            created_at=known_date,
            alerted_status=SafeguardingReferral.AlertedStatus.ALERTED,
        )

        SafeguardingNotificationFactory(
            ar=accommodation_request,
            created_at=known_date,
        )

        SafeguardingNotificationFactory(
            ar=accommodation_request, created_at=known_date + timezone.timedelta(days=2)
        )

        response = self.client.get(self.url)

        self.assertContains(response, "John Doe")
        self.assertContains(response, "1 Jan 1990")
        self.assertContains(response, "A1234567")
        self.assertContains(response, "GWF123456")
        self.assertContains(response, "UAN123456")
        self.assertContains(response, "Arrived")
        self.assertContains(response, "3 Jun 2025, 1:34pm")
        self.assertContains(response, "Alerted")
        self.assertContains(response, "5 Jun 2025, 1:34pm")

    def test_table_handles_missing_data(self):
        self.client.force_login(self.user)
        # person without an accommodation request or sponsor
        person = MvPersonFactory(
            first_name="Jane",
            last_name="Smith",
            date_of_birth="1985-05-05",
            passport_id=["B7654321"],
            gwf=["GWF654321"],
            application_number=["UAN654321"],
            visa_status="Pending",
            accommodation_request=None,
        )
        SafeguardingReferralFactory(person=person)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jane Smith")
        self.assertContains(response, "5 May 1985")
        self.assertContains(response, "B7654321")
        self.assertContains(response, "GWF654321")
        self.assertContains(response, "UAN654321")
        self.assertContains(response, "Pending")

    def test_table_handles_missing_alert_data(self):
        self.client.force_login(self.user)
        sponsor = MvVolunteerFactory(full_name="Test Sponsor")
        accommodation_request = MvAccommodationRequestFactory(primary_sponsor=sponsor)
        person = MvPersonFactory(
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-01",
            passport_id=["A1234567"],
            gwf=["GWF123456"],
            application_number=["UAN123456"],
            visa_status="Arrived",
            accommodation_request=accommodation_request,
        )

        known_date = timezone.make_aware(datetime(2025, 6, 3, 13, 34, 0))
        SafeguardingReferralFactory(
            person=person,
            created_at=known_date,
            alerted_status=SafeguardingReferral.AlertedStatus.ALERTED,
        )

        SafeguardingNotificationFactory(
            ar=accommodation_request,
            created_at=None,
        )

        SafeguardingNotificationFactory(
            ar=accommodation_request,
            created_at=None,
        )

        response = self.client.get(self.url)
        self.assertContains(response, "3 Jun 2025, 1:34pm", count=2)


class SafeguardingDetailSafeguardingChecksViewTestCase(
    TestSessionTokenMixin, SafeguardingBaseTestCase
):
    def setUp(self):
        super().setUp()
        self.client.force_login(get_admin_user())
        self.referral = SafeguardingReferralFactory(person=self.person)

    def test_shows_accommodation_check(self):
        url = reverse(
            "safeguarding:detail-safeguarding-checks",
            args=[self.person.pk, str(self.referral.id)],
        )
        response = self.client.get(url)
        self.assertContains(response, "Accommodation suitable")

    def test_shows_accommodation_exists_check(self):
        url = reverse(
            "safeguarding:detail-safeguarding-checks",
            args=[self.person.pk, str(self.referral.id)],
        )
        response = self.client.get(url)
        self.assertContains(response, "Accommodation exists")

    def test_shows_sponsor_dbs_check(self):
        url = reverse(
            "safeguarding:detail-safeguarding-checks",
            args=[self.person.pk, str(self.referral.id)],
        )
        response = self.client.get(url)
        self.assertContains(response, "DBS check and Sponsor suitable")

    def test_shows_guest_has_arrived_check(self):
        url = reverse(
            "safeguarding:detail-safeguarding-checks",
            args=[self.person.pk, str(self.referral.id)],
        )
        response = self.client.get(url)
        self.assertContains(response, "Guests have arrived in their accommodation")

    def test_renders_correct_message_for_check_status(self):
        status_to_message = {
            DevCheckV2.CheckStatus.PASSED: "Checks complete: Passed",
            DevCheckV2.CheckStatus.FAILED: "Checks complete: Failed",
            DevCheckV2.CheckStatus.NOT_STARTED: "Checks not started",
            DevCheckV2.CheckStatus.IN_PROGRESS: "Checks in progress",
            DevCheckV2.CheckStatus.NO_LONGER_NEEDED: "Checks complete: "
            "No longer needed",
        }
        for status, message in status_to_message.items():
            with self.subTest(status=status, message=message):
                self.accommodation_suitable_check.check_status = status
                self.accommodation_suitable_check.save()
                url = reverse(
                    "safeguarding:detail-safeguarding-checks",
                    args=[self.person.pk, str(self.referral.id)],
                )
                response = self.client.get(url)
                self.assertContains(response, message)
