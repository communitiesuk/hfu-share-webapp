from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import CheckType, DevCheckV2, SafeguardingNotification
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
    SafeguardingNotificationFactory,
    SafeguardingReferralFactory,
    VisaApplicationFactory,
)
from user_management.tests.base import (
    get_ukvi_user,
)


class SponsorVisaApplicationAlertTests(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        # Create sponsor
        self.sponsor = MvVolunteerFactory(
            application_unique_application_number=[
                "1300-3423-3462-9435",
                "1300-7658-5457-7686",
            ]
        )

        self.ar1 = MvAccommodationRequestFactory()
        self.ar2 = MvAccommodationRequestFactory()
        self.guest1 = MvPersonFactory(accommodation_request=self.ar1)
        self.guest2 = MvPersonFactory(accommodation_request=self.ar2)
        self.visa1 = VisaApplicationFactory(
            application_unique_application_number="1300-3423-3462-9435",
            gwf="GWF137686345",
            visa_status="Issued",
            visa_decision_date=datetime(2025, 10, 1, 0, 0, tzinfo=timezone.utc),
            application_event_datetime=datetime(2025, 9, 1, 0, 0, tzinfo=timezone.utc),
            title="Title 1",
        )
        self.visa2 = VisaApplicationFactory(
            application_unique_application_number="1300-7658-5457-7686",
            gwf="GWF487491403",
            visa_status="Issued",
            visa_decision_date=datetime(2025, 10, 2, 0, 0, tzinfo=timezone.utc),
            application_event_datetime=datetime(2025, 9, 2, 0, 0, tzinfo=timezone.utc),
            title="Title 2",
        )
        self.visa3 = VisaApplicationFactory(
            application_unique_application_number="1300-7658-5457-7686",
            gwf="GWF347840192",
            visa_status="Issued",
            visa_decision_date=datetime(2025, 10, 3, 0, 0, tzinfo=timezone.utc),
            application_event_datetime=datetime(2025, 9, 3, 0, 0, tzinfo=timezone.utc),
        )
        self.check = DevCheckV2Factory(
            check_type_id=CheckType.Id.SPONSOR_DBS,
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        self.check.AR.add(self.ar1)

        self.referral = SafeguardingReferralFactory(person=self.guest1)
        self.notification = SafeguardingNotificationFactory(
            alert_type=SafeguardingNotification.AlertType.SAFEGUARDING_CHECK,
            sponsor_ids=[self.sponsor.id],
            dev_check_v2=self.check,
        )
        self.user = get_ukvi_user()
        self.client.force_login(self.user)

    def test_alert_detail_view_shows_all_sponsor_dbs_visa_applications(self):
        url = reverse(
            "safeguarding:detail-central-safeguarding-check-detail",
            args=[self.guest1.pk, self.referral.pk, self.notification.pk],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.visa1.gwf)
        self.assertContains(response, self.visa2.gwf)
        self.assertContains(response, self.visa1.visa_status)
        self.assertContains(response, self.visa2.visa_status)
        self.assertContains(response, self.visa1.title)
        self.assertContains(response, self.visa2.title)
        self.assertContains(response, "1 October 2025")
        self.assertContains(response, "2 October 2025")
        self.assertContains(response, "1 September 2025")
        self.assertContains(response, "2 September 2025")


class AccommodationExistsVisaApplicationAlertTests(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.guest1 = MvPersonFactory(application_number=["1300-3423-3462-9435"])
        self.guest2 = MvPersonFactory(application_number=["1300-7658-5457-7686"])
        self.guest3 = MvPersonFactory(
            application_number=["1300-7658-5457-7687", "1300-7658-5457-7688"]
        )

        self.visa1 = VisaApplicationFactory(
            application_unique_application_number="1300-3423-3462-9435",
            gwf="GWF137686345",
            visa_status="Issued",
            visa_decision_date=datetime(2025, 10, 1, 0, 0, tzinfo=timezone.utc),
            application_event_datetime=datetime(2025, 9, 1, 0, 0, tzinfo=timezone.utc),
        )
        self.visa2 = VisaApplicationFactory(
            application_unique_application_number="1300-7658-5457-7686",
            gwf="GWF487491403",
            visa_status="Issued",
            visa_decision_date=datetime(2025, 10, 2, 0, 0, tzinfo=timezone.utc),
            application_event_datetime=datetime(2025, 9, 2, 0, 0, tzinfo=timezone.utc),
        )
        self.visa3 = VisaApplicationFactory(
            application_unique_application_number="1300-7658-5457-7687",
            gwf="GWF347840193",
            visa_status="Issued",
            visa_decision_date=datetime(2025, 10, 3, 0, 0, tzinfo=timezone.utc),
            application_event_datetime=datetime(2025, 9, 3, 0, 0, tzinfo=timezone.utc),
        )
        self.visa4 = VisaApplicationFactory(
            application_unique_application_number="1300-7658-5457-7688",
            gwf="GWF347840194",
            visa_status="Issued",
            visa_decision_date=datetime(2025, 10, 3, 0, 0, tzinfo=timezone.utc),
            application_event_datetime=datetime(2025, 9, 3, 0, 0, tzinfo=timezone.utc),
        )
        self.visa5 = VisaApplicationFactory(
            application_unique_application_number="1300-7658-5457-7689",
            gwf="GWF347840199",
            visa_status="Issued",
            visa_decision_date=datetime(2025, 10, 3, 0, 0, tzinfo=timezone.utc),
            application_event_datetime=datetime(2025, 9, 3, 0, 0, tzinfo=timezone.utc),
        )

        self.check = DevCheckV2Factory(
            check_type_id=CheckType.Id.ACCOMM_EXISTS,
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        self.check.person.set([self.guest1, self.guest2, self.guest3])

        self.referral = SafeguardingReferralFactory(person=self.guest1)
        self.notification = SafeguardingNotificationFactory(
            alert_type=SafeguardingNotification.AlertType.SAFEGUARDING_CHECK,
            dev_check_v2=self.check,
        )
        self.user = get_ukvi_user()
        self.client.force_login(self.user)

    def test_alert_detail_view_shows_all_related_visa_applications(self):
        url = reverse(
            "safeguarding:detail-central-safeguarding-check-detail",
            args=[self.guest1.pk, self.referral.pk, self.notification.pk],
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GWF137686345")
        self.assertContains(response, "GWF487491403")
        self.assertContains(response, "GWF347840193")
        self.assertContains(response, "GWF347840194")
        self.assertNotContains(response, "GWF347840199")


class NoVisaApplicationsAlertTests(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sponsor = MvVolunteerFactory(
            application_unique_application_number=["1300-9999-9999-9999"]
        )
        self.ar = MvAccommodationRequestFactory()
        self.guest = MvPersonFactory(accommodation_request=self.ar)
        self.check = DevCheckV2Factory(
            check_type_id=CheckType.Id.SPONSOR_DBS,
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        self.check.AR.add(self.ar)
        self.referral = SafeguardingReferralFactory(person=self.guest)
        self.notification = SafeguardingNotificationFactory(
            alert_type=SafeguardingNotification.AlertType.SAFEGUARDING_CHECK,
            sponsor_ids=[self.sponsor.id],
            dev_check_v2=self.check,
        )
        self.user = get_ukvi_user()
        self.client.force_login(self.user)

    def test_alert_detail_view_shows_no_visa_applications_placeholder(self):
        url = reverse(
            "safeguarding:detail-central-safeguarding-check-detail",
            args=[self.guest.pk, self.referral.pk, self.notification.pk],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No visa applications found")
