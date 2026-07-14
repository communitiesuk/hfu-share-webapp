import http.client
from datetime import datetime, timezone

from botocore.exceptions import ClientError
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.models.CheckType import CheckType
from ontology.tests.base import UamsBaseTestCase
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvPersonFactory,
    SponsorshipCertificationAttachmentMetadataFactory,
    SponsorshipCertificationFormFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)
from webapp.tests.test_s3 import S3TestCaseMixin


class UamDownloadAttachmentViewTests(
    TestSessionTokenMixin, UamsBaseTestCase, S3TestCaseMixin
):
    def setUp(self):
        super().setUp()

        self.ltla_one_a_uam_with_files = SponsorshipCertificationFormFactory(
            reference="UAM-WITH-FILES-123",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            uk_parental_consent_filename="uk_parental_consent.txt",
            ukraine_parental_consent_filename="ukraine_parental_consent.txt",
        )

        self.person_for_uam_with_files = MvPersonFactory(
            accommodation_request__ltla_name=[self.ltla_one_a_name],
            accommodation_request__utla_name=[self.utla_one_name],
            sponsorship_certification_number_id=[
                self.ltla_one_a_uam_with_files.reference
            ],
        )

        self.uk_form_id = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.UK_FORM_UPLOADED),
            document="uk-form-id",
            person=[self.person_for_uam_with_files],
        )

        self.uk_form_metadata = SponsorshipCertificationAttachmentMetadataFactory(
            id="1",
            rid="uk-form-id",
            filename="random-name-uk.txt",
            file_path="uk-form-id/uk_parental_consent.txt",
        )

        self.ltla_one_another_uam_with_files = SponsorshipCertificationFormFactory(
            reference="UAM12346",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )

        self.uk_another_form_id = SponsorshipCertificationAttachmentMetadataFactory(
            id="2",
            rid="uk-form-id-2",
            sponsorship_certification_form=self.ltla_one_another_uam_with_files,
            filename="random-name-uk.txt",
            file_path="uk-form-id/uk_parental_consent.txt",
        )

        self.ukr_form_id = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.UKR_FORM_UPLOADED),
            document="ukr-form-id",
            person=[self.person_for_uam_with_files],
        )

        self.ukr_form_metadata = SponsorshipCertificationAttachmentMetadataFactory(
            id="3",
            rid="ukr-form-id",
            filename="random-name-ukr.txt",
            file_path="ukr-form-id/ukraine_parental_consent.txt",
        )

    def test_dev_user_is_granted_access(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:download-attachment",
                kwargs={
                    "pk": self.ltla_one_a_uam_with_files.pk,
                    "metadata_id": self.uk_form_metadata.id,
                },
            )
        )

        # Check if the response is a redirect to the presigned URL
        self.assertEqual(response.status_code, http.client.FOUND)
        self.assertIn("uams/uk-form-id/uk_parental_consent.txt", response.url)

    def test_dev_user_gets_by_attachment_metadata(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:download-attachment",
                kwargs={
                    "pk": self.ltla_one_another_uam_with_files.pk,
                    "metadata_id": self.uk_another_form_id.id,
                },
            )
        )

        # Check if the response is a redirect to the presigned URL
        self.assertEqual(response.status_code, http.client.FOUND)
        self.assertIn("uams/uk-form-id/uk_parental_consent.txt", response.url)

    def test_user_without_access_to_requested_uam_is_denied_access(self):
        la_user = self.ltla_two_a_user
        self.client.force_login(la_user)

        response = self.client.get(
            reverse(
                "uams:download-attachment",
                kwargs={
                    "pk": self.ltla_one_a_uam_with_files.pk,
                    "metadata_id": self.uk_form_metadata.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_la_user_is_granted_access(self):
        user = self.ltla_one_a_user
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:download-attachment",
                kwargs={
                    "pk": self.ltla_one_a_uam_with_files.pk,
                    "metadata_id": self.uk_form_metadata.id,
                },
            )
        )

        # Check if the response is a redirect to the presigned URL
        self.assertEqual(response.status_code, http.client.FOUND)
        self.assertIn("uams/uk-form-id/uk_parental_consent.txt", response.url)

    def test_mhclg_user_is_granted_access(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:download-attachment",
                kwargs={
                    "pk": self.ltla_one_a_uam_with_files.pk,
                    "metadata_id": self.uk_form_metadata.id,
                },
            )
        )

        # Check if the response is a redirect to the presigned URL
        self.assertEqual(response.status_code, http.client.FOUND)
        self.assertIn("uams/uk-form-id/uk_parental_consent.txt", response.url)

    def test_ukvi_user_is_granted_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:download-attachment",
                kwargs={
                    "pk": self.ltla_one_a_uam_with_files.pk,
                    "metadata_id": self.uk_form_metadata.id,
                },
            )
        )

        # Check if the response is a redirect to the presigned URL
        self.assertEqual(response.status_code, http.client.FOUND)
        self.assertIn("uams/uk-form-id/uk_parental_consent.txt", response.url)

    def test_service_support_user_is_granted_access(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:download-attachment",
                kwargs={
                    "pk": self.ltla_one_a_uam_with_files.pk,
                    "metadata_id": self.uk_form_metadata.id,
                },
            )
        )

        # Check if the response is a redirect to the presigned URL
        self.assertEqual(response.status_code, http.client.FOUND)
        self.assertIn("uams/uk-form-id/uk_parental_consent.txt", response.url)

    def test_uam_with_wrong_check_type_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:download-attachment",
                kwargs={
                    "pk": self.ltla_one_a_uam_with_files.pk,
                    "metadata_id": "4",
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_uam_without_person_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Remove the person link to the UAM
        self.person_for_uam_with_files.sponsorship_certification_number_id = []
        self.person_for_uam_with_files.save()

        response = self.client.get(
            reverse(
                "uams:download-attachment",
                kwargs={
                    "pk": self.ltla_one_a_uam_with_files.pk,
                    "metadata_id": self.uk_form_metadata.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_uam_with_person_from_other_la_returns_404(self):
        user = self.ltla_one_a_user
        self.client.force_login(user)

        # Move person to a different LA
        self.person_for_uam_with_files.accommodation_request.ltla_name = [
            self.ltla_two_a_name
        ]
        self.person_for_uam_with_files.accommodation_request.utla_name = [
            self.utla_two_name
        ]
        self.person_for_uam_with_files.accommodation_request.save()

        response = self.client.get(
            reverse(
                "uams:download-attachment",
                kwargs={
                    "pk": self.ltla_one_a_uam_with_files.pk,
                    "metadata_id": self.uk_form_metadata.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_uam_without_check_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Remove the person link to the UAM
        self.person_for_uam_with_files.checks.clear()

        response = self.client.get(
            reverse(
                "uams:download-attachment",
                kwargs={
                    "pk": self.ltla_one_a_uam_with_files.pk,
                    "metadata_id": self.uk_form_metadata.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_uam_with_check_without_document_prop_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Remove the document from the check
        self.uk_form_id.document = None
        self.uk_form_id.save()

        response = self.client.get(
            reverse(
                "uams:download-attachment",
                kwargs={
                    "pk": self.ltla_one_a_uam_with_files.pk,
                    "metadata_id": self.uk_form_metadata.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_uam_without_metadata_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Unlink metadata from the check document
        self.uk_form_metadata.rid = "different-id"
        self.uk_form_metadata.save()

        response = self.client.get(
            reverse(
                "uams:download-attachment",
                kwargs={
                    "pk": self.ltla_one_a_uam_with_files.pk,
                    "metadata_id": self.uk_form_metadata.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_uam_with_metadata_without_file_path_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Remove metadata.file_path
        self.uk_form_metadata.file_path = ""
        self.uk_form_metadata.save()

        response = self.client.get(
            reverse(
                "uams:download-attachment",
                kwargs={
                    "pk": self.ltla_one_a_uam_with_files.pk,
                    "metadata_id": self.uk_form_metadata.id,
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_uam_with_incorrect_file_path_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Make file not exist in S3
        self.uk_form_metadata.file_path = "404-path"
        self.uk_form_metadata.save()

        with self.assertRaises(ClientError) as context:
            response = self.client.get(
                reverse(
                    "uams:download-attachment",
                    kwargs={
                        "pk": self.ltla_one_a_uam_with_files.pk,
                        "metadata_id": self.uk_form_metadata.id,
                    },
                )
            )

            response = context.exception.response
            self.assertEqual(response["ResponseMetadata"]["HTTPStatusCode"], 404)
            self.assertEqual(response["Error"]["Message"], "Not Found")


class UamGOVUKFormsAttachmentViewTests(
    TestSessionTokenMixin, UamsBaseTestCase, S3TestCaseMixin
):
    def setUp(self):
        super().setUp()

        created_at = datetime(2026, 7, 1, 13, 2, 3, tzinfo=timezone.utc)
        self.uam = SponsorshipCertificationFormFactory(
            reference="UAM123",
            created_at=created_at,
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            uk_parental_consent_filename="uk_parental_consent.txt",
            ukraine_parental_consent_filename="ukraine_parental_consent.txt",
        )

        self.uam_with_missing_file = SponsorshipCertificationFormFactory(
            reference="UAM1234",
            created_at=created_at,
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            uk_parental_consent_filename="uk_file_not_found.txt",
            ukraine_parental_consent_filename="ukraine_parental_consent.txt",
        )

    def test_dev_user_is_granted_access_to_uk_form_attachment(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:download-govuk-forms-attachment",
                kwargs={
                    "pk": self.uam.pk,
                    "consent_file_type": "uk",
                },
            )
        )

        # Check if the response is a redirect to the presigned URL
        self.assertEqual(response.status_code, http.client.FOUND)
        self.assertIn(
            "uams/govuk_forms/20260701T130203Z_UAM123/uk_parental_consent.txt",
            response.url,
        )

    def test_dev_user_is_granted_access_to_ukraine_form_attachment(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:download-govuk-forms-attachment",
                kwargs={
                    "pk": self.uam.pk,
                    "consent_file_type": "ukraine",
                },
            )
        )

        # Check if the response is a redirect to the presigned URL
        self.assertEqual(response.status_code, http.client.FOUND)
        self.assertIn(
            "uams/govuk_forms/20260701T130203Z_UAM123/ukraine_parental_consent.txt",
            response.url,
        )

    def test_unauthorised_user_cannot_download_attachment(self):
        la_user = self.ltla_two_a_user
        self.client.force_login(la_user)

        response = self.client.get(
            reverse(
                "uams:download-govuk-forms-attachment",
                kwargs={
                    "pk": self.uam.pk,
                    "consent_file_type": "ukraine",
                },
            )
        )
        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_incorrect_attachment_consent_file_type_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:download-govuk-forms-attachment",
                kwargs={
                    "pk": self.uam.pk,
                    "consent_file_type": "wrong_file_type",
                },
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_missing_file_attachment_returns_404(self):
        user = get_admin_user()
        self.client.force_login(user)

        with self.assertRaises(ClientError) as context:
            self.client.get(
                reverse(
                    "uams:download-govuk-forms-attachment",
                    kwargs={
                        "pk": self.uam_with_missing_file.pk,
                        "consent_file_type": "uk",
                    },
                )
            )

        response = context.exception.response
        self.assertEqual(response["ResponseMetadata"]["HTTPStatusCode"], 404)
        self.assertEqual(response["Error"]["Message"], "Not Found")
