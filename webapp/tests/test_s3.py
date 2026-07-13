import os
from datetime import datetime, timezone
from unittest import mock
from unittest.mock import patch

import boto3
from botocore.exceptions import ClientError
from django.test import TestCase
from moto import mock_aws

from webapp.s3 import (
    get_file_header,
    get_govuk_forms_attachment_filepath,
    get_presigned_download_url,
)


class S3TestCaseMixin(TestCase):
    # Use boto's default endpoint; moto will intercept it regardless of env settings
    patcher = patch.dict(
        os.environ, {"AWS_ENDPOINT_URL": "https://s3.eu-west-2.amazonaws.com"}
    )

    def setUp(self):
        self.patcher.start()
        self.mock_aws = mock_aws()
        self.mock_aws.start()
        self.aws_region = "eu-west-2"
        self.test_bucket = "test-bucket"
        self.uam_folder_name = "uams"
        self.interactions_folder_name = "interactions"
        self.comments_folder_name = "comments"

        conn = boto3.client(
            "s3",
            region_name=self.aws_region,
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )
        # Attempt to create the S3 bucket.
        # If the bucket already exists and is owned by you (on any environment),
        # ignore the error. For any other error, raise the exception.
        try:
            conn.create_bucket(
                Bucket=self.test_bucket,
                CreateBucketConfiguration={"LocationConstraint": self.aws_region},
            )
        except ClientError as e:
            if e.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
                raise

        self.file_key_1 = (
            f"{self.uam_folder_name}/unique-id-123-321/testfile_123_321.txt"
        )
        self.file_key_2 = f"{self.uam_folder_name}/uk-form-id/uk_parental_consent.txt"
        self.file_key_3 = (
            f"{self.uam_folder_name}/ukr-form-id/ukraine_parental_consent.txt"
        )
        self.file_key_4 = (
            f"{self.interactions_folder_name}/interaction-file-id/file.txt"
        )
        self.file_key_5 = f"{self.comments_folder_name}/comment_attachment.txt"

        # GOV.UK Forms attachments
        self.file_key_6 = (
            f"{self.uam_folder_name}/20260701T130203Z_UAM123/uk_parental_consent.txt"
        )
        self.file_key_7 = f"{self.uam_folder_name}/20260701T130203Z_UAM123/ukraine_parental_consent.txt"  # noqa E501

        conn.put_object(
            Bucket=self.test_bucket,
            Key=self.file_key_1,
            Body="Example content",
        )
        conn.put_object(
            Bucket=self.test_bucket,
            Key=self.file_key_2,
            Body="Example content",
        )
        conn.put_object(
            Bucket=self.test_bucket,
            Key=self.file_key_3,
            Body="Example content",
        )
        conn.put_object(
            Bucket=self.test_bucket,
            Key=self.file_key_4,
            Body="Example content in interaction file",
        )
        conn.put_object(
            Bucket=self.test_bucket,
            Key=self.file_key_5,
            Body="Example content in comment file",
        )
        conn.put_object(
            Bucket=self.test_bucket,
            Key=self.file_key_6,
            Body="Example content in Forms UAM UK file",
        )
        conn.put_object(
            Bucket=self.test_bucket,
            Key=self.file_key_7,
            Body="Example content in Forms UAM Ukraine file",
        )

    def tearDown(self):
        self.mock_aws.stop()
        self.addCleanup(self.patcher.stop)


class TestS3FileHeader(S3TestCaseMixin):
    def test_get_file_header_success(self):
        header = get_file_header(
            bucket_name=self.test_bucket,
            file_key=self.file_key_1,
        )

        self.assertTrue(header is not None)

    def test_get_file_header_bucket_not_exists(self):
        with self.assertRaises(ClientError) as context:
            get_file_header(
                bucket_name="nonexistent-bucket",
                file_key=self.file_key_1,
            )

        response = context.exception.response
        self.assertEqual(response["ResponseMetadata"]["HTTPStatusCode"], 404)
        self.assertEqual(response["Error"]["Code"], "NoSuchBucket")

    def test_get_file_header_file_not_exists(self):
        with self.assertRaises(ClientError) as context:
            get_file_header(
                bucket_name=self.test_bucket,
                file_key="uams/nonexistent-file.txt",
            )

        response = context.exception.response
        self.assertEqual(response["ResponseMetadata"]["HTTPStatusCode"], 404)
        self.assertEqual(response["Error"]["Message"], "Not Found")


class TestGetPresignedDownloadUrl(S3TestCaseMixin):
    def test_get_presigned_download_url_returns_url(self):
        url = get_presigned_download_url(
            bucket_name=self.test_bucket,
            file_key=self.file_key_1,
            filename="testfile.txt",
        )

        self.assertTrue(url.startswith("https://"))
        self.assertIn(self.file_key_1, url)

    def test_get_presigned_download_url_returns_url_with_different_filename(self):
        url = get_presigned_download_url(
            bucket_name=self.test_bucket,
            file_key=self.file_key_1,
            filename="different_name.txt",
        )

        self.assertTrue(url.startswith("https://"))
        self.assertIn("different_name.txt", url)

    def test_get_presigned_download_url_bucket_not_exists(self):
        with self.assertRaises(ClientError) as context:
            get_presigned_download_url(
                bucket_name="nonexistent-bucket",
                file_key=self.file_key_1,
                filename="testfile.txt",
            )

        response = context.exception.response
        self.assertEqual(response["ResponseMetadata"]["HTTPStatusCode"], 404)
        self.assertEqual(response["Error"]["Code"], "NoSuchBucket")

    def test_get_presigned_download_url_file_not_exists(self):
        with self.assertRaises(ClientError) as context:
            get_presigned_download_url(
                bucket_name=self.test_bucket,
                file_key="uams/nonexistent-file.txt",
                filename="nonexistent-file.txt",
            )

        response = context.exception.response
        self.assertEqual(response["ResponseMetadata"]["HTTPStatusCode"], 404)
        self.assertEqual(response["Error"]["Message"], "Not Found")


class TestGetGovukFormsAttachmentFilePath(TestCase):
    def setUp(self):
        created_at = datetime(2026, 7, 1, 13, 2, 3, tzinfo=timezone.utc)
        self.uam = mock.Mock(
            created_at=created_at,
            reference="UAM123",
            uk_parental_consent_filename="uk_parental_consent.txt",
            ukraine_parental_consent_filename="ukraine_parental_consent.txt",
        )
        self.uam_without_created_date = mock.Mock(
            created_at=None,
            reference="UAM123",
            uk_parental_consent_filename="uk_parental_consent.txt",
            ukraine_parental_consent_filename="ukraine_parental_consent.txt",
        )

    def test_get_govuk_forms_attachment_file_uk(self):
        self.assertEqual(
            get_govuk_forms_attachment_filepath(self.uam, "uk"),
            "uams/20260701T130203Z_UAM123/uk_parental_consent.txt",
        )

    def test_get_govuk_forms_attachment_file_ukraine(self):
        self.assertEqual(
            get_govuk_forms_attachment_filepath(self.uam, "ukraine"),
            "uams/20260701T130203Z_UAM123/ukraine_parental_consent.txt",
        )

    def test_get_govuk_forms_attachment_file_invalid_type(self):
        self.assertEqual(get_govuk_forms_attachment_filepath(self.uam, "invalid"), "")

    def test_get_govuk_forms_attachment_file_invalid_created_date(self):
        self.assertEqual(
            get_govuk_forms_attachment_filepath(
                self.uam_without_created_date, "ukraine"
            ),
            "",
        )
