import http.client

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
    get_da_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)
from webapp.tests.test_s3 import S3TestCaseMixin


class UamDetailFilesViewTests(TestSessionTokenMixin, UamsBaseTestCase, S3TestCaseMixin):
    def test_dev_user_is_granted_access(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_user_without_access_to_requested_uam_is_denied_access(self):
        la_user = self.ltla_two_a_user
        self.client.force_login(la_user)

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_la_user_is_granted_access(self):
        user = self.ltla_one_a_user
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_granted_access(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": self.scotland_da_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_mhclg_user_is_granted_access(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_ukvi_user_is_granted_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_service_support_user_is_granted_access(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_page_heading_shows_up(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertContains(response, "Files")

    def test_uam_without_person_linked_shows_no_file_exists_message(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertContains(response, "No files uploaded.")

    def test_uam_with_person_and_no_checks_shows_no_file_exists_message(self):
        user = get_admin_user()
        self.client.force_login(user)

        MvPersonFactory(sponsorship_certification_number_id=[self.ltla_one_a_uam.pk])

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": self.ltla_one_a_uam.pk},
            )
        )

        self.assertContains(response, "No files uploaded.")

    def test_uam_with_person_and_checks_shows_files(self):
        user = get_admin_user()
        self.client.force_login(user)

        uam = SponsorshipCertificationFormFactory(
            reference="UAM12345",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )

        person = MvPersonFactory(sponsorship_certification_number_id=[uam.reference])

        DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.UK_FORM_UPLOADED),
            document="uk-form-id",
            person=[person],
        )

        SponsorshipCertificationAttachmentMetadataFactory(
            rid="uk-form-id",
            filename="random-name-uk.txt",
            file_path="uk-form-id/uk_parental_consent.txt",
        )

        DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.UKR_FORM_UPLOADED),
            document="ukr-form-id",
            person=[person],
        )

        SponsorshipCertificationAttachmentMetadataFactory(
            rid="ukr-form-id",
            filename="random-name-ukr.txt",
            file_path="ukr-form-id/ukraine_parental_consent.txt",
        )

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": uam.pk},
            )
        )

        self.assertContains(response, "random-name-uk.txt")
        self.assertContains(response, "random-name-ukr.txt")

    def test_uam_with_attachment_metadata_reference_shows_files(self):
        user = get_admin_user()
        self.client.force_login(user)

        uam = SponsorshipCertificationFormFactory(
            reference="UAM12345",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )

        SponsorshipCertificationAttachmentMetadataFactory(
            sponsorship_certification_form=uam,
            filename="random-name-uk.txt",
            file_path="uk-form-id/uk_parental_consent.txt",
        )

        SponsorshipCertificationAttachmentMetadataFactory(
            sponsorship_certification_form=uam,
            filename="random-name-ukr.txt",
            file_path="ukr-form-id/ukraine_parental_consent.txt",
        )

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": uam.pk},
            )
        )

        self.assertContains(response, "random-name-uk.txt")
        self.assertContains(response, "random-name-ukr.txt")

    def test_uam_with_attachment_metadata_and_rid_reference_shows_files(self):
        user = get_admin_user()
        self.client.force_login(user)

        uam = SponsorshipCertificationFormFactory(
            reference="UAM12345",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )

        SponsorshipCertificationAttachmentMetadataFactory(
            rid="uk-form-id",
            sponsorship_certification_form=uam,
            filename="random-name-uk.txt",
            file_path="uk-form-id/uk_parental_consent.txt",
        )

        SponsorshipCertificationAttachmentMetadataFactory(
            rid="ukr-form-id",
            filename="random-name-ukr.txt",
            file_path="ukr-form-id/ukraine_parental_consent.txt",
        )

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": uam.pk},
            )
        )

        self.assertContains(response, "random-name-uk.txt")
        self.assertNotContains(response, "random-name-ukr.txt")

    def test_uam_with_person_and_checks_wont_show_files_if_get_header_fails(self):
        user = get_admin_user()
        self.client.force_login(user)

        # filenames are set to fail fetching from S3
        uam = SponsorshipCertificationFormFactory(
            reference="UAM12345",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )

        person = MvPersonFactory(sponsorship_certification_number_id=[uam.reference])

        DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.UK_FORM_UPLOADED),
            document="uk-form-id",
            person=[person],
        )

        # file path does not exist in S3
        SponsorshipCertificationAttachmentMetadataFactory(
            rid="uk-form-id",
            filename="random-name-uk.txt",
            file_path="uk-form-id/uk_parental_consent_2.txt",
        )

        DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.UKR_FORM_UPLOADED),
            document="ukr-form-id",
            person=[person],
        )

        # file path does not exist in S3
        SponsorshipCertificationAttachmentMetadataFactory(
            rid="ukr-form-id",
            filename="random-name-ukr.txt",
            file_path="ukr-form-id/ukraine_parental_consent_2.txt",
        )

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": uam.pk},
            )
        )

        self.assertNotContains(response, '<table class="govuk-table">')

    def test_uam_without_filenames_shows_default_filename(self):
        user = get_admin_user()
        self.client.force_login(user)

        uam = SponsorshipCertificationFormFactory(
            reference="UAM12345",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )

        person = MvPersonFactory(sponsorship_certification_number_id=[uam.reference])

        DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.UK_FORM_UPLOADED),
            document="uk-form-id",
            person=[person],
        )

        # filename is None
        SponsorshipCertificationAttachmentMetadataFactory(
            rid="uk-form-id",
            filename=None,
            file_path="uk-form-id/uk_parental_consent.txt",
        )

        DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.UKR_FORM_UPLOADED),
            document="ukr-form-id",
            person=[person],
        )

        # filename is None
        SponsorshipCertificationAttachmentMetadataFactory(
            rid="ukr-form-id",
            filename=None,
            file_path="ukr-form-id/ukraine_parental_consent.txt",
        )

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": uam.pk},
            )
        )

        self.assertContains(response, "Consent form")

    def test_uam_with_person_and_checks_shows_only_if_document_prop_exists(self):
        user = get_admin_user()
        self.client.force_login(user)

        uam = SponsorshipCertificationFormFactory(
            reference="UAM12345",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            uk_parental_consent_filename="uk_parental_consent.txt",
            ukraine_parental_consent_filename="ukraine_parental_consent.txt",
        )

        person = MvPersonFactory(sponsorship_certification_number_id=[uam.reference])

        DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.UK_FORM_UPLOADED),
            document="uk-form-id",
            person=[person],
        )

        # filename is None
        SponsorshipCertificationAttachmentMetadataFactory(
            rid="uk-form-id",
            filename="uk_parental_consent.txt",
            file_path="uk-form-id/uk_parental_consent.txt",
        )

        DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.UKR_FORM_UPLOADED),
            document=None,
            person=[person],
        )

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": uam.pk},
            )
        )

        self.assertContains(response, "uk_parental_consent.txt")
        self.assertNotContains(response, "ukraine_parental_consent.txt")

    def test_uam_without_metadata_wont_show_table(self):
        user = get_admin_user()
        self.client.force_login(user)

        uam = SponsorshipCertificationFormFactory(
            reference="UAM12345",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )

        person = MvPersonFactory(sponsorship_certification_number_id=[uam.reference])

        DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.UK_FORM_UPLOADED),
            document="uk-form-id",
            person=[person],
        )

        DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.UKR_FORM_UPLOADED),
            document="ukr-form-id",
            person=[person],
        )

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": uam.pk},
            )
        )

        self.assertNotContains(response, '<table class="govuk-table">')

    def test_uam_with_bad_metadata_wont_show_table(self):
        user = get_admin_user()
        self.client.force_login(user)

        uam = SponsorshipCertificationFormFactory(
            reference="UAM12345",
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
        )

        person = MvPersonFactory(sponsorship_certification_number_id=[uam.reference])

        DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.UK_FORM_UPLOADED),
            document="uk-form-id",
            person=[person],
        )

        SponsorshipCertificationAttachmentMetadataFactory(
            rid="uk-form-id",
            filename=None,
            file_path=None,
        )

        DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.UKR_FORM_UPLOADED),
            document="ukr-form-id",
            person=[person],
        )

        SponsorshipCertificationAttachmentMetadataFactory(
            rid="ukr-form-id",
            filename=None,
            file_path=None,
        )

        response = self.client.get(
            reverse(
                "uams:detail-files",
                kwargs={"pk": uam.pk},
            )
        )

        self.assertNotContains(response, '<table class="govuk-table">')
