from django.test import TestCase

from ontology.models import VisaApplication
from ontology.tests.factories import VisaApplicationFactory
from visa_applications.views import VisaApplicationsTableFilter


class VisaApplicationFilterTestCase(TestCase):
    def setUp(self):
        self.app1 = VisaApplicationFactory(
            application_unique_application_number="UAN123",
            Q44g_full_name="John Doe",
            visa_status="Approved",
            application_event_datetime="2023-01-01T00:00:00Z",
            visa_decision_date="2023-01-11T00:00:00Z",
            Q11b_applicant_date_of_birth="1993-01-01",
        )
        self.app2 = VisaApplicationFactory(
            application_unique_application_number="UAN789",
            Q44g_full_name="Jane Smith",
            visa_status="Pending",
            application_event_datetime="2023-02-01T00:00:00Z",
            visa_decision_date="2023-02-10T00:00:00Z",
            Q11b_applicant_date_of_birth="2010-01-01",
        )

    def test_filter_by_application_event_datetime_range(self):
        filter_set = VisaApplicationsTableFilter(
            queryset=VisaApplication.objects.all(),
            data={
                "application_event_datetime_0": "2023-01-01",
                "application_event_datetime_1": "2023-01-31",
            },
        )

        results = filter_set.qs
        visa_application_ids = results.values_list(
            "application_unique_application_number",
            flat=True,
        )

        self.assertEqual(len(visa_application_ids), 1)
        self.assertIn(
            self.app1.application_unique_application_number,
            visa_application_ids,
        )
        self.assertNotIn(
            self.app2.application_unique_application_number,
            visa_application_ids,
        )

    def test_filter_by_visa_decision_date_range(self):
        filter_set = VisaApplicationsTableFilter(
            queryset=VisaApplication.objects.all(),
            data={
                "visa_decision_date_0": "2023-01-01",
                "visa_decision_date_1": "2023-01-31",
            },
        )

        results = filter_set.qs
        visa_application_ids = results.values_list(
            "application_unique_application_number", flat=True
        )

        self.assertEqual(len(visa_application_ids), 1)
        self.assertIn(
            self.app1.application_unique_application_number,
            visa_application_ids,
        )
        self.assertNotIn(
            self.app2.application_unique_application_number,
            visa_application_ids,
        )

    def test_invalid_application_event_datetime_range(self):
        filter_set = VisaApplicationsTableFilter(
            queryset=VisaApplication.objects.all(),
            data={
                "application_event_datetime_0": "2023-01-31",
                "application_event_datetime_1": "2023-01-01",
            },
        )

        self.assertFalse(filter_set.is_valid())
        self.assertIn(
            "application_event_datetime",
            filter_set.errors,
        )
        self.assertIn(
            "'Date from' must be before 'Date to'.",
            filter_set.errors["application_event_datetime"],
        )

    def test_invalid_visa_decision_date_range(self):
        filter_set = VisaApplicationsTableFilter(
            queryset=VisaApplication.objects.all(),
            data={
                "visa_decision_date_0": "2023-01-31",
                "visa_decision_date_1": "2023-01-01",
            },
        )

        self.assertFalse(filter_set.is_valid())
        self.assertIn(
            "visa_decision_date",
            filter_set.errors,
        )
        self.assertIn(
            "'Date from' must be before 'Date to'.",
            filter_set.errors["visa_decision_date"],
        )
