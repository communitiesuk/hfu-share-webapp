from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import (
    CheckType,
    DevCheckV2,
    SafeguardingReferral,
)
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
    SafeguardingNotificationFactory,
    SafeguardingReferralFactory,
)
from safeguarding.views import (
    SafeguardingDetailCentralSafeguardingView,
)
from user_management.tests.base import (
    get_admin_user,
)


class SafeguardingDetailCentralSafeguardingViewTestCase(
    TestSessionTokenMixin, TestCase
):
    def setUp(self):
        super().setUp()
        self.client.force_login(get_admin_user())
        self.accommodation = MvAccommodationFactory()
        self.sponsor = MvVolunteerFactory()
        self.accommodation_request = MvAccommodationRequestFactory(
            primary_accommodation=self.accommodation, primary_sponsor=self.sponsor
        )
        self.person = MvPersonFactory(
            gwf=["GWF999999"], accommodation_request=self.accommodation_request
        )
        self.referral = SafeguardingReferralFactory(
            person=self.person,
            alerted_status=SafeguardingReferral.AlertedStatus.ALERTED,
        )

        self.accomm_check = DevCheckV2Factory(
            check_type_id=CheckType.Id.ACCOMM_SUITABLE,
            check_status=DevCheckV2.CheckStatus.FAILED,
            check_subtype=DevCheckV2.SuitabilityFailure.OVERCROWDED,
        )
        self.accomm_check.accommodation.set([self.accommodation])
        self.accomm_check.AR.set([self.accommodation_request])

        self.accomm_notification = SafeguardingNotificationFactory(
            ar=self.accommodation_request,
            dev_check_v2=self.accomm_check,
            name="Accommodation suitable check failed",
            description="Accommodation is overcrowded or at risk of overcrowding.",
            accommodation_ids=[str(self.accommodation.id)],
        )

        self.sponsor_dbs_check = DevCheckV2Factory(
            check_type_id=CheckType.Id.SPONSOR_DBS,
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        self.sponsor_dbs_check.AR.set([self.accommodation_request])
        self.sponsor_dbs_check.sponsor.set([self.sponsor])

        self.sponsor_notification = SafeguardingNotificationFactory(
            ar=self.accommodation_request,
            dev_check_v2=self.sponsor_dbs_check,
            name="DBS check and Sponsor suitable check failed",
            sponsor_ids=[str(self.sponsor.id)],
        )

        self.url = reverse(
            "safeguarding:detail-central-safeguarding",
            args=[self.person.pk, str(self.referral.id)],
        )

    def test_central_safeguarding_page_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Central safeguarding")
        self.assertContains(response, "GWF999999")

    def test_alerted_status_selected(self):
        response = self.client.get(self.url)
        self.assertRegex(response.content.decode(), r'value="Alerted"\s+checked')

    def test_accommodation_and_sponsor_dbs_checks_displayed(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Accommodation suitable check failed")
        self.assertContains(
            response, "Accommodation is overcrowded or at risk of overcrowding."
        )
        self.assertContains(response, "DBS check and Sponsor suitable check failed")


class SafeguardingDetailCentralSafeguardingViewGetDetailsTest(TestCase):
    def setUp(self):
        self.person = MvPersonFactory()
        self.accommodation = MvAccommodationFactory()
        self.sponsor = MvVolunteerFactory()
        self.accommodation_request = self.person.accommodation_request
        self.accommodation_request.primary_accommodation = self.accommodation
        self.accommodation_request.primary_sponsor = self.sponsor
        self.accommodation_request.save()
        self.referral = SafeguardingReferralFactory(person=self.person)
        self.check_accomm_exists = DevCheckV2Factory(
            AR=[self.accommodation_request],
            check_type_id=CheckType.Id.ACCOMM_EXISTS,
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        self.check_accomm_exists.accommodation.set([self.accommodation])
        self.check_accomm_suitable = DevCheckV2Factory(
            AR=[self.accommodation_request],
            check_type_id=CheckType.Id.ACCOMM_SUITABLE,
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        self.check_accomm_suitable.accommodation.set([self.accommodation])
        self.check_sponsor_dbs = DevCheckV2Factory(
            AR=[self.accommodation_request],
            check_type_id=CheckType.Id.SPONSOR_DBS,
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        self.check_sponsor_dbs.sponsor.set([self.sponsor])
        self.check_group_arrived = DevCheckV2Factory(
            AR=[self.accommodation_request],
            check_type_id=CheckType.Id.GROUP_ARRIVED,
            check_status=DevCheckV2.CheckStatus.FAILED,
        )
        SafeguardingNotificationFactory(
            ar=self.accommodation_request,
            dev_check_v2=self.check_accomm_exists,
            name="Accommodation exists check failed",
        )
        SafeguardingNotificationFactory(
            ar=self.accommodation_request,
            dev_check_v2=self.check_accomm_suitable,
            name="Accommodation suitable check failed",
        )
        SafeguardingNotificationFactory(
            ar=self.accommodation_request,
            dev_check_v2=self.check_sponsor_dbs,
            name="DBS check and Sponsor suitable check failed",
        )
        self.view = SafeguardingDetailCentralSafeguardingView()
        self.view.kwargs = {"pk": self.person.pk, "referral_id": str(self.referral.id)}
        self.view.get_object = lambda: self.person

    def test_get_details_returns_expected_checks(self):
        person, referral, notifications = self.view.get_details()
        self.assertEqual(person, self.person)
        self.assertEqual(str(referral.id), str(self.referral.id))
        check_type_ids = {
            n.dev_check_v2.check_type_id
            for n in notifications
            if getattr(n, "dev_check_v2", None)
        }
        self.assertIn(CheckType.Id.ACCOMM_EXISTS, check_type_ids)
        self.assertIn(CheckType.Id.ACCOMM_SUITABLE, check_type_ids)
        self.assertIn(CheckType.Id.SPONSOR_DBS, check_type_ids)
        self.assertNotIn(CheckType.Id.GROUP_ARRIVED, check_type_ids)
        self.assertEqual(len(notifications), 3)

    def test_get_details_includes_sponsor_withdrawn_notification(self):
        reason = "Sponsor no longer available"
        alert = SafeguardingNotificationFactory(
            ar=self.accommodation_request,
            name="Sponsor withdrawn",
            alert_type="SPONSOR_WITHDRAWN",
            description=reason,
            sponsor_ids=[str(self.sponsor.id)],
            created_at=timezone.now(),
        )
        _, _, notifications = self.view.get_details()
        self.assertIn(alert.id, {n.id for n in notifications})
        sponsor_withdrawn = next(n for n in notifications if n.id == alert.id)
        self.assertEqual(sponsor_withdrawn.name, "Sponsor withdrawn")
        self.assertEqual(sponsor_withdrawn.alert_type, "SPONSOR_WITHDRAWN")
        self.assertEqual(sponsor_withdrawn.description, reason)
        self.assertIsNone(sponsor_withdrawn.dev_check_v2)
        self.assertIn(str(self.sponsor.id), sponsor_withdrawn.sponsor_ids or [])
