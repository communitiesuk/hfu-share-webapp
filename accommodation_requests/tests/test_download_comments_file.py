import http.client
import uuid
from datetime import datetime

import requests
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.base import LocalAuthorityBaseTestCaseMixin
from ontology.tests.factories import (
    CommentAttachmentFactory,
    CommentAttachmentMetadataFactory,
    CommentFactory,
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


class AccommodationRequestCommentsDownloadAttachmentViewTests(
    TestSessionTokenMixin,
    LocalAuthorityBaseTestCaseMixin,
    S3TestCaseMixin,
):
    def setUp(self):
        super().setUp()

        self.accommodation_request = MvAccommodationRequestFactory(
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )
        self.comment_with_attachment = CommentFactory(
            attached_accommodation_request_id=self.accommodation_request,
            content="Example comment",
            created_at=datetime.today(),
        )
        self.attachment = CommentAttachmentFactory(
            key="comment-key-1",
            comment_id=self.comment_with_attachment.id,
            filename="comment_displayed_name.txt",
        )
        self.attachment_metadata = CommentAttachmentMetadataFactory(
            id="uuid-0",
            file_name="comment_attachment.txt",
            attachment_key="comment-key-1",
        )

        self.comment_without_attachment = CommentFactory(
            attached_accommodation_request_id=self.accommodation_request,
            content="Example other comment",
            created_at=datetime.today(),
        )

    def test_dev_user_can_download(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:comments-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "comment_id": self.comment_with_attachment.id,
                    "attachment_id": self.attachment.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.FOUND)
        expected_path = "comments/comment_attachment.txt"
        self.assertIn(expected_path, response.url)
        self.assertEqual(
            requests.get(response.url).content, b"Example content in comment file"
        )

    def test_la_user_can_download(self):
        user = self.ltla_one_a_user
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:comments-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "comment_id": self.comment_with_attachment.id,
                    "attachment_id": self.attachment.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.FOUND)
        expected_path = "comments/comment_attachment.txt"
        self.assertIn(expected_path, response.url)
        self.assertEqual(
            requests.get(response.url).content, b"Example content in comment file"
        )

    def test_mhclg_user_can_download(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:comments-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "comment_id": self.comment_with_attachment.id,
                    "attachment_id": self.attachment.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.FOUND)
        expected_path = "comments/comment_attachment.txt"
        self.assertIn(expected_path, response.url)
        self.assertEqual(
            requests.get(response.url).content, b"Example content in comment file"
        )

    def test_ukvi_user_can_download(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:comments-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "comment_id": self.comment_with_attachment.id,
                    "attachment_id": self.attachment.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.FOUND)
        expected_path = "comments/comment_attachment.txt"
        self.assertIn(expected_path, response.url)
        self.assertEqual(
            requests.get(response.url).content, b"Example content in comment file"
        )

    def test_service_support_user_can_download(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:comments-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "comment_id": self.comment_with_attachment.id,
                    "attachment_id": self.attachment.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.FOUND)
        expected_path = "comments/comment_attachment.txt"
        self.assertIn(expected_path, response.url)
        self.assertEqual(
            requests.get(response.url).content, b"Example content in comment file"
        )

    def test_comment_without_attachment_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:comments-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "comment_id": self.comment_without_attachment.id,
                    "attachment_id": str(uuid.uuid4()),
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_ar_without_comment_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:comments-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "comment_id": str(uuid.uuid4()),
                    "attachment_id": str(uuid.uuid4()),
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_comment_without_metadata_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        comment_no_metadata = CommentFactory(
            attached_accommodation_request_id=self.accommodation_request,
            content="No metadata",
            created_at=datetime.today(),
        )

        attachment_no_metadata = CommentAttachmentFactory(
            key="no-metadata-key",
            comment_id=comment_no_metadata.id,
            filename="no_meta.txt",
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:comments-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "comment_id": comment_no_metadata.id,
                    "attachment_id": attachment_no_metadata.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_comment_with_metadata_without_filename_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        comment_no_filename = CommentFactory(
            attached_accommodation_request_id=self.accommodation_request,
            content="Missing filename",
            created_at=datetime.today(),
        )

        attachment_no_filename = CommentAttachmentFactory(
            key="no-filename-key",
            comment_id=comment_no_filename.id,
        )

        CommentAttachmentMetadataFactory(
            id="uuid-1",
            attachment_key="no-filename-key",
            file_name="s3_path.txt",
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:comments-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "comment_id": comment_no_filename.id,
                    "attachment_id": attachment_no_filename.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_comment_with_metadata_without_file_path_in_s3_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        comment_no_file_path = CommentFactory(
            attached_accommodation_request_id=self.accommodation_request,
            content="Missing file path",
            created_at=datetime.today(),
        )

        attachment_no_s3_file_path = CommentAttachmentFactory(
            key="no-file-path-key",
            comment_id=comment_no_file_path.id,
            filename="display.txt",
        )

        CommentAttachmentMetadataFactory(
            id="uuid-2",
            attachment_key="no-file-path-key",
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:comments-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "comment_id": comment_no_file_path.id,
                    "attachment_id": attachment_no_s3_file_path.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_comment_with_incorrect_file_path_raises_client_error(self):
        user = get_admin_user()
        self.client.force_login(user)

        comment_wrong_path = CommentFactory(
            attached_accommodation_request_id=self.accommodation_request,
            content="Wrong path",
            created_at=datetime.today(),
        )

        attachment_wrong = CommentAttachmentFactory(
            key="wrong-path-key",
            comment_id=comment_wrong_path.id,
            filename="display.txt",
        )

        CommentAttachmentMetadataFactory(
            id="uuid-3",
            attachment_key="wrong-path-key",
            file_name="some_other_file.txt",
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:comments-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "comment_id": comment_wrong_path.id,
                    "attachment_id": attachment_wrong.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_la_user_cannot_download_attachment_from_other_la(self):
        comment = CommentFactory(
            attached_accommodation_request_id=self.accommodation_request
        )
        attachment = CommentAttachmentFactory(comment_id=comment.id)
        CommentAttachmentMetadataFactory(
            id="uuid-4",
            attachment_key=attachment.key,
            file_name="other_la_file.txt",
        )

        somerset_user = get_la_user()
        self.client.force_login(somerset_user)

        response = self.client.get(
            reverse(
                "accommodation_requests:comments-download-attachment",
                kwargs={
                    "pk": self.accommodation_request.id,
                    "comment_id": comment.id,
                    "attachment_id": attachment.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_la_user_cannot_download_attachment_from_other_la_with_valid_ar(self):
        self.somerset_ar = MvAccommodationRequestFactory(
            id="somerset-accommodation-request-with-files-123",
            ltla_name=["Somerset"],
        )

        comment = CommentFactory(
            attached_accommodation_request_id=self.accommodation_request
        )
        attachment = CommentAttachmentFactory(comment_id=comment.id)
        CommentAttachmentMetadataFactory(
            id="uuid-5",
            attachment_key=attachment.key,
            file_name="other_la_file.txt",
        )

        somerset_user = get_la_user()
        self.client.force_login(somerset_user)

        response = self.client.get(
            reverse(
                "accommodation_requests:comments-download-attachment",
                kwargs={
                    "pk": self.somerset_ar.id,
                    "comment_id": comment.id,
                    "attachment_id": attachment.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)
