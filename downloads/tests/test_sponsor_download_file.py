from collections import deque
from unittest.mock import call, patch

from django.test import TestCase
from django.urls import reverse

from accounts.enums import GroupType
from accounts.tests.base import TestSessionTokenMixin
from downloads.forms import DownloadType
from ontology.models import MvVolunteer
from ontology.tests.factories import MvAccommodationFactory, MvVolunteerFactory
from user_management.tests.base import (
    UserGroup,
    get_admin_user,
    get_da_user,
    get_user_with_groups,
)


class DownloadsViewSponsorTestCase(TestSessionTokenMixin, TestCase):
    def test_da_download_view_sponsor_csv(self):
        user = get_da_user()
        self.client.force_login(user)

        sponsor_details = {
            "id": "sponsor-123-123-123",
            "first_name": "John",
            "last_name": "Doe",
            "email": "sponsor@example.com",
            "phone_number": ["9876543210"],
            "sponsor_status": "Active",
        }

        sponsor = MvVolunteerFactory(**sponsor_details)
        accommodation = MvAccommodationFactory(ltla_name="City of Edinburgh")
        sponsor.accommodations.add(accommodation)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.SPONSORS},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check header
        header = content[0].split(",")
        sponsor_details_keys = sponsor_details.keys()
        self.assertTrue(column_name in header for column_name in sponsor_details_keys)

        # check row
        new_row = next((row for row in content if "sponsor-123-123-123" in row), None)

        # check row
        self.assertIsNotNone(new_row)

        # check row length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_admin_download_view_sponsor_csv(self):
        user = get_admin_user()
        self.client.force_login(user)

        sponsor_details = {
            "id": "sponsor-123-123-123",
            "first_name": "John",
            "last_name": "Doe",
            "email": "sponsor@example.com",
            "phone_number": ["9876543210"],
            "sponsor_status": "Active",
        }

        sponsor = MvVolunteerFactory(**sponsor_details)
        accommodation = MvAccommodationFactory(ltla_name="Bromley")
        sponsor.accommodations.add(accommodation)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.SPONSORS},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check header
        header = content[0].split(",")
        sponsor_details_keys = sponsor_details.keys()
        self.assertTrue(column_name in header for column_name in sponsor_details_keys)

        # check row
        new_row = next((row for row in content if "sponsor-123-123-123" in row), None)

        # check row
        self.assertIsNotNone(new_row)

        # check row length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_bromley_la_download_view_sponsor_csv(self):
        user = get_user_with_groups(
            [UserGroup(name="Bromley", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        sponsor_details = {
            "id": "sponsor-123-123-123",
            "first_name": "John",
            "last_name": "Doe",
            "email": "sponsor@example.com",
            "phone_number": ["9876543210"],
            "sponsor_status": "Active",
        }

        sponsor = MvVolunteerFactory(**sponsor_details)
        accommodation = MvAccommodationFactory(ltla_name="Bromley")
        sponsor.accommodations.add(accommodation)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.SPONSORS},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check header
        header = content[0].split(",")
        sponsor_details_keys = sponsor_details.keys()
        self.assertTrue(column_name in header for column_name in sponsor_details_keys)

        # check row
        new_row = next((row for row in content if "sponsor-123-123-123" in row), None)

        # check row
        self.assertIsNotNone(new_row)

        # check row length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_lewisham_la_does_not_see_bromley_data_download_view_sponsor_csv(self):
        user = get_user_with_groups(
            [UserGroup(name="Lewisham", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        sponsor_details = {
            "id": "sponsor-123-123-123",
            "first_name": "John",
            "last_name": "Doe",
            "email": "sponsor@example.com",
            "phone_number": ["9876543210"],
            "sponsor_status": "Active",
        }

        sponsor = MvVolunteerFactory(**sponsor_details)
        accommodation = MvAccommodationFactory(ltla_name="Bromley")
        sponsor.accommodations.add(accommodation)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={"download_type": DownloadType.SPONSORS},
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check header
        header = content[0].split(",")
        sponsor_details_keys = sponsor_details.keys()
        self.assertTrue(column_name in header for column_name in sponsor_details_keys)

        # check row
        new_row = next((row for row in content if "sponsor-123-123-123" in row), None)

        # check row not found
        self.assertIsNone(new_row)

    def test_should_use_get_for_user_method_when_retrieving_objects(self):
        user = get_user_with_groups(
            [UserGroup(name="Lewisham", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        sponsor_details = {
            "id": "sponsor-123-123-123",
            "first_name": "John",
            "last_name": "Doe",
            "email": "sponsor@example.com",
            "phone_number": ["9876543210"],
            "sponsor_status": "Active",
        }

        sponsor = MvVolunteerFactory(**sponsor_details)
        accommodation = MvAccommodationFactory(ltla_name="Bromley")
        sponsor.accommodations.add(accommodation)

        with patch.object(
            MvVolunteer.objects.__class__, "get_for_user"
        ) as mock_get_for_user:
            mock_get_for_user.return_value = MvVolunteer.objects.none()

            response = self.client.post(
                reverse("downloads:download-page"),
                data={"download_type": DownloadType.SPONSORS},
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
            data={"download_type": DownloadType.SPONSORS},
        )

        expected_call_attributes = {
            "download_type": "sponsors",
            "user_id": user.id,
        }
        self.assertEqual(sentry_metrics.call_count, 1)
        self.assertEqual(
            sentry_metrics.call_args_list,
            [call("csv_download", 1, attributes=expected_call_attributes)],
        )
