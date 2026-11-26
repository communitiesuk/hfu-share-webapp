from unittest.mock import patch

from django.db import DatabaseError

from accounts.tests.factories import UserFactory
from ontology.models import MvInteraction, SponsorshipCertificationForm
from ontology.tests.factories import SponsorshipCertificationFormFactory
from test_utils.base import BaseTestCase

CheckStatus = SponsorshipCertificationForm.PreApprovalCheckStatus
InteractionContact = MvInteraction.InteractionContact
PRE_APPROVAL_CHECK_INTERACTION = (
    SponsorshipCertificationForm.PRE_APPROVAL_CHECK_INTERACTION
)


class SponsorshipCertificationFormUpdatePreApprovalCheckStatusTests(BaseTestCase):
    def setUp(self):
        self.user = UserFactory(first_name="John", last_name="Doe")

    def test_passed_status_on_check_field_updates_field_and_records_interaction(self):
        uam = SponsorshipCertificationFormFactory(
            reference="SCF-TEST",
            uk_consent_form_status=CheckStatus.NOT_STARTED,
        )

        uam.update_pre_approval_check_status(
            SponsorshipCertificationForm.PreApprovalCheckField.UK_CONSENT_FORM_STATUS,
            CheckStatus.PASSED,
            self.user,
        )

        uam.refresh_from_db()
        self.assertEqual(uam.uk_consent_form_status, CheckStatus.PASSED)

        self.assertEqual(MvInteraction.objects.count(), 1)

        interaction = MvInteraction.objects.get()

        self.assertEqual(interaction.linked_uam, uam)
        self.assertEqual(interaction.created_by, self.user)
        self.assertEqual(
            interaction.interaction_contact,
            InteractionContact.UK_CONSENT_FORM_STATUS_CHECK,
        )
        self.assertEqual(
            interaction.interaction_type,
            InteractionContact.UK_CONSENT_FORM_STATUS_CHECK,
        )
        self.assertEqual(
            interaction.title, InteractionContact.UK_CONSENT_FORM_STATUS_CHECK
        )
        self.assertEqual(interaction.interaction_notes, "UK consent form: passed")

    def test_all_check_fields_and_statuses(self):
        fields = (
            SponsorshipCertificationForm.UKVI_CHECK_FIELDS
            + SponsorshipCertificationForm.LA_CHECK_FIELDS
        )
        for field in fields:
            details = PRE_APPROVAL_CHECK_INTERACTION[field]
            for status in (
                CheckStatus.NOT_STARTED,
                CheckStatus.IN_PROGRESS,
                CheckStatus.PASSED,
                CheckStatus.FAILED,
            ):
                with self.subTest(attribute=field.value, status=status):
                    uam = SponsorshipCertificationFormFactory()
                    uam.update_pre_approval_check_status(field, status, self.user)
                    uam.refresh_from_db()
                    self.assertEqual(getattr(uam, field.value), status)
                    interaction = MvInteraction.objects.get(linked_uam=uam)
                    self.assertEqual(
                        interaction.interaction_notes,
                        details["note"].format(check_status=status.lower()),
                    )
                    self.assertEqual(interaction.title, details["title"])

    def test_code_emailed_boolean_records_interaction_without_status_suffix(self):
        uam = SponsorshipCertificationFormFactory(
            reference="SCF-CODE", certificate_reference="CERT-123456"
        )

        uam.update_pre_approval_check_status(
            SponsorshipCertificationForm.PreApprovalCheckField.SPONSOR_CERTIFICATION_CODE_EMAILED,
            True,
            self.user,
        )

        uam.refresh_from_db()
        self.assertTrue(uam.sponsor_certification_code_emailed)

        interaction = MvInteraction.objects.get()
        self.assertEqual(interaction.linked_uam, uam)
        self.assertEqual(
            interaction.title,
            InteractionContact.SPONSOR_CERTIFICATION_CODE_EMAILED_CHECK,
        )
        self.assertEqual(
            interaction.interaction_notes,
            "Sponsor certification code: CERT-123456 emailed to sponsor",
        )

    def test_code_emailed_boolean_records_interaction_when_set_to_false(self):
        uam = SponsorshipCertificationFormFactory(
            reference="SCF-CODE", certificate_reference="CERT-123456"
        )

        uam.update_pre_approval_check_status(
            SponsorshipCertificationForm.PreApprovalCheckField.SPONSOR_CERTIFICATION_CODE_EMAILED,
            False,
            self.user,
        )

        uam.refresh_from_db()
        self.assertFalse(uam.sponsor_certification_code_emailed)

        interaction = MvInteraction.objects.get()
        self.assertEqual(interaction.linked_uam, uam)
        self.assertEqual(
            interaction.title,
            InteractionContact.SPONSOR_CERTIFICATION_CODE_NOT_EMAILED_CHECK,
        )
        self.assertEqual(
            interaction.interaction_notes,
            "Sponsor certification code marked as not sent",
        )

    def test_unknown_attribute_raises_value_error_and_writes_nothing(self):
        uam = SponsorshipCertificationFormFactory(
            reference="SCF-BAD",
            uk_consent_form_status=CheckStatus.NOT_STARTED,
        )

        with self.assertRaises(ValueError):
            uam.update_pre_approval_check_status(
                CheckStatus.PASSED, CheckStatus.PASSED, self.user
            )

        uam.refresh_from_db()
        self.assertEqual(uam.uk_consent_form_status, CheckStatus.NOT_STARTED)
        self.assertEqual(MvInteraction.objects.count(), 0)

    def test_rolls_back_field_update_when_interaction_creation_fails(self):
        uam = SponsorshipCertificationFormFactory(
            reference="SCF-ROLLBACK",
            uk_consent_form_status=CheckStatus.NOT_STARTED,
        )

        with patch.object(MvInteraction.objects, "create", side_effect=DatabaseError):
            with self.assertRaises(DatabaseError):
                uam.update_pre_approval_check_status(
                    SponsorshipCertificationForm.PreApprovalCheckField.UK_CONSENT_FORM_STATUS,
                    CheckStatus.PASSED,
                    self.user,
                )

        uam.refresh_from_db()
        self.assertEqual(uam.uk_consent_form_status, CheckStatus.NOT_STARTED)
        self.assertEqual(MvInteraction.objects.count(), 0)
