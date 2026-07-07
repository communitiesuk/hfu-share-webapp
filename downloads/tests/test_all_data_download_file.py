import csv
import io
from collections import deque
from datetime import datetime
from unittest.mock import call, patch

from django.test import TestCase
from django.urls import reverse

from accounts.enums import GroupType
from accounts.tests.base import TestSessionTokenMixin
from downloads.forms import DownloadType
from ontology.mixins import DaViewerGroupNames
from ontology.models import ExportToolObject
from ontology.tests.factories import (
    ExportToolObjectFactory,
    MvAccommodationFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import (
    UserGroup,
    get_admin_user,
    get_da_user,
    get_ukvi_user,
    get_user_with_groups,
)


class DownloadsViewAllDataTestCase(TestSessionTokenMixin, TestCase):
    def test_da_download_view_all_data_csv(self):
        user = get_da_user()
        self.client.force_login(user)

        all_data_details = {
            "id": "export-tool-123-123-123",
            "person_full_name": "Test",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "latest_application_date": datetime(2010, 1, 1),
            "ltla_name": ["City of Edinburgh"],
        }

        ExportToolObjectFactory(**all_data_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                "date_from": "2000-01-01",
                "date_to": "2024-12-31",
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check row count
        self.assertEqual(len(content), 3)  # header + one row + empty line

        # check header
        header = content[0].split(",")  # header is first row in the CSV
        all_data_details_keys = list(all_data_details.keys())
        self.assertTrue(
            all(column_name in header for column_name in all_data_details_keys)
        )

        # check row
        new_row = next(
            (row for row in content if "export-tool-123-123-123" in row), None
        )

        # check row exists
        self.assertIsNotNone(new_row)

        # check row matches header length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_da_download_view_all_data_with_created_at_csv(self):
        user = get_da_user()
        self.client.force_login(user)

        all_data_details = {
            "id": "export-tool-123-123-123",
            "person_full_name": "Test",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "created_at": "2024-01-18 09:57:23.860782+00",
            "latest_application_date": datetime(2010, 1, 1),
            "ltla_name": ["City of Edinburgh"],
        }

        ExportToolObjectFactory(**all_data_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                "date_from": "2000-01-01",
                "date_to": "2024-12-31",
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check row count
        self.assertEqual(len(content), 3)  # header + one row + empty line

        # check header
        header = content[0].split(",")  # header is first row in the CSV
        all_data_details_keys = list(all_data_details.keys())
        self.assertTrue(
            all(column_name in header for column_name in all_data_details_keys)
        )
        self.assertTrue("created_at_tz" in header)

        # check row
        new_row = next(
            (row for row in content if "export-tool-123-123-123" in row), None
        )

        # check row exists
        self.assertIsNotNone(new_row)
        self.assertTrue("UTC" in new_row)

        # check row matches header length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_admin_download_view_all_data_csv(self):
        user = get_admin_user()
        self.client.force_login(user)

        all_data_details = {
            "id": "export-tool-123-123-123",
            "person_full_name": "Test",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "latest_application_date": datetime(2010, 1, 1),
        }

        ExportToolObjectFactory(**all_data_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                "date_from": "2000-01-01",
                "date_to": "2024-12-31",
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check row count
        self.assertEqual(len(content), 3)  # header + one row + empty line

        # check header
        header = content[0].split(",")  # header is first row in the CSV
        all_data_details_keys = list(all_data_details.keys())
        self.assertTrue(
            all(column_name in header for column_name in all_data_details_keys)
        )

        # check row
        new_row = next(
            (row for row in content if "export-tool-123-123-123" in row), None
        )

        # check row exists
        self.assertIsNotNone(new_row)

        # check row matches header length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_admin_download_view_all_data_with_created_at_csv(self):
        user = get_admin_user()
        self.client.force_login(user)

        all_data_details = {
            "id": "export-tool-123-123-123",
            "person_full_name": "Test",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "created_at": "2024-01-18 09:57:23.860782+00",
            "latest_application_date": datetime(2010, 1, 1),
        }

        ExportToolObjectFactory(**all_data_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                "date_from": "2000-01-01",
                "date_to": "2024-12-31",
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check row count
        self.assertEqual(len(content), 3)  # header + one row + empty line

        # check header
        header = content[0].split(",")  # header is first row in the CSV
        all_data_details_keys = list(all_data_details.keys())
        self.assertTrue(
            all(column_name in header for column_name in all_data_details_keys)
        )
        self.assertTrue("created_at_tz" in header)

        # check row
        new_row = next(
            (row for row in content if "export-tool-123-123-123" in row), None
        )

        # check row exists
        self.assertIsNotNone(new_row)
        self.assertTrue("UTC" in new_row)

        # check row matches header length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_bromley_la_download_view_all_data_csv(self):
        user = get_user_with_groups(
            [UserGroup(name="Bromley", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        all_data_details = {
            "id": "export-tool-123-123-123",
            "person_full_name": "Test",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "ltla_name": ["Bromley"],
            "latest_application_date": datetime(2010, 1, 1),
        }

        ExportToolObjectFactory(**all_data_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                "date_from": "2000-01-01",
                "date_to": "2024-12-31",
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check row count
        self.assertEqual(len(content), 3)  # header + one row + empty line

        # check header
        header = content[0].split(",")  # header is first row in the CSV
        all_data_details_keys = list(all_data_details.keys())
        self.assertTrue(
            all(column_name in header for column_name in all_data_details_keys)
        )

        # check row
        new_row = next(
            (row for row in content if "export-tool-123-123-123" in row), None
        )

        # check row exists
        self.assertIsNotNone(new_row)

        # check row matches header length
        self.assertEqual(len(header), len(new_row.split(",")))

    def test_lewisham_la_does_not_see_bromley_data_download_view_all_data_csv(self):
        user = get_user_with_groups(
            [UserGroup(name="Lewisham", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        all_data_details = {
            "id": "export-tool-123-123-123",
            "person_full_name": "Test",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "ltla_name": ["Bromley"],
            "latest_application_date": datetime(2010, 1, 1),
        }

        ExportToolObjectFactory(**all_data_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                "date_from": "2000-01-01",
                "date_to": "2024-12-31",
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8").split("\r\n")

        # check row count
        self.assertEqual(len(content), 2)  # header + empty line

        # check header
        header = content[0].split(",")  # header is first row in the CSV
        all_data_details_keys = list(all_data_details.keys())
        self.assertTrue(
            all(column_name in header for column_name in all_data_details_keys)
        )

        # check row
        new_row = next(
            (row for row in content if "export-tool-123-123-123" in row), None
        )

        # check row doesn't exist
        self.assertIsNone(new_row)

    def test_da_user_should_use_get_for_user_method(self):
        user = get_user_with_groups(
            [UserGroup(name="da_england", type=GroupType.DEVOLVED_ADMINISTRATION)]
        )
        self.client.force_login(user)

        all_data_details = {
            "id": "export-tool-123-123-123",
            "person_full_name": "Test",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "viewer_group_names": [DaViewerGroupNames.ENGLAND.value],
            "latest_application_date": datetime(2010, 1, 1),
        }

        ExportToolObjectFactory(**all_data_details)

        with (
            patch.object(
                ExportToolObject.objects.__class__, "get_for_user"
            ) as mock_get_for_user,
            patch.object(
                ExportToolObject.objects.__class__, "get_queryset_without_annotations"
            ) as mock_get_queryset_without_annotations,
        ):
            mock_get_for_user.return_value = ExportToolObject.objects.none()
            mock_get_queryset_without_annotations.return_value = (
                ExportToolObject.objects.none()
            )

            response = self.client.post(
                reverse("downloads:download-page"),
                data={
                    "download_type": DownloadType.ALL,
                    "date_from": "2000-01-01",
                    "date_to": "2024-12-31",
                },
            )

            # Exhaust the iterator into an empty deque
            deque(response.streaming_content, maxlen=0)

            mock_get_for_user.assert_called()
            mock_get_queryset_without_annotations.assert_not_called()

    def test_admin_user_should_use_get_for_user_without_annotations_method(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        all_data_details = {
            "id": "export-tool-123-123-123",
            "person_full_name": "Test",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "latest_application_date": datetime(2010, 1, 1),
        }

        ExportToolObjectFactory(**all_data_details)

        with patch.object(
            ExportToolObject.objects.__class__, "get_queryset_without_annotations"
        ) as mock_get_queryset:
            mock_get_queryset.return_value = ExportToolObject.objects.none()

            response = self.client.post(
                reverse("downloads:download-page"),
                data={
                    "download_type": DownloadType.ALL,
                    "date_from": "2000-01-01",
                    "date_to": "2024-12-31",
                },
            )

            # Exhaust the iterator into an empty deque
            deque(response.streaming_content, maxlen=0)

            mock_get_queryset.assert_called()

    def test_la_user_should_use_get_for_user_method(self):
        user = get_user_with_groups(
            [UserGroup(name="Lewisham", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        all_data_details = {
            "id": "export-tool-123-123-123",
            "person_full_name": "Test",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "ltla_name": ["Bromley"],
            "latest_application_date": datetime(2010, 1, 1),
        }

        ExportToolObjectFactory(**all_data_details)

        with (
            patch.object(
                ExportToolObject.objects.__class__, "get_for_user"
            ) as mock_get_for_user,
            patch.object(
                ExportToolObject.objects.__class__, "get_queryset_without_annotations"
            ) as mock_get_queryset_without_annotations,
        ):
            mock_get_for_user.return_value = ExportToolObject.objects.none()
            mock_get_queryset_without_annotations.return_value = (
                ExportToolObject.objects.none()
            )

            response = self.client.post(
                reverse("downloads:download-page"),
                data={
                    "download_type": DownloadType.ALL,
                    "date_from": "2000-01-01",
                    "date_to": "2024-12-31",
                },
            )

            # Exhaust the iterator into an empty deque
            deque(response.streaming_content, maxlen=0)

            mock_get_for_user.assert_called()
            mock_get_queryset_without_annotations.assert_not_called()

    def test_download_view_all_data_date_range_csv(self):
        user = get_admin_user()
        self.client.force_login(user)

        all_data_details_2025 = {
            "id": "export-tool-123-123-123",
            "person_full_name": "Test_2025",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "latest_application_date": datetime(2025, 1, 1),
        }

        all_data_details_2024 = {
            "id": "export-tool-789-789-790",
            "person_full_name": "Test_2024",
            "accommodation_full_address": "90 Second Street",
            "group_max_age": 50,
            "latest_application_date": datetime(2024, 1, 1),
        }

        ExportToolObjectFactory(**all_data_details_2025)
        ExportToolObjectFactory(**all_data_details_2024)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                "date_from": "2024-01-01",
                "date_to": "2024-12-31",
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(content))
        for row in csv_reader:
            self.assertEqual(row["id"], "export-tool-789-789-790")
            self.assertEqual(row["latest_application_date"], "2024-01-01")

        # check row count
        self.assertEqual(len(content.split("\r\n")), 3)  # header + one row + empty line

    def test_download_view_all_data_no_dates_csv_includes_all_and_null_date(self):
        user = get_admin_user()
        self.client.force_login(user)

        obj_2025 = {
            "id": "export-tool-111-111-111",
            "person_full_name": "Test_2025",
            "accommodation_full_address": "1 Alpha Street",
            "group_max_age": 21,
            "latest_application_date": datetime(2025, 1, 1),
        }
        obj_2024 = {
            "id": "export-tool-222-222-222",
            "person_full_name": "Test_2024",
            "accommodation_full_address": "2 Beta Street",
            "group_max_age": 31,
            "latest_application_date": datetime(2024, 6, 15),
        }
        obj_null = {
            "id": "export-tool-333-333-333",
            "person_full_name": "Test_NULL",
            "accommodation_full_address": "3 Gamma Street",
            "group_max_age": 41,
            # latest_application_date intentionally omitted
        }

        ExportToolObjectFactory(**obj_2025)
        ExportToolObjectFactory(**obj_2024)
        ExportToolObjectFactory(**obj_null)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                # no date_from / date_to provided
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(content))
        rows = list(csv_reader)

        returned_ids = {row["id"] for row in rows}
        self.assertSetEqual(
            returned_ids,
            {
                "export-tool-111-111-111",
                "export-tool-222-222-222",
                "export-tool-333-333-333",
            },
        )

        self.assertEqual(len(content.split("\r\n")), 5)

    def test_download_view_all_data_only_date_from_csv(self):
        user = get_admin_user()
        self.client.force_login(user)

        older = {
            "id": "export-tool-444-444-444",
            "person_full_name": "Older_2023",
            "accommodation_full_address": "4 Delta Street",
            "group_max_age": 25,
            "latest_application_date": datetime(2023, 12, 31),
        }
        boundary = {
            "id": "export-tool-555-555-555",
            "person_full_name": "Boundary_2024_06_01",
            "accommodation_full_address": "5 Epsilon Street",
            "group_max_age": 35,
            "latest_application_date": datetime(2024, 6, 1),
        }
        newer = {
            "id": "export-tool-666-666-666",
            "person_full_name": "Newer_2025",
            "accommodation_full_address": "6 Zeta Street",
            "group_max_age": 45,
            "latest_application_date": datetime(2025, 1, 1),
        }

        ExportToolObjectFactory(**older)
        ExportToolObjectFactory(**boundary)
        ExportToolObjectFactory(**newer)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                "date_from": "2024-06-01",
                # no date_to
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(content))
        rows = list(csv_reader)

        returned_ids = {row["id"] for row in rows}
        # Should include boundary and newer, exclude older
        self.assertSetEqual(
            returned_ids, {"export-tool-555-555-555", "export-tool-666-666-666"}
        )
        # header + 2 rows + empty line
        self.assertEqual(len(content.split("\r\n")), 4)

    def test_download_view_all_data_only_date_to_csv(self):
        user = get_admin_user()
        self.client.force_login(user)

        older = {
            "id": "export-tool-777-777-777",
            "person_full_name": "Older_2023",
            "accommodation_full_address": "7 Eta Street",
            "group_max_age": 26,
            "latest_application_date": datetime(2023, 12, 31),
        }
        boundary = {
            "id": "export-tool-888-888-888",
            "person_full_name": "Boundary_2024_06_01",
            "accommodation_full_address": "8 Theta Street",
            "group_max_age": 36,
            "latest_application_date": datetime(2024, 6, 1),
        }
        newer = {
            "id": "export-tool-999-999-999",
            "person_full_name": "Newer_2025",
            "accommodation_full_address": "9 Iota Street",
            "group_max_age": 46,
            "latest_application_date": datetime(2025, 1, 1),
        }

        ExportToolObjectFactory(**older)
        ExportToolObjectFactory(**boundary)
        ExportToolObjectFactory(**newer)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                # no date_from
                "date_to": "2024-06-01",
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(content))
        rows = list(csv_reader)

        returned_ids = {row["id"] for row in rows}
        # Should include older and boundary, exclude newer
        self.assertSetEqual(
            returned_ids, {"export-tool-777-777-777", "export-tool-888-888-888"}
        )

        # header + 2 rows + empty line
        self.assertEqual(len(content.split("\r\n")), 4)

    def test_download_view_all_data_empty_date_fields_treated_as_no_filter(self):
        user = get_admin_user()
        self.client.force_login(user)

        obj_2025 = {
            "id": "export-tool-101-101-101",
            "person_full_name": "Test_2025",
            "accommodation_full_address": "10 Kappa Street",
            "group_max_age": 28,
            "latest_application_date": datetime(2025, 2, 2),
        }
        obj_2024 = {
            "id": "export-tool-202-202-202",
            "person_full_name": "Test_2024",
            "accommodation_full_address": "20 Lambda Street",
            "group_max_age": 38,
            "latest_application_date": datetime(2024, 2, 2),
        }
        obj_null = {
            "id": "export-tool-303-303-303",
            "person_full_name": "Test_NULL",
            "accommodation_full_address": "30 Mu Street",
            "group_max_age": 48,
            # no latest_application_date
        }

        ExportToolObjectFactory(**obj_2025)
        ExportToolObjectFactory(**obj_2024)
        ExportToolObjectFactory(**obj_null)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                "date_from": "",
                "date_to": "",
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(content))
        rows = list(csv_reader)

        returned_ids = {row["id"] for row in rows}
        self.assertSetEqual(
            returned_ids,
            {
                "export-tool-101-101-101",
                "export-tool-202-202-202",
                "export-tool-303-303-303",
            },
        )

        # null date should render as empty string
        null_row = next(r for r in rows if r["id"] == "export-tool-303-303-303")
        self.assertEqual(null_row["latest_application_date"], "")

        # header + 3 rows + empty line
        self.assertEqual(len(content.split("\r\n")), 5)

    def test_bromley_la_download_view_all_data_redacted_sponsor_csv(self):
        user = get_user_with_groups(
            [UserGroup(name="Bromley", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        sponsor_bromley = MvVolunteerFactory()
        sponsor_lewisham = MvVolunteerFactory()
        sponsor_bromley_and_lewisham = MvVolunteerFactory()
        sponsor_missing_ltla = MvVolunteerFactory()

        bromley_accommodation_1 = MvAccommodationFactory(ltla_name="Bromley")

        bromley_accommodation_1.hosts.set([sponsor_bromley])

        lewisham_accommodation_1 = MvAccommodationFactory(ltla_name="Lewisham")
        lewisham_accommodation_1.hosts.set([sponsor_lewisham])

        bromley_accommodation_2 = MvAccommodationFactory(ltla_name="Bromley")

        bromley_accommodation_2.hosts.set([sponsor_bromley_and_lewisham])

        lewisham_accommodation_2 = MvAccommodationFactory(ltla_name="Lewisham")
        lewisham_accommodation_2.hosts.set([sponsor_bromley_and_lewisham])

        bromley_only_details = {
            "id": "export-tool-123-123-123",
            "person_full_name": "Test_bromley",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_bromley.id,
            "sponsor_full_name": "Name-Bromley",
        }

        lewisham_only_details = {
            "id": "export-tool-789-789-790",
            "person_full_name": "Test_lewisham",
            "accommodation_full_address": "90 Second Street",
            "group_max_age": 50,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_lewisham.id,
            "sponsor_full_name": "Mrs Lewisham",
        }

        bromley_and_lewisham_details = {
            "id": "export-tool-456-456-456",
            "person_full_name": "Test_bromley_and_lewisham",
            "accommodation_full_address": "23 Test Street",
            "group_max_age": 60,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_bromley_and_lewisham.id,
            "sponsor_full_name": "Name-Bromley-Lewisham",
        }

        bromley_missing_sponsor_id = {
            "id": "export-tool-111-111-111",
            "person_full_name": "Test_missing_sponsor_id",
            "accommodation_full_address": "123 Third Street",
            "group_max_age": 80,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_full_name": "Name-Missing-Sponsor-ID",
        }

        bromley_missing_sponsor = {
            "id": "export-tool-222-222-222",
            "person_full_name": "Test_missing_sponsor",
            "accommodation_full_address": "123 Fourth Street",
            "group_max_age": 90,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": "missing-sponsor",
            "sponsor_full_name": "Name-Missing-Sponsor",
        }

        bromley_sponsor_missing_ltla = {
            "id": "export-tool-333-333-333",
            "person_full_name": "Test_missing_sponsor_ltla",
            "accommodation_full_address": "123 Fifth Street",
            "group_max_age": 70,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_missing_ltla.id,
            "sponsor_full_name": "Name-Sponsor-Missing-LTLA",
        }

        ExportToolObjectFactory(**bromley_only_details)
        ExportToolObjectFactory(**lewisham_only_details)
        ExportToolObjectFactory(**bromley_and_lewisham_details)
        ExportToolObjectFactory(**bromley_missing_sponsor_id)
        ExportToolObjectFactory(**bromley_missing_sponsor)
        ExportToolObjectFactory(**bromley_sponsor_missing_ltla)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                "date_from": "2000-01-01",
                "date_to": "2025-01-31",
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8")

        csv_reader = csv.DictReader(io.StringIO(content))
        ids = set()
        expected_result = {
            "export-tool-123-123-123": "Name-Bromley",
            "export-tool-456-456-456": "Name-Bromley-Lewisham",
            "export-tool-789-789-790": "",
            "export-tool-111-111-111": "Name-Missing-Sponsor-ID",
            "export-tool-222-222-222": "Name-Missing-Sponsor",
            "export-tool-333-333-333": "Name-Sponsor-Missing-LTLA",
        }
        for row in csv_reader:
            ids.add(row["id"])
            self.assertEqual(expected_result[row["id"]], row["sponsor_full_name"])

        self.assertEqual(len(ids), 6)  # Expect all 6 rows to appear

    def test_dev_download_view_all_data_no_redaction_csv(self):
        user = get_admin_user()
        self.client.force_login(user)

        sponsor_bromley = MvVolunteerFactory()
        sponsor_lewisham = MvVolunteerFactory()

        bromley_accommodation_1 = MvAccommodationFactory(ltla_name="Bromley")

        bromley_accommodation_1.hosts.set([sponsor_bromley])

        lewisham_accommodation_1 = MvAccommodationFactory(ltla_name="Lewisham")
        lewisham_accommodation_1.hosts.set([sponsor_lewisham])

        bromley_only_details = {
            "id": "export-tool-123-123-123",
            "person_full_name": "Test_bromley",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_bromley.id,
            "sponsor_full_name": "Name-Bromley",
        }

        lewisham_only_details = {
            "id": "export-tool-789-789-790",
            "person_full_name": "Test_lewisham",
            "accommodation_full_address": "90 Second Street",
            "group_max_age": 50,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_lewisham.id,
            "sponsor_full_name": "Mrs Lewisham",
        }

        ExportToolObjectFactory(**bromley_only_details)
        ExportToolObjectFactory(**lewisham_only_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                "date_from": "2000-01-01",
                "date_to": "2025-01-31",
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8")

        csv_reader = csv.DictReader(io.StringIO(content))
        ids = set()
        expected_result = {
            "export-tool-123-123-123": "Name-Bromley",
            "export-tool-789-789-790": "Mrs Lewisham",
        }
        for row in csv_reader:
            ids.add(row["id"])
            self.assertEqual(expected_result[row["id"]], row["sponsor_full_name"])

        self.assertEqual(len(ids), 2)

    def test_bromley_la_download_view_all_data_exclude_lewisham_csv(self):
        user = get_user_with_groups(
            [UserGroup(name="Bromley", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        sponsor_bromley = MvVolunteerFactory()
        sponsor_lewisham = MvVolunteerFactory()

        bromley_accommodation_1 = MvAccommodationFactory(ltla_name="Bromley")

        bromley_accommodation_1.hosts.set([sponsor_bromley])

        lewisham_accommodation_1 = MvAccommodationFactory(ltla_name="Lewisham")
        lewisham_accommodation_1.hosts.set([sponsor_lewisham])

        bromley_only_details = {
            "id": "export-tool-123-123-123",
            "person_full_name": "Test_bromley",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_bromley.id,
            "sponsor_full_name": "Name-Bromley",
        }

        lewisham_only_details = {
            "id": "export-tool-789-789-790",
            "person_full_name": "Test_lewisham",
            "accommodation_full_address": "90 Second Street",
            "group_max_age": 50,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Lewisham"],
            "sponsor_id": sponsor_lewisham.id,
            "sponsor_full_name": "Mrs Lewisham",
        }

        ExportToolObjectFactory(**bromley_only_details)
        ExportToolObjectFactory(**lewisham_only_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                "date_from": "2000-01-01",
                "date_to": "2025-01-31",
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8")

        csv_reader = csv.DictReader(io.StringIO(content))
        ids = set()
        expected_result = {
            "export-tool-123-123-123": "Name-Bromley",
        }
        for row in csv_reader:
            ids.add(row["id"])
            self.assertEqual(expected_result[row["id"]], row["sponsor_full_name"])

        self.assertEqual(len(ids), 1)

    def test_download_view_all_data_remove_duplicates_from_redaction(self):
        user = get_user_with_groups(
            [UserGroup(name="Bromley", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        sponsor_bromley = MvVolunteerFactory()
        sponsor_lewisham = MvVolunteerFactory()
        sponsor_lewisham_2 = MvVolunteerFactory()
        sponsor_croydon = MvVolunteerFactory()

        bromley_accommodation_1 = MvAccommodationFactory(ltla_name="Bromley")

        bromley_accommodation_1.hosts.set([sponsor_bromley])

        lewisham_accommodation_1 = MvAccommodationFactory(ltla_name="Lewisham")
        lewisham_accommodation_1.hosts.set([sponsor_lewisham])

        lewisham_accommodation_2 = MvAccommodationFactory(ltla_name="Lewisham")
        lewisham_accommodation_2.hosts.set([sponsor_lewisham_2])

        croydon_accommodation_1 = MvAccommodationFactory(ltla_name="Croydon")
        croydon_accommodation_1.hosts.set([sponsor_croydon])

        bromley_details = {
            "export_tool_id": 1,
            "id": "export-tool-a",
            "person_full_name": "Test_bromley",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_bromley.id,
            "sponsor_full_name": "Name-Bromley",
        }

        bromley_details_2 = {
            "export_tool_id": 2,
            "id": "export-tool-a",
            "person_full_name": "Test_bromley_2",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_bromley.id,
            "sponsor_full_name": "Name-Bromley",
        }

        lewisham_details = {
            "export_tool_id": 3,
            "id": "export-tool-b",
            "person_full_name": "Test_lewisham",
            "accommodation_full_address": "90 Second Street",
            "group_max_age": 50,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_lewisham.id,
            "sponsor_full_name": "Mrs Lewisham",
        }

        another_lewisham_details = {
            "export_tool_id": 4,
            "id": "export-tool-b",
            "person_full_name": "Test_lewisham",
            "accommodation_full_address": "90 Second Street",
            "group_max_age": 50,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_lewisham_2.id,
            "sponsor_full_name": "Mr Lewisham the second",
        }

        croydon_details = {
            "export_tool_id": 5,
            "id": "export-tool-c",
            "person_full_name": "Test_croydon",
            "accommodation_full_address": "23 Test Street",
            "group_max_age": 60,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_croydon.id,
            "sponsor_full_name": "Mrs Croydon",
        }

        ExportToolObjectFactory(**bromley_details)
        ExportToolObjectFactory(**bromley_details_2)
        ExportToolObjectFactory(**lewisham_details)
        ExportToolObjectFactory(**another_lewisham_details)
        ExportToolObjectFactory(**croydon_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                "date_from": "2000-01-01",
                "date_to": "2025-01-31",
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8")

        csv_reader = csv.DictReader(io.StringIO(content))
        rows = [row for row in csv_reader]

        rows.sort(key=lambda x: x["id"])

        self.assertEqual(rows[0]["sponsor_full_name"], "Name-Bromley")
        self.assertEqual(rows[0]["person_full_name"], "Test_bromley")

        self.assertEqual(rows[1]["sponsor_full_name"], "Name-Bromley")
        self.assertEqual(rows[1]["person_full_name"], "Test_bromley_2")

        self.assertEqual(rows[2]["sponsor_full_name"], "")
        self.assertEqual(rows[2]["person_full_name"], "Test_lewisham")

        self.assertEqual(rows[3]["sponsor_full_name"], "")
        self.assertEqual(rows[3]["person_full_name"], "Test_croydon")

        self.assertEqual(len(rows), 4)

    def test_download_all_remove_duplicates_and_redact_for_la_user_additional_group(
        self,
    ):
        user = get_user_with_groups(
            [
                UserGroup(name="Bromley", type=GroupType.LOCAL_AUTHORITY),
                UserGroup(
                    name="Bromley_ea", type=GroupType.LOCAL_AUTHORITY_EARLY_ADOPTERS
                ),
            ]
        )
        self.client.force_login(user)

        sponsor_bromley = MvVolunteerFactory()
        sponsor_lewisham = MvVolunteerFactory()
        sponsor_lewisham_2 = MvVolunteerFactory()
        sponsor_croydon = MvVolunteerFactory()

        bromley_accommodation_1 = MvAccommodationFactory(ltla_name="Bromley")

        bromley_accommodation_1.hosts.set([sponsor_bromley])

        lewisham_accommodation_1 = MvAccommodationFactory(ltla_name="Lewisham")
        lewisham_accommodation_1.hosts.set([sponsor_lewisham])

        lewisham_accommodation_2 = MvAccommodationFactory(ltla_name="Lewisham")
        lewisham_accommodation_2.hosts.set([sponsor_lewisham_2])

        croydon_accommodation_1 = MvAccommodationFactory(ltla_name="Croydon")
        croydon_accommodation_1.hosts.set([sponsor_croydon])

        bromley_details = {
            "export_tool_id": 1,
            "id": "export-tool-a",
            "person_full_name": "Test_bromley",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_bromley.id,
            "sponsor_full_name": "Name-Bromley",
        }

        bromley_details_2 = {
            "export_tool_id": 2,
            "id": "export-tool-a",
            "person_full_name": "Test_bromley_2",
            "accommodation_full_address": "123 Main Street",
            "group_max_age": 30,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_bromley.id,
            "sponsor_full_name": "Name-Bromley",
        }

        lewisham_details = {
            "export_tool_id": 3,
            "id": "export-tool-b",
            "person_full_name": "Test_lewisham",
            "accommodation_full_address": "90 Second Street",
            "group_max_age": 50,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_lewisham.id,
            "sponsor_full_name": "Mrs Lewisham",
        }

        another_lewisham_details = {
            "export_tool_id": 4,
            "id": "export-tool-b",
            "person_full_name": "Test_lewisham",
            "accommodation_full_address": "90 Second Street",
            "group_max_age": 50,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_lewisham_2.id,
            "sponsor_full_name": "Mr Lewisham the second",
        }

        croydon_details = {
            "export_tool_id": 5,
            "id": "export-tool-c",
            "person_full_name": "Test_croydon",
            "accommodation_full_address": "23 Test Street",
            "group_max_age": 60,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_croydon.id,
            "sponsor_full_name": "Mrs Croydon",
        }

        ExportToolObjectFactory(**bromley_details)
        ExportToolObjectFactory(**bromley_details_2)
        ExportToolObjectFactory(**lewisham_details)
        ExportToolObjectFactory(**another_lewisham_details)
        ExportToolObjectFactory(**croydon_details)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                "date_from": "2000-01-01",
                "date_to": "2025-01-31",
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8")

        csv_reader = csv.DictReader(io.StringIO(content))
        rows = [row for row in csv_reader]

        rows.sort(key=lambda x: x["id"])

        self.assertEqual(rows[0]["sponsor_full_name"], "Name-Bromley")
        self.assertEqual(rows[0]["person_full_name"], "Test_bromley")

        self.assertEqual(rows[1]["sponsor_full_name"], "Name-Bromley")
        self.assertEqual(rows[1]["person_full_name"], "Test_bromley_2")

        self.assertEqual(rows[2]["sponsor_full_name"], "")
        self.assertEqual(rows[2]["person_full_name"], "Test_lewisham")

        self.assertEqual(rows[3]["sponsor_full_name"], "")
        self.assertEqual(rows[3]["person_full_name"], "Test_croydon")

        self.assertEqual(len(rows), 4)

    def test_download_view_all_data_different_redaction_not_duplicates(self):
        user = get_user_with_groups(
            [UserGroup(name="Bromley", type=GroupType.LOCAL_AUTHORITY)]
        )
        self.client.force_login(user)

        sponsor_bromley = MvVolunteerFactory()
        sponsor_croydon = MvVolunteerFactory()

        bromley_accommodation_1 = MvAccommodationFactory(ltla_name="Bromley")
        bromley_accommodation_1.hosts.set([sponsor_bromley])

        croydon_accommodation_1 = MvAccommodationFactory(ltla_name="Croydon")
        croydon_accommodation_1.hosts.set([sponsor_croydon])

        bromley_mix_details_1 = {
            "id": "export-tool-222-222-222",
            "person_full_name": "Test_bromley_mix",
            "accommodation_full_address": "22 Jump Street",
            "group_max_age": 70,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_croydon.id,
            "sponsor_full_name": "Name-Croydon",
            "accommodation_id": bromley_accommodation_1.id,
            "accommodation_postcode": "AA1 1BB",
        }

        bromley_mix_details_2 = {
            "id": "export-tool-222-222-222",
            "person_full_name": "Test_bromley_mix",
            "accommodation_full_address": "22 Jump Street",
            "group_max_age": 70,
            "latest_application_date": datetime(2025, 1, 1),
            "ltla_name": ["Bromley"],
            "sponsor_id": sponsor_bromley.id,
            "sponsor_full_name": "Name-Bromley",
            "accommodation_id": croydon_accommodation_1.id,
            "accommodation_postcode": "CC1 1DD",
        }

        ExportToolObjectFactory(**bromley_mix_details_1)
        ExportToolObjectFactory(**bromley_mix_details_2)

        response = self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                "date_from": "2000-01-01",
                "date_to": "2025-01-31",
            },
        )

        content = b"".join(response.streaming_content).decode("utf-8")

        csv_reader = csv.DictReader(io.StringIO(content))
        num_rows = 0
        bromley_sponsor_seen = False
        bromley_accommodation_seen = False
        for row in csv_reader:
            num_rows += 1
            if row["sponsor_full_name"] == "Name-Bromley":
                bromley_sponsor_seen = True
            if row["accommodation_postcode"] == "AA1 1BB":
                bromley_accommodation_seen = True

        self.assertTrue(bromley_sponsor_seen)
        self.assertTrue(bromley_accommodation_seen)
        self.assertEqual(num_rows, 2)

    @patch("downloads.views.sentry_sdk.metrics.count")
    def test_all_data_download_sends_sentry_metric(self, sentry_metrics):
        user = get_da_user()
        self.client.force_login(user)

        self.client.post(
            reverse("downloads:download-page"),
            data={
                "download_type": DownloadType.ALL,
                "date_from": "2024-01-01",
                "date_to": "2024-12-31",
            },
        )

        expected_call_attributes = {
            "download_type": "all",
            "user_id": user.id,
        }
        self.assertEqual(sentry_metrics.call_count, 1)
        self.assertEqual(
            sentry_metrics.call_args_list,
            [call("csv_download", 1, attributes=expected_call_attributes)],
        )
