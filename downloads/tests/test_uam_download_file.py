from collections import deque
from unittest.mock import call, patch

from django.urls import reverse

from accounts.enums import GroupType
from accounts.tests.base import TestSessionTokenMixin
from downloads.forms import DownloadType
from ontology.models import SponsorshipCertificationForm
from ontology.tests.factories import (
    SponsorshipCertificationFormFactory,
)
from test_utils.base import BaseTestCase
from user_management.tests.base import (
    UserGroup,
    get_admin_user,
    get_da_user,
    get_user_with_groups,
)


class DownloadsViewUamTestCase(TestSessionTokenMixin, BaseTestCase):
    def test_da_download_view_uam_data_csv(self):
        user = get_da_user()
        self.client.force_login(user)

        uams_data_details = {
            "given_name": "Joe",
            "family_name": "Doe",
            "sponsor_date_of_birth": "2000-01-01",
            "email": "joe.doe@example.com",
            "identification_type": "passport",
            "identification_number": "1234512345",
            "residential_postcode": "12345",
            "residential_town": "Sutton",
            "ltla_name": ["City of Edinburgh"],
            "reference": "UAM-123123",
            "created_at": "2024-01-18 09:57:23.860782+00",
        }

        SponsorshipCertificationFormFactory(**uams_data_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.UAMS},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check row count
        self.assertEqual(len(content), 3)  # header + one row + empty line

        # check header
        header = content[0].split(",")
        uams_data_details_keys = uams_data_details.keys()
        self.assertTrue(column_name in header for column_name in uams_data_details_keys)
        self.assertIn("created_at_tz", header)

        # check row
        new_row = next((row for row in content if "UAM-123123" in row), None)

        # check row
        self.assertIsNotNone(new_row)
        self.assertIn("UTC", new_row)

        # check row length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_da_download_view_uam_data_without_created_at_csv(self):
        user = get_da_user()
        self.client.force_login(user)

        uams_data_details = {
            "given_name": "Joe",
            "family_name": "Doe",
            "sponsor_date_of_birth": "2000-01-01",
            "email": "joe.doe@example.com",
            "identification_type": "passport",
            "identification_number": "1234512345",
            "residential_postcode": "12345",
            "residential_town": "Sutton",
            "ltla_name": ["City of Edinburgh"],
            "reference": "UAM-123123",
        }

        SponsorshipCertificationFormFactory(**uams_data_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.UAMS},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check row count
        self.assertEqual(len(content), 3)  # header + one row + empty line

        # check header
        header = content[0].split(",")
        uams_data_details_keys = uams_data_details.keys()
        self.assertTrue(column_name in header for column_name in uams_data_details_keys)

        # check row
        new_row = next((row for row in content if "UAM-123123" in row), None)

        # check row
        self.assertIsNotNone(new_row)
        self.assertNotIn("UTC", new_row)

        # check row length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_admin_download_view_uam_data_csv(self):
        user = get_admin_user()
        self.client.force_login(user)

        uams_data_details = {
            "given_name": "Joe",
            "family_name": "Doe",
            "sponsor_date_of_birth": "2000-01-01",
            "email": "joe.doe@example.com",
            "identification_type": "passport",
            "identification_number": "1234512345",
            "residential_postcode": "12345",
            "residential_town": "Sutton",
            "ltla_name": ["Croydon"],
            "reference": "UAM-123123",
            "created_at": "2024-01-18 09:57:23.860782+00",
        }

        SponsorshipCertificationFormFactory(**uams_data_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.UAMS},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check row count
        self.assertEqual(len(content), 3)  # header + one row + empty line

        # check header
        header = content[0].split(",")
        uams_data_details_keys = uams_data_details.keys()
        self.assertTrue(column_name in header for column_name in uams_data_details_keys)
        self.assertIn("created_at_tz", header)

        # check row
        new_row = next((row for row in content if "UAM-123123" in row), None)

        # check row
        self.assertIsNotNone(new_row)
        self.assertIn("UTC", new_row)

        # check row length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_admin_download_view_uam_data_without_created_at_csv(self):
        user = get_admin_user()
        self.client.force_login(user)

        uams_data_details = {
            "given_name": "Joe",
            "family_name": "Doe",
            "sponsor_date_of_birth": "2000-01-01",
            "email": "joe.doe@example.com",
            "identification_type": "passport",
            "identification_number": "1234512345",
            "residential_postcode": "12345",
            "residential_town": "Sutton",
            "ltla_name": ["Croydon"],
            "reference": "UAM-123123",
        }

        SponsorshipCertificationFormFactory(**uams_data_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.UAMS},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check row count
        self.assertEqual(len(content), 3)  # header + one row + empty line

        # check header
        header = content[0].split(",")
        uams_data_details_keys = uams_data_details.keys()
        self.assertTrue(column_name in header for column_name in uams_data_details_keys)

        # check row
        new_row = next((row for row in content if "UAM-123123" in row), None)

        # check row
        self.assertIsNotNone(new_row)
        self.assertNotIn("UTC", new_row)

        # check row length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_bromley_la_download_view_uam_csv(self):
        user = get_user_with_groups(
            [UserGroup(name="Bromley", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        uams_data_details = {
            "given_name": "Joe",
            "family_name": "Doe",
            "sponsor_date_of_birth": "2000-01-01",
            "email": "joe.doe@example.com",
            "identification_type": "passport",
            "identification_number": "1234512345",
            "residential_postcode": "12345",
            "residential_town": "Sutton",
            "ltla_name": ["Bromley"],
            "reference": "UAM-123123",
            "created_at": "2024-01-18 09:57:23.860782+00",
        }

        SponsorshipCertificationFormFactory(**uams_data_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.UAMS},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check row count
        self.assertEqual(len(content), 3)  # header + one row + empty line

        # check header
        header = content[0].split(",")
        uams_data_details_keys = uams_data_details.keys()
        self.assertTrue(column_name in header for column_name in uams_data_details_keys)

        # check row
        new_row = next((row for row in content if "UAM-123123" in row), None)

        # check row
        self.assertIsNotNone(new_row)
        self.assertIn("UTC", new_row)

        # check row length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_lewisham_la_does_not_see_bromley_data_download_view_uam_csv(self):
        user = get_user_with_groups(
            [UserGroup(name="Lewisham", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        uams_data_details = {
            "given_name": "Joe",
            "family_name": "Doe",
            "sponsor_date_of_birth": "2000-01-01",
            "email": "joe.doe@example.com",
            "identification_type": "passport",
            "identification_number": "1234512345",
            "residential_postcode": "12345",
            "residential_town": "Sutton",
            "ltla_name": ["Bromley"],
            "reference": "UAM-123123",
            "created_at": "2024-01-18 09:57:23.860782+00",
        }

        SponsorshipCertificationFormFactory(**uams_data_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.UAMS},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check row count
        self.assertEqual(len(content), 2)  # header + empty line

        # check header
        header = content[0].split(",")
        uams_data_details_keys = uams_data_details.keys()
        self.assertTrue(column_name in header for column_name in uams_data_details_keys)

        # check row
        new_row = next((row for row in content if "UAM-123123" in row), None)

        # check row is not found
        self.assertIsNone(new_row)

    def test_should_use_get_for_user_method_when_retrieving_objects(self):
        user = get_user_with_groups(
            [UserGroup(name="Lewisham", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        uams_data_details = {
            "given_name": "Joe",
            "family_name": "Doe",
            "sponsor_date_of_birth": "2000-01-01",
            "email": "joe.doe@example.com",
            "identification_type": "passport",
            "identification_number": "1234512345",
            "residential_postcode": "12345",
            "residential_town": "Sutton",
            "ltla_name": ["Bromley"],
            "reference": "UAM-123123",
            "created_at": "2024-01-18 09:57:23.860782+00",
        }

        SponsorshipCertificationFormFactory(**uams_data_details)

        with patch.object(
            SponsorshipCertificationForm.objects.__class__, "get_for_user"
        ) as mock_get_for_user:
            mock_get_for_user.return_value = SponsorshipCertificationForm.objects.none()
            response = self.client.post(
                reverse("downloads:download-page"),
                data={"download_type": DownloadType.UAMS},
            )

            # Exhaust the iterator into an empty deque
            deque(response.streaming_content, maxlen=0)

            mock_get_for_user.assert_called()

    @patch("downloads.views.time.perf_counter", side_effect=[0, 2])
    @patch("downloads.views.sentry_sdk.metrics.distribution")
    @patch("downloads.views.sentry_sdk.metrics.count")
    def test_uam_download_sends_sentry_metric(
        self, sentry_metrics_count, sentry_metrics_distribution, perf_counter
    ):
        user = get_da_user()
        self.client.force_login(user)

        uams_data_details = {
            "given_name": "Joe",
            "family_name": "Doe",
            "sponsor_date_of_birth": "2000-01-01",
            "email": "joe.doe@example.com",
            "identification_type": "passport",
            "identification_number": "1234512345",
            "residential_postcode": "12345",
            "residential_town": "Sutton",
            "ltla_name": ["City of Edinburgh"],
            "reference": "UAM-123123",
            "created_at": "2024-01-18 09:57:23.860782+00",
        }

        SponsorshipCertificationFormFactory(**uams_data_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.UAMS},
        )

        # Exhaust the iterator into an empty deque
        deque(response.streaming_content, maxlen=0)

        expected_call_attributes = {
            "download_type": "uams",
            "user_id": user.id,
        }

        expected_completed_call_attributes = {
            "download_type": "uams",
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
