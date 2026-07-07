from collections import deque
from unittest.mock import call, patch

from django.test import TestCase
from django.urls import reverse

from accounts.enums import GroupType
from accounts.tests.base import TestSessionTokenMixin
from downloads.forms import DownloadType
from ontology.models import MvAccommodation
from ontology.tests.factories import MvAccommodationFactory
from user_management.tests.base import (
    UserGroup,
    get_admin_user,
    get_da_user,
    get_user_with_groups,
)


class DownloadsViewAccommodationTestCase(TestSessionTokenMixin, TestCase):
    def test_da_download_view_accommodation_csv(self):
        user = get_da_user()
        self.client.force_login(user)

        accommodation_details = {
            "id": "accommodation-123-123-123",
            "full_address": "123 Main Street",
            "current_capacity": 5,
            "who_can_you_accommodate": "Families",
            "ltla_name": "City of Edinburgh",
        }

        MvAccommodationFactory(**accommodation_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.ACCOMMODATION},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check header
        header = content[0].split(",")  # header is first row in the CSV
        accommodation_details_keys = accommodation_details.keys()
        self.assertTrue(
            all(column_name in header for column_name in accommodation_details_keys)
        )

        # check row
        new_row = next(
            (row for row in content if "accommodation-123-123-123" in row), None
        )

        # check row exists
        self.assertIsNotNone(new_row)

        # check row matches header length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_da_download_view_accommodation_with_created_at_csv(self):
        user = get_da_user()
        self.client.force_login(user)

        accommodation_details = {
            "id": "accommodation-123-123-123",
            "full_address": "123 Main Street",
            "current_capacity": 5,
            "who_can_you_accommodate": "Families",
            "ltla_name": "City of Edinburgh",
            "created_at": "2024-01-18 09:57:23.860782+00",
        }

        MvAccommodationFactory(**accommodation_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.ACCOMMODATION},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check header
        header = content[0].split(",")  # header is first row in the CSV
        accommodation_details_keys = accommodation_details.keys()
        self.assertTrue(
            all(column_name in header for column_name in accommodation_details_keys)
        )
        self.assertIn("created_at_tz", header)

        # check row
        new_row = next(
            (row for row in content if "accommodation-123-123-123" in row), None
        )

        # check row exists
        self.assertIsNotNone(new_row)
        self.assertTrue("UTC" in new_row)

        # check row matches header length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_admin_download_view_accommodation_csv(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_details = {
            "id": "accommodation-123-123-123",
            "full_address": "123 Main Street",
            "current_capacity": 5,
            "who_can_you_accommodate": "Families",
            "ltla_name": "Bromley",
        }

        MvAccommodationFactory(**accommodation_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.ACCOMMODATION},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check header
        header = content[0].split(",")  # header is first row in the CSV
        accommodation_details_keys = accommodation_details.keys()
        self.assertTrue(
            all(column_name in header for column_name in accommodation_details_keys)
        )

        # check row
        new_row = next(
            (row for row in content if "accommodation-123-123-123" in row), None
        )

        # check row exists
        self.assertIsNotNone(new_row)

        # check row matches header length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_admin_download_view_accommodation_with_created_at_csv(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_details = {
            "id": "accommodation-123-123-123",
            "full_address": "123 Main Street",
            "current_capacity": 5,
            "who_can_you_accommodate": "Families",
            "ltla_name": "Bromley",
            "created_at": "2024-01-18 09:57:23.860782+00",
        }

        MvAccommodationFactory(**accommodation_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.ACCOMMODATION},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check header
        header = content[0].split(",")  # header is first row in the CSV
        accommodation_details_keys = accommodation_details.keys()
        self.assertTrue(
            all(column_name in header for column_name in accommodation_details_keys)
        )
        self.assertIn("created_at_tz", header)

        # check row
        new_row = next(
            (row for row in content if "accommodation-123-123-123" in row), None
        )

        # check row exists
        self.assertIsNotNone(new_row)
        self.assertTrue("UTC" in new_row)

        # check row matches header length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_bromley_la_download_view_accommodation_csv(self):
        user = get_user_with_groups(
            [UserGroup(name="Bromley", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        accommodation_details = {
            "id": "accommodation-123-123-123",
            "full_address": "123 Main Street",
            "current_capacity": 5,
            "who_can_you_accommodate": "Families",
            "ltla_name": "Bromley",
        }

        MvAccommodationFactory(**accommodation_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.ACCOMMODATION},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check header
        header = content[0].split(",")  # header is first row in the CSV
        accommodation_details_keys = accommodation_details.keys()
        self.assertTrue(
            all(column_name in header for column_name in accommodation_details_keys)
        )

        # check row
        new_row = next(
            (row for row in content if "accommodation-123-123-123" in row), None
        )

        # check row exists
        self.assertIsNotNone(new_row)

        # check row matches header length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_lewisham_la_does_not_see_bromley_data_download_view_accommodation_csv(
        self,
    ):
        user = get_user_with_groups(
            [UserGroup(name="Lewisham", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        accommodation_details = {
            "id": "accommodation-123-123-123",
            "full_address": "123 Main Street",
            "current_capacity": 5,
            "who_can_you_accommodate": "Families",
            "ltla_name": "Bromley",
        }

        MvAccommodationFactory(**accommodation_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.ACCOMMODATION},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check header
        header = content[0].split(",")  # header is first row in the CSV
        accommodation_details_keys = accommodation_details.keys()
        self.assertTrue(
            all(column_name in header for column_name in accommodation_details_keys)
        )

        # check row
        new_row = next(
            (row for row in content if "accommodation-123-123-123" in row), None
        )

        # check row exists
        self.assertIsNone(new_row)

    def test_should_use_get_for_user_method_when_retrieving_objects(
        self,
    ):
        user = get_user_with_groups(
            [UserGroup(name="Lewisham", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        accommodation_details = {
            "id": "accommodation-123-123-123",
            "full_address": "123 Main Street",
            "current_capacity": 5,
            "who_can_you_accommodate": "Families",
            "ltla_name": "Bromley",
        }

        MvAccommodationFactory(**accommodation_details)

        with patch.object(
            MvAccommodation.objects.__class__, "get_for_user"
        ) as mock_get_for_user:
            mock_get_for_user.return_value = MvAccommodation.objects.none()

            response = self.client.post(
                reverse("downloads:download-page"),
                data={"download_type": DownloadType.ACCOMMODATION},
            )

            # Exhaust the iterator into an empty deque
            deque(response.streaming_content, maxlen=0)

            mock_get_for_user.assert_called()

    @patch("downloads.views.sentry_sdk.metrics.count")
    def test_accommodation_download_sends_sentry_metric(self, sentry_metrics):
        user = get_da_user()
        self.client.force_login(user)

        self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.ACCOMMODATION},
        )

        expected_call_attributes = {
            "download_type": "accommodation",
            "user_id": user.id,
        }
        self.assertEqual(sentry_metrics.call_count, 1)
        self.assertEqual(
            sentry_metrics.call_args_list,
            [call("csv_download", 1, attributes=expected_call_attributes)],
        )
