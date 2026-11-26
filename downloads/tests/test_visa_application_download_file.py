from collections import deque
from unittest.mock import call, patch

from django.urls import reverse

from accounts.enums import GroupType
from accounts.tests.base import TestSessionTokenMixin
from downloads.forms import DownloadType
from ontology.models import VisaApplication
from ontology.tests.factories import (
    VisaApplicationFactory,
)
from test_utils.base import BaseTestCase
from user_management.tests.base import (
    UserGroup,
    get_admin_user,
    get_da_user,
    get_user_with_groups,
)


class DownloadsViewVisaApplicationTestCase(TestSessionTokenMixin, BaseTestCase):
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

    @patch("downloads.views.time.perf_counter", side_effect=[0, 2])
    @patch("downloads.views.sentry_sdk.metrics.distribution")
    @patch("downloads.views.sentry_sdk.metrics.count")
    def test_sponsor_download_sends_sentry_metric(
        self, sentry_metrics_count, sentry_metrics_distribution, perf_counter
    ):
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

        # Exhaust the iterator into an empty deque
        deque(response.streaming_content, maxlen=0)

        expected_call_attributes = {
            "download_type": "visa_applications",
            "user_id": user.id,
        }

        expected_completed_call_attributes = {
            "download_type": "visa_applications",
            "duration_bucket": "0-5s",
            "row_count_bucket": "0-100",
            "file_size_bucket": "0-1MB",
        }

        self.assertEqual(sentry_metrics_count.call_count, 2)
        self.assertEqual(
            sentry_metrics_count.call_args_list,
            [
                call("csv_download", 1, attributes=expected_call_attributes),
                call("completed_csv_download", 1, attributes=expected_call_attributes),
            ],
        )

        self.assertEqual(sentry_metrics_distribution.call_count, 3)

        duration_call, size_call, rows_call = sentry_metrics_distribution.call_args_list

        self.assertEqual(
            duration_call,
            call(
                "csv_download_duration",
                2,
                unit="second",
                attributes=expected_completed_call_attributes,
            ),
        )
        self.assertEqual(
            rows_call,
            call(
                "csv_download_rows",
                1,
                unit="none",
                attributes=expected_completed_call_attributes,
            ),
        )

        # size: present and positive (file is not empty); exact value is not meaningful
        self.assertEqual(size_call.args[0], "csv_download_size")
        self.assertGreater(size_call.args[1], 0)
        self.assertEqual(size_call.kwargs["unit"], "byte")
        self.assertEqual(
            size_call.kwargs["attributes"], expected_completed_call_attributes
        )
