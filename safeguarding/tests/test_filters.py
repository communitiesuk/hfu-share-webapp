from django.db.models import DateTimeField, Max, OuterRef, Subquery
from django.test import TestCase

from ontology.models import SafeguardingNotification, SafeguardingReferral
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvPersonFactory,
    SafeguardingNotificationFactory,
    SafeguardingReferralFactory,
)
from safeguarding.views import EscalatedChecksTableFilter


class EscalatedChecksFilterTestCase(TestCase):
    def setUp(self):
        # Create a person with an escalated safeguarding notification
        self.escalated_person = MvPersonFactory(
            id="person-00001",
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-01",
            visa_status="Arrived",
        )

        self.escalated_referral = SafeguardingReferralFactory(
            id="referral-00001",
            person=self.escalated_person,
            alerted_status="Alerted",
        )

        # Create another person with a different alert status
        self.closed_person = MvPersonFactory(
            id="person-00002",
            first_name="Jane",
            last_name="Smith",
            date_of_birth="1985-05-05",
            visa_status="Pending",
        )

        self.closed_referral = SafeguardingReferralFactory(
            id="referral-00002",
            person=self.closed_person,
            alerted_status="Not Alerted",
        )

        self.escalated_referral.created_at = "2024-06-01T12:00:00Z"
        self.escalated_referral.save()
        self.closed_referral.created_at = "2024-12-01T08:00:00Z"
        self.closed_referral.save()

    def test_filter_by_visa_status(self):
        # Test filtering by Visa status
        filter_set = EscalatedChecksTableFilter(
            queryset=SafeguardingReferral.objects.all(),
            data={"visa_status": ["Arrived"]},
        )

        results = filter_set.qs
        referral_ids = results.values_list("id", flat=True)

        self.assertEqual(len(referral_ids), 1)
        self.assertIn(self.escalated_referral.id, referral_ids)
        self.assertNotIn(self.closed_referral.id, referral_ids)

        # Test filtering by Pending status
        filter_set = EscalatedChecksTableFilter(
            queryset=SafeguardingReferral.objects.all(),
            data={"visa_status": ["Pending"]},
        )

        results = filter_set.qs
        referral_ids = results.values_list("id", flat=True)

        self.assertEqual(len(referral_ids), 1)
        self.assertNotIn(self.escalated_referral.id, referral_ids)
        self.assertIn(self.closed_referral.id, referral_ids)

    def test_filter_by_date_of_birth(self):
        # Test filtering by DOB date range
        filter_set = EscalatedChecksTableFilter(
            queryset=SafeguardingReferral.objects.all(),
            data={
                "date_of_birth_0": "1989-01-01",
                "date_of_birth_1": "1991-01-01",
            },
        )

        results = filter_set.qs
        referral_ids = results.values_list("id", flat=True)

        self.assertEqual(len(referral_ids), 1)
        self.assertIn(self.escalated_referral.id, referral_ids)
        self.assertNotIn(self.closed_referral.id, referral_ids)

        # Test filtering by different date range
        filter_set = EscalatedChecksTableFilter(
            queryset=SafeguardingReferral.objects.all(),
            data={
                "date_of_birth_0": "1984-01-01",
                "date_of_birth_1": "1986-01-01",
            },
        )

        results = filter_set.qs
        referral_ids = results.values_list("id", flat=True)

        self.assertEqual(len(referral_ids), 1)
        self.assertNotIn(self.escalated_referral.id, referral_ids)
        self.assertIn(self.closed_referral.id, referral_ids)

    def test_filter_by_alerted_status(self):
        # Test filtering by Alerted status
        filter_set = EscalatedChecksTableFilter(
            queryset=SafeguardingReferral.objects.all(),
            data={"alerted_status": ["Alerted"]},
        )

        results = filter_set.qs
        referral_ids = results.values_list("id", flat=True)

        self.assertEqual(len(referral_ids), 1)
        self.assertIn(self.escalated_referral.id, referral_ids)
        self.assertNotIn(self.closed_referral.id, referral_ids)

        # Test filtering by not alerted status
        filter_set = EscalatedChecksTableFilter(
            queryset=SafeguardingReferral.objects.all(),
            data={"alerted_status": ["Not Alerted"]},
        )

        results = filter_set.qs
        referral_ids = results.values_list("id", flat=True)

        self.assertEqual(len(referral_ids), 1)
        self.assertNotIn(self.escalated_referral.id, referral_ids)
        self.assertIn(self.closed_referral.id, referral_ids)

    def test_filter_by_created_at(self):
        # Test filtering by first shared to UKVI date range
        filter_set = EscalatedChecksTableFilter(
            queryset=SafeguardingReferral.objects.all(),
            data={
                "created_at_0": "2024-01-01",
                "created_at_1": "2024-08-01",
            },
        )

        results = filter_set.qs
        referral_ids = results.values_list("id", flat=True)

        self.assertEqual(len(referral_ids), 1)

    def test_filter_by_latest_alert_date(self):
        ar1 = MvAccommodationRequestFactory(id="ar-2024")
        ar2 = MvAccommodationRequestFactory(id="ar-2025")
        self.escalated_person.accommodation_request = ar1
        self.escalated_person.save()
        self.closed_person.accommodation_request = ar2
        self.closed_person.save()

        SafeguardingReferralFactory(
            id="referral-2024",
            person=self.escalated_person,
            alerted_status="Alerted",
        )
        SafeguardingReferralFactory(
            id="referral-2025",
            person=self.closed_person,
            alerted_status="Alerted",
        )

        SafeguardingNotificationFactory(
            ar=ar1,
            created_at="2024-05-15T10:00:00Z",
        )

        SafeguardingNotificationFactory(
            ar=ar2,
            created_at="2025-03-10T09:00:00Z",
        )

        # Annotate queryset with latest_alert_date
        latest_alert_date_subquery = (
            SafeguardingNotification.objects.filter(
                ar=OuterRef("person__accommodation_request")
            )
            .values("ar")
            .annotate(max_date=Max("created_at"))
            .values("max_date")[:1]
        )
        qs = SafeguardingReferral.objects.annotate(
            latest_alert_date=Subquery(
                latest_alert_date_subquery, output_field=DateTimeField()
            )
        )

        # Filter for 2024 only
        filter_set = EscalatedChecksTableFilter(
            queryset=qs,
            data={
                "latest_alert_date_0": "2024-01-01",
                "latest_alert_date_1": "2024-12-31",
            },
        )
        results = filter_set.qs
        referral_ids = set(results.values_list("id", flat=True))
        self.assertIn("referral-2024", referral_ids)
        self.assertNotIn("referral-2025", referral_ids)

        # Filter for 2025 only
        filter_set = EscalatedChecksTableFilter(
            queryset=qs,
            data={
                "latest_alert_date_0": "2025-01-01",
                "latest_alert_date_1": "2025-12-31",
            },
        )
        results = filter_set.qs
        referral_ids = set(results.values_list("id", flat=True))
        self.assertNotIn("referral-2024", referral_ids)
        self.assertIn("referral-2025", referral_ids)

        # Filter for both years
        filter_set = EscalatedChecksTableFilter(
            queryset=qs,
            data={
                "latest_alert_date_0": "2024-01-01",
                "latest_alert_date_1": "2025-12-31",
            },
        )
        results = filter_set.qs
        referral_ids = set(results.values_list("id", flat=True))
        self.assertIn("referral-2024", referral_ids)
        self.assertIn("referral-2025", referral_ids)
