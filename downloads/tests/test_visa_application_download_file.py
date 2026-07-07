from collections import deque
from unittest.mock import call, patch

from django.test import TestCase
from django.urls import reverse

from accounts.enums import GroupType
from accounts.tests.base import TestSessionTokenMixin
from downloads.forms import DownloadType
from ontology.models import VisaApplication
from ontology.tests.factories import (
    VisaApplicationFactory,
)
from user_management.tests.base import (
    UserGroup,
    get_admin_user,
    get_da_user,
    get_user_with_groups,
)


class DownloadsViewVisaApplicationTestCase(TestSessionTokenMixin, TestCase):
    def test_da_download_view_visa_applications_csv(self):
        user = get_da_user()
        self.client.force_login(user)

        visa_application_details = {
            "application_unique_application_number": "VA12345",
            "visa_status": "Approved",
            "address_preference": "123 Main Street",
            "ltla_name": "City of Edinburgh",
        }

        VisaApplicationFactory(**visa_application_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.VISA_APPLICATIONS},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check row count
        self.assertEqual(len(content), 3)  # header + one row + empty line

        # check header
        header = content[0].split(",")  # header is first row in the CSV
        visa_application_details_keys = list(visa_application_details.keys())
        self.assertTrue(
            all(column_name in header for column_name in visa_application_details_keys)
        )

        # check row
        new_row = next((row for row in content if "VA12345" in row), None)

        # check row exists
        self.assertIsNotNone(new_row)

        # check row matches header length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_admin_download_view_visa_applications_csv(self):
        user = get_admin_user()
        self.client.force_login(user)

        visa_application_details = {
            "application_unique_application_number": "VA12345",
            "visa_status": "Approved",
            "address_preference": "123 Main Street",
            "ltla_name": "Bromley",
        }

        VisaApplicationFactory(**visa_application_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.VISA_APPLICATIONS},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check row count
        self.assertEqual(len(content), 3)  # header + one row + empty line

        # check header
        header = content[0].split(",")  # header is first row in the CSV
        visa_application_details_keys = list(visa_application_details.keys())
        self.assertTrue(
            all(column_name in header for column_name in visa_application_details_keys)
        )

        # check row
        new_row = next((row for row in content if "VA12345" in row), None)

        # check row exists
        self.assertIsNotNone(new_row)

        # check row matches header length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_bromley_la_download_view_visa_applications_csv(self):
        user = get_user_with_groups(
            [UserGroup(name="Bromley", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        visa_application_details = {
            "application_unique_application_number": "VA12345",
            "visa_status": "Approved",
            "address_preference": "123 Main Street",
            "ltla_name": "Bromley",
        }

        VisaApplicationFactory(**visa_application_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.VISA_APPLICATIONS},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check row count
        self.assertEqual(len(content), 3)  # header + one row + empty line

        # check header
        header = content[0].split(",")  # header is first row in the CSV
        visa_application_details_keys = list(visa_application_details.keys())
        self.assertTrue(
            all(column_name in header for column_name in visa_application_details_keys)
        )

        # check row
        new_row = next((row for row in content if "VA12345" in row), None)

        # check row exists
        self.assertIsNotNone(new_row)

        # check row matches header length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_lewisham_la_does_not_see_bromley_data_download_view_visa_applications_csv(
        self,
    ):
        user = get_user_with_groups(
            [UserGroup(name="Lewisham", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        visa_application_details = {
            "application_unique_application_number": "VA12345",
            "visa_status": "Approved",
            "address_preference": "123 Main Street",
            "ltla_name": "Bromley",
        }

        VisaApplicationFactory(**visa_application_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.VISA_APPLICATIONS},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check row exists
        self.assertEqual(len(content), 2)  # header + empty line

        # check header
        header = content[0].split(",")  # header is first row in the CSV
        visa_application_details_keys = list(visa_application_details.keys())
        self.assertTrue(
            all(column_name in header for column_name in visa_application_details_keys)
        )

        # check row
        new_row = next((row for row in content if "VA12345" in row), None)

        # check row exists
        self.assertIsNone(new_row)

    def test_should_use_get_for_user_method_when_retrieving_objects(
        self,
    ):
        user = get_user_with_groups(
            [UserGroup(name="Lewisham", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        visa_application_details = {
            "application_unique_application_number": "VA12345",
            "visa_status": "Approved",
            "address_preference": "123 Main Street",
            "ltla_name": "Bromley",
        }

        VisaApplicationFactory(**visa_application_details)

        with patch.object(
            VisaApplication.objects.__class__, "get_for_user"
        ) as mock_get_for_user:
            mock_get_for_user.return_value = VisaApplication.objects.none()

            response = self.client.post(
                reverse("downloads:download-page"),
                data={"download_type": DownloadType.VISA_APPLICATIONS},
            )

            # Exhaust the iterator into an empty deque
            deque(response.streaming_content, maxlen=0)

            mock_get_for_user.assert_called()

    @patch("downloads.views.sentry_sdk.metrics.count")
    def test_sponsor_download_sends_sentry_metric(self, sentry_metrics):
        user = get_da_user()
        self.client.force_login(user)

        self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.VISA_APPLICATIONS},
        )

        expected_call_attributes = {
            "download_type": "visa_applications",
            "user_id": user.id,
        }
        self.assertEqual(sentry_metrics.call_count, 1)
        self.assertEqual(
            sentry_metrics.call_args_list,
            [call("csv_download", 1, attributes=expected_call_attributes)],
        )
