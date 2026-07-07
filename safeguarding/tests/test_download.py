import csv
from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import (
    SafeguardingReferral,
)
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
    SafeguardingNotificationFactory,
    SafeguardingReferralFactory,
    VisaApplicationFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_ukvi_user,
)


class EscalatedChecksCSVDownloadViewTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(get_ukvi_user())
        self.url = reverse("safeguarding:escalated_checks_download_csv")
        self.sponsor1 = MvVolunteerFactory(
            first_name="Sponsor",
            last_name="One",
            date_of_birth=datetime(1970, 1, 1),
            residential_postcodes=["AB12 3CD"],
            passport_details=["333222789"],
            application_unique_application_number=["3423-3432-3244-3424"],
        )
        self.sponsor2 = MvVolunteerFactory(
            first_name="Sponsor",
            last_name="Two",
            date_of_birth=datetime(1980, 2, 2),
            residential_postcodes=["EF45 6GH"],
            passport_details=["222222789"],
            application_unique_application_number=["3423-3432-3244-3425"],
        )
        self.accommodation1 = MvAccommodationFactory()
        self.accommodation2 = MvAccommodationFactory()
        self.accommodation_request1 = MvAccommodationRequestFactory(
            primary_sponsor=self.sponsor1,
            primary_accommodation=self.accommodation1,
            utla_name=["UTLA1"],
        )
        self.accommodation_request2 = MvAccommodationRequestFactory(
            primary_sponsor=self.sponsor2,
            primary_accommodation=self.accommodation2,
            utla_name=["UTLA2"],
        )
        self.person1 = MvPersonFactory(
            accommodation_request=self.accommodation_request1,
            first_name="Alice",
            last_name="Johnson",
            date_of_birth=datetime(1995, 3, 3),
            passport_id=["123456789"],
            gwf=["GWF111111222"],
            application_number=["3423-3432-3244-3424"],
            visa_status="Issued",
        )
        self.person2 = MvPersonFactory(
            accommodation_request=self.accommodation_request2,
            first_name="Bob",
            last_name="Smith",
            date_of_birth=datetime(1990, 4, 4),
            passport_id=["123222789"],
            gwf=["GWF222222111"],
            application_number=["3423-3432-3244-3425"],
            visa_status="Pending",
        )
        VisaApplicationFactory(
            application_unique_application_number="3423-3432-3244-3424",
            applicant_final_address="1 Street, Bristol, BR1 3CD",
        )
        VisaApplicationFactory(
            application_unique_application_number="3423-3432-3244-3425",
            applicant_final_address="2 Avenue, Manchester, MA1 3SW",
        )
        referral1_created_at = timezone.make_aware(datetime(2025, 6, 3, 13, 34, 0))
        self.referral1 = SafeguardingReferralFactory(
            person=self.person1,
            alerted_status=SafeguardingReferral.AlertedStatus.ALERTED,
            created_at=referral1_created_at,
        )
        referral2_created_at = timezone.make_aware(datetime(2025, 6, 4, 14, 35, 0))
        self.referral2 = SafeguardingReferralFactory(
            person=self.person2,
            alerted_status=SafeguardingReferral.AlertedStatus.NOT_ALERTED,
            created_at=referral2_created_at,
        )
        SafeguardingNotificationFactory(
            ar=self.accommodation_request1,
            created_at=timezone.make_aware(datetime(2025, 6, 3, 13, 35, 0)),
        )
        SafeguardingNotificationFactory(
            ar=self.accommodation_request2,
            created_at=timezone.make_aware(datetime(2025, 6, 4, 14, 36, 0)),
        )

    def test_download_csv(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertTrue(
            response["Content-Disposition"].startswith("attachment; filename=")
        )
        self.assertIn("escalated_checks-", response["Content-Disposition"])

    def test_csv_headers(self):
        response = self.client.get(self.url)
        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")
        headers = content[0].split(",")
        expected_headers = [
            "Applicant Full Name",
            "Applicant Date Of Birth",
            "Applicant Passport Number",
            "Applicant GWF(s)",
            "Applicant UAN(s)",
            "Visa Status",
            "Sponsor Name",
            "Sponsor DOB",
            "Sponsor Full Address",
            "Sponsor Passport",
            "UTLA",
        ]
        self.assertEqual(headers, expected_headers)

    def test_csv_content(self):
        response = self.client.get(self.url)
        lines = b"".join(response.streaming_content).decode("utf-8").split("\r\n")
        reader = csv.DictReader(lines)
        data_rows = list(reader)
        self.assertEqual(len(data_rows), 2)

        expected_rows = [
            {
                "Applicant Full Name": "Bob Smith",
                "Applicant Date Of Birth": "1990-04-04",
                "Applicant Passport Number": "123222789",
                "Applicant GWF(s)": "GWF222222111",
                "Applicant UAN(s)": "3423-3432-3244-3425",
                "Visa Status": "Pending",
                "Sponsor Name": "Sponsor Two",
                "Sponsor DOB": "1980-02-02",
                "Sponsor Full Address": "2 Avenue, Manchester, MA1 3SW",
                "Sponsor Passport": "222222789",
                "UTLA": "UTLA2",
            },
            {
                "Applicant Full Name": "Alice Johnson",
                "Applicant Date Of Birth": "1995-03-03",
                "Applicant Passport Number": "123456789",
                "Applicant GWF(s)": "GWF111111222",
                "Applicant UAN(s)": "3423-3432-3244-3424",
                "Visa Status": "Issued",
                "Sponsor Name": "Sponsor One",
                "Sponsor DOB": "1970-01-01",
                "Sponsor Full Address": "1 Street, Bristol, BR1 3CD",
                "Sponsor Passport": "333222789",
                "UTLA": "UTLA1",
            },
        ]
        for i, expected_row in enumerate(expected_rows):
            for key, value in expected_row.items():
                self.assertEqual(data_rows[i][key].strip('"'), value.strip('"'))

    def test_csv_filter_visa_status_and_alerted_status(self):
        person3 = MvPersonFactory(
            accommodation_request=self.accommodation_request1,
            first_name="Charlie",
            last_name="Brown",
            date_of_birth=datetime(1988, 5, 5),
            passport_id=["999999999"],
            gwf=["GWF333333"],
            application_number=["3423-3432-3244-3426"],
            visa_status="Pending",
        )

        SafeguardingReferralFactory(
            person=person3,
            alerted_status=SafeguardingReferral.AlertedStatus.SOME_ALERTED,
            created_at=timezone.make_aware(datetime(2025, 6, 5, 15, 36, 0)),
        )

        # Filter by visa_status=Issued (should only include person1)
        response = self.client.get(self.url + "?visa_status=Issued")
        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")
        self.assertEqual(len(content), 3)  # header + sgr row + newline
        self.assertTrue(any("Alice Johnson" in line for line in content))
        self.assertFalse(any("Bob Smith" in line for line in content))
        self.assertFalse(any("Charlie Brown" in line for line in content))

        # Filter by visa_status=Pending (should include Bob and Charlie)
        response = self.client.get(self.url + "?visa_status=Pending")
        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")
        self.assertEqual(len(content), 4)  # header + sgr row + newline
        self.assertFalse(any("Alice Johnson" in line for line in content))
        self.assertTrue(any("Bob Smith" in line for line in content))
        self.assertTrue(any("Charlie Brown" in line for line in content))

        # Filter by alerted_status=Some Alerted (should only include Charlie)
        response = self.client.get(self.url + "?alerted_status=Some+Alerted")
        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")
        self.assertEqual(len(content), 3)  # header + sgr row + newline
        self.assertFalse(any("Alice Johnson" in line for line in content))
        self.assertFalse(any("Bob Smith" in line for line in content))
        self.assertTrue(any("Charlie Brown" in line for line in content))


class EscalatedChecksCSVDownloadViewTwoTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(get_ukvi_user())
        self.url = reverse("safeguarding:escalated_checks_download_csv")

    def test_csv_handles_referral_with_no_person(self):
        SafeguardingReferralFactory(person=None, person_id="non-existsent-id-123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")
        header = content[0].split(",")
        self.assertIn("Applicant Full Name", header)
        self.assertEqual(len(content), 3)  # header + sgr row + newline

    def test_csv_handles_referral_with_broken_person_to_ar_fk(self):
        person = MvPersonFactory(
            accommodation_request=None,
            accommodation_request_id="nonexistent_id",
        )

        SafeguardingReferralFactory(person=person)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")
        header = content[0].split(",")
        self.assertIn("Applicant Full Name", header)
        self.assertEqual(len(content), 3)  # header + sgr row + newline

    def test_csv_handles_referral_with_broken_ar_to_sponsor_fk(self):
        accommodation_request = MvAccommodationRequestFactory(
            primary_sponsor_id="nonexistent_id",
        )

        person = MvPersonFactory(accommodation_request=accommodation_request)

        SafeguardingReferralFactory(person=person)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")
        header = content[0].split(",")
        self.assertIn("Applicant Full Name", header)
        self.assertEqual(len(content), 3)  # header + sgr row + newline


class EscalatedChecksCSVDownloadWithNoARTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.client.force_login(get_ukvi_user())
        self.url = reverse("safeguarding:escalated_checks_download_csv")

        self.sponsor1 = MvVolunteerFactory(
            first_name="Sponsor",
            last_name="One",
            date_of_birth=datetime(1970, 1, 1),
            residential_postcodes=["AB12 3CD"],
            passport_details=["333222789"],
        )

        self.person1 = MvPersonFactory(
            accommodation_request=None,
            accommodation_request_id="nonexistent_id",
            first_name="Alice",
            last_name="Johnson",
            date_of_birth=datetime(1995, 3, 3),
            passport_id=["123456789"],
            gwf=["GWF111111222"],
            application_number=["3423-3432-3244-3424"],
            visa_status="Issued",
        )

        referral1_created_at = timezone.make_aware(datetime(2025, 6, 3, 13, 34, 0))
        self.referral1 = SafeguardingReferralFactory(
            person=self.person1,
            alerted_status=SafeguardingReferral.AlertedStatus.ALERTED,
            created_at=referral1_created_at,
        )

    def test_csv_content(self):
        response = self.client.get(self.url)

        # Doesn't 500 due to foreign key constraint on AR_id
        self.assertEqual(response.status_code, 200)


class EscalatedChecksCSVDownloadPermissionsTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("safeguarding:escalated_checks_download_csv")

    def test_ukvi_user_can_download(self):
        self.client.force_login(get_ukvi_user())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])

    def test_admin_user_can_download(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])

    def test_la_user_cannot_download(self):
        self.client.force_login(get_la_user())
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_da_user_cannot_download(self):
        self.client.force_login(get_da_user())
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_mhclg_user_cannot_download(self):
        self.client.force_login(get_mhclg_user())
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)
