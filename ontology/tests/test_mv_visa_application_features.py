from django.test import TestCase

from ontology.tests.factories import MvVolunteerFactory, VisaApplicationFactory


class MvPersonPermissionsTest(TestCase):
    def setUp(self):
        self.visa_application = VisaApplicationFactory(
            application_unique_application_number="123"
        )

        self.related_sponsor = MvVolunteerFactory(
            application_unique_application_number=["123"],
            email="related@example.com",
            phone_number=["111-222-333", "444-555-666"],
        )

        self.unrelated_sponsor = MvVolunteerFactory(
            application_unique_application_number=["abc"],
            email="un-related@example.com",
            phone_number=["000-999-888"],
        )

    def test_property_returns_correct_sponsor(self):
        self.assertEqual(self.visa_application.sponsor.pk, str(self.related_sponsor.pk))
        self.assertEqual(
            self.visa_application.sponsor.email, self.related_sponsor.email
        )
        self.assertEqual(
            self.visa_application.sponsor.phone_number,
            self.related_sponsor.phone_number,
        )
