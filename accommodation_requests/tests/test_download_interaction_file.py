# pylint: disable=duplicate-code
import http.client

import requests
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.base import LocalAuthorityBaseTestCaseMixin
from ontology.tests.factories import (
    InteractionAttachmentMetadataFactory,
    InteractionFactory,
    MvAccommodationRequestFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)
from webapp.tests.test_s3 import S3TestCaseMixin


class AccommodationRequestInteractionsDownloadAttachmentViewTests(
    TestSessionTokenMixin,
    LocalAuthorityBaseTestCaseMixin,
    S3TestCaseMixin,
):
    def setUp(self):
        super().setUp()

        # Create an accommodation request with files
        self.accommodation_request = MvAccommodationRequestFactory(
            id="accommodation-request-with-files-123",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )

        # Create an interaction with attachment
        self.interaction_with_attachment = InteractionFactory(
            id="interaction-with-attachment-123",
            linked_accommodation_request=self.accommodation_request,
            attachment="interaction-file-id",
        )

        # Create metadata for the attachment
        self.attachment_metadata = InteractionAttachmentMetadataFactory(
            rid="interaction-file-id",
            filename="interaction_file.txt",
            file_path="interaction-file-id/file.txt",
        )

    def test_dev_user_can_download(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation_requests:interactions-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "interaction_id": self.interaction_with_attachment.id,
                },
            )
        )

        # Check if the response is a redirect to the presigned URL
        self.assertEqual(response.status_code, http.client.FOUND)
        expected_path = "interactions/interaction-file-id/file.txt"
        self.assertIn(expected_path, response.url)
        self.assertEqual(
            requests.get(response.url).content, b"Example content in interaction file"
        )

    def test_la_user_can_download(self):
        user = self.ltla_one_a_user
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation_requests:interactions-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "interaction_id": self.interaction_with_attachment.id,
                },
            )
        )

        # Check if the response is a redirect to the presigned URL
        self.assertEqual(response.status_code, http.client.FOUND)
        expected_path = "interactions/interaction-file-id/file.txt"
        self.assertIn(expected_path, response.url)
        self.assertEqual(
            requests.get(response.url).content, b"Example content in interaction file"
        )

    def test_mhclg_user_can_download(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation_requests:interactions-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "interaction_id": self.interaction_with_attachment.id,
                },
            )
        )

        # Check if the response is a redirect to the presigned URL
        self.assertEqual(response.status_code, http.client.FOUND)
        expected_path = "interactions/interaction-file-id/file.txt"
        self.assertIn(expected_path, response.url)
        self.assertEqual(
            requests.get(response.url).content, b"Example content in interaction file"
        )

    def test_ukvi_user_can_download(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation_requests:interactions-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "interaction_id": self.interaction_with_attachment.id,
                },
            )
        )

        # Check if the response is a redirect to the presigned URL
        self.assertEqual(response.status_code, http.client.FOUND)
        expected_path = "interactions/interaction-file-id/file.txt"
        self.assertIn(expected_path, response.url)
        self.assertEqual(
            requests.get(response.url).content, b"Example content in interaction file"
        )

    def test_service_support_user_can_download(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation_requests:interactions-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "interaction_id": self.interaction_with_attachment.id,
                },
            )
        )

        # Check if the response is a redirect to the presigned URL
        self.assertEqual(response.status_code, http.client.FOUND)
        expected_path = "interactions/interaction-file-id/file.txt"
        self.assertIn(expected_path, response.url)
        self.assertEqual(
            requests.get(response.url).content, b"Example content in interaction file"
        )

    def test_interaction_without_attachment_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Create an interaction without attachment
        interaction_without_attachment = InteractionFactory(
            id="interaction-without-attachment",
            linked_accommodation_request=self.accommodation_request,
            attachment=None,
        )

        response = self.client.get(
            reverse(
                "accommodation_requests:interactions-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "interaction_id": interaction_without_attachment.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_ar_without_interaction_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation_requests:interactions-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "interaction_id": "non-existent-interaction-id",
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_interaction_without_metadata_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Create an interaction with attachment but no metadata
        interaction_no_metadata = InteractionFactory(
            id="interaction-no-metadata",
            linked_accommodation_request=self.accommodation_request,
            attachment="no-metadata-attachment-id",
        )

        response = self.client.get(
            reverse(
                "accommodation_requests:interactions-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "interaction_id": interaction_no_metadata.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_interaction_with_metadata_without_filename_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Create an interaction with metadata but missing filename
        interaction_no_filename = InteractionFactory(
            id="interaction-no-filename",
            linked_accommodation_request=self.accommodation_request,
            attachment="no-filename-attachment-id",
        )

        InteractionAttachmentMetadataFactory(
            rid="no-filename-attachment-id",
            filename="",  # Empty filename
            file_path="no-filename-attachment-id/file.txt",
        )

        response = self.client.get(
            reverse(
                "accommodation_requests:interactions-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "interaction_id": interaction_no_filename.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_interaction_with_metadata_without_file_path_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Create an interaction with metadata but missing file_path
        interaction_no_file_path = InteractionFactory(
            id="interaction-no-file-path",
            linked_accommodation_request=self.accommodation_request,
            attachment="no-file-path-attachment-id",
        )

        InteractionAttachmentMetadataFactory(
            rid="no-file-path-attachment-id",
            filename="file.txt",
            file_path="",  # Empty file_path
        )

        response = self.client.get(
            reverse(
                "accommodation_requests:interactions-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "interaction_id": interaction_no_file_path.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_interaction_with_incorrect_file_path_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Create interaction with metadata but incorrect file path
        # (file doesn't exist in S3)
        interaction_wrong_path = InteractionFactory(
            id="interaction-wrong-path",
            linked_accommodation_request=self.accommodation_request,
            attachment="wrong-path-attachment-id",
        )

        InteractionAttachmentMetadataFactory(
            rid="wrong-path-attachment-id",
            filename="file.txt",
            file_path="404-path",  # File doesn't exist in S3
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:interactions-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "interaction_id": interaction_wrong_path.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_la_user_cannot_download_attachment_from_other_la(self):
        interaction = InteractionFactory(
            id="interaction-permission-test",
            linked_accommodation_request=self.accommodation_request,
            attachment="permission-test-attachment-id",
        )

        InteractionAttachmentMetadataFactory(
            rid="permission-test-attachment-id",
            filename="file.txt",
            file_path="valid-path",
        )

        somerset_user = get_la_user()
        self.client.force_login(somerset_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:interactions-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "interaction_id": interaction.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_la_user_cannot_download_attachment_from_other_la_with_valid_ar(self):
        self.somerset_ar = MvAccommodationRequestFactory(
            id="somerset-accommodation-request-with-files-123",
            ltla_name=["Somerset"],
        )

        interaction = InteractionFactory(
            id="interaction-permission-test",
            linked_accommodation_request=self.accommodation_request,
            attachment="permission-test-attachment-id",
        )

        InteractionAttachmentMetadataFactory(
            rid="permission-test-attachment-id",
            filename="file.txt",
            file_path="valid-path",
        )

        somerset_user = get_la_user()
        self.client.force_login(somerset_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:interactions-download-attachment",
                kwargs={
                    "pk": self.somerset_ar.id,
                    "interaction_id": interaction.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)
